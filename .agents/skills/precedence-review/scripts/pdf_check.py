"""Check that a compiled write-up PDF holds only text, internal links and web links.

Usage: python3 -I -X utf8 pdf_check.py <file.pdf> ...

The write-up's TeX is written by agents that read untrusted sources. Whatever
that TeX does, the published PDF may contain nothing that acts on the reader's
machine. This script parses every object in the file the way a PDF reader does
(strings, hex strings, names with #xx escapes decoded, nested dictionaries) and
reports:
  - any action other than GoTo (an internal link) and URI. Every other PDF
    action type is refused by name: GoToR GoToE GoToDp Launch Thread Sound
    Movie Hide Named SubmitForm ResetForm ImportData SetOCGState Rendition Trans
    GoTo3DView JavaScript RichMediaExecute;
  - a /URI that is not a string beginning with http:// or https://;
  - an annotation that is not a link (form fields, file attachments, media);
  - /JS, additional actions (/AA), embedded or associated files, file
    specifications, interactive forms (/AcroForm, /XFA), /Encrypt;
  - object streams and cross-reference streams. This script does not read
    inside them, so they are refused; sandbox_pdflatex (tex_sandbox.sh) compiles
    with \\pdfobjcompresslevel=0, which keeps every object at the top level;
  - an object defined twice (an incremental update).
Content streams and fonts are not parsed: a PDF reader runs no actions from
them.

Exit status 0 if every file is clean; 1 if a file has a problem (one line each)
or cannot be parsed; 2 on bad usage.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# PDF 2.0 (ISO 32000-2), Table 201: every action type except GoTo and URI.
REFUSED_ACTIONS = set(
    "GoToR GoToE GoToDp Launch Thread Sound Movie Hide Named SubmitForm ResetForm ImportData "
    "SetOCGState Rendition Trans GoTo3DView JavaScript RichMediaExecute".split())
REFUSED_OTHER = set(
    "JS AA EmbeddedFile EmbeddedFiles AF Filespec FileAttachment AcroForm XFA Widget RichMedia "
    "Screen 3D Collection Encrypt ObjStm XRef XRefStm".split())
REFUSED = REFUSED_ACTIONS | REFUSED_OTHER

WS = rb"\x00\t\n\x0c\r "
TOKEN = re.compile(rb"""
    (?P<ws>[\x00\t\n\x0c\r ]+)
  | (?P<comment>%[^\r\n]*)
  | (?P<dopen><<) | (?P<dclose>>>)
  | (?P<hex><[0-9A-Fa-f\x00\t\n\x0c\r ]*>)
  | (?P<lpar>\()
  | (?P<name>/[^\x00\t\n\x0c\r ()<>\[\]{}/%]*)
  | (?P<punct>[\[\]{}])
  | (?P<regular>[^\x00\t\n\x0c\r ()<>\[\]{}/%]+)
""", re.X)
INT = re.compile(rb"[+-]?\d+")
REAL = re.compile(rb"[+-]?(?:\d+\.\d*|\.\d+)")
ESCAPES = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}


class ParseError(Exception):
    pass


class Name(str):
    pass


class Str(bytes):
    pass


class Ref(tuple):
    pass


class Kw(str):
    pass


class PDict:
    """A dictionary that keeps every value of a repeated key."""

    def __init__(self):
        self.items = []

    def values(self, key):
        return [v for k, v in self.items if k == key]


class Lexer:
    def __init__(self, data):
        self.d = data
        self.pos = 0
        self.ahead = []

    def _literal(self):
        d, i, depth, out = self.d, self.pos, 1, bytearray()
        while i < len(d):
            c = d[i]
            if c == 0x5C:  # backslash
                i += 1
                if i >= len(d):
                    break
                c = d[i]
                if c in ESCAPES:
                    out.append(ESCAPES[c])
                    i += 1
                elif 0x30 <= c <= 0x37:
                    j, v = i, 0
                    while j < len(d) and j < i + 3 and 0x30 <= d[j] <= 0x37:
                        v = v * 8 + d[j] - 0x30
                        j += 1
                    out.append(v & 0xFF)
                    i = j
                elif c == 0x0D:  # line continuation
                    i += 2 if d[i + 1:i + 2] == b"\n" else 1
                elif c == 0x0A:
                    i += 1
                else:
                    out.append(c)
                    i += 1
                continue
            if c == 0x28:
                depth += 1
            elif c == 0x29:
                depth -= 1
                if depth == 0:
                    self.pos = i + 1
                    return bytes(out)
            out.append(c)
            i += 1
        raise ParseError("unterminated string")

    def _scan(self):
        while self.pos < len(self.d):
            start = self.pos
            m = TOKEN.match(self.d, start)
            if not m:
                raise ParseError(f"unreadable byte at offset {start}")
            self.pos = m.end()
            kind, text = m.lastgroup, m.group()
            if kind in ("ws", "comment"):
                continue
            if kind == "lpar":
                return ("str", Str(self._literal()), start)
            if kind == "hex":
                h = re.sub(rb"[\x00\t\n\x0c\r ]", b"", text[1:-1])
                if len(h) % 2:
                    h += b"0"
                return ("str", Str(bytes.fromhex(h.decode("ascii"))), start)
            if kind == "name":
                raw = re.sub(rb"#([0-9A-Fa-f]{2})", lambda x: bytes([int(x.group(1), 16)]), text[1:])
                return ("name", Name(raw.decode("latin-1")), start)
            if kind in ("dopen", "dclose", "punct"):
                return (text.decode("ascii"), None, start)
            if INT.fullmatch(text):
                return ("int", int(text), start)
            if REAL.fullmatch(text):
                return ("real", float(text), start)
            return ("kw", Kw(text.decode("latin-1")), start)
        return None

    def next(self):
        return self.ahead.pop(0) if self.ahead else self._scan()

    def peek(self, k=0):
        while len(self.ahead) <= k:
            t = self._scan()
            if t is None:
                return None
            self.ahead.append(t)
        return self.ahead[k]

    def value(self, t):
        if t is None:
            raise ParseError("unexpected end of file")
        kind, v, pos = t
        if kind == "<<":
            d = PDict()
            while True:
                k = self.next()
                if k is None:
                    raise ParseError(f"unterminated dictionary at offset {pos}")
                if k[0] == ">>":
                    return d
                if k[0] != "name":
                    raise ParseError(f"dictionary key that is not a name at offset {k[2]}")
                d.items.append((k[1], self.value(self.next())))
        if kind == "[":
            arr = []
            while True:
                x = self.next()
                if x is None:
                    raise ParseError(f"unterminated array at offset {pos}")
                if x[0] == "]":
                    return arr
                arr.append(self.value(x))
        if kind == "int":
            # "n g R" is a reference. Look ahead no further than needed: the
            # bytes after a 'stream' keyword are not tokens.
            a = self.peek(0)
            b = self.peek(1) if a and a[0] == "int" else None
            if b and b[0] == "kw" and b[1] == "R":
                self.next()
                self.next()
                return Ref((v, a[1]))
            return v
        if kind in ("str", "name", "real"):
            return v
        if kind == "kw" and v in ("true", "false", "null"):
            return {"true": True, "false": False, "null": None}[v]
        raise ParseError(f"unexpected {kind} {v!r} at offset {pos}")

    def skip_stream(self, length, pos):
        d, i = self.d, self.pos
        if self.ahead:
            raise ParseError(f"stream at offset {pos}: internal lookahead")
        if d[i:i + 2] == b"\r\n":
            i += 2
        elif d[i:i + 1] == b"\n":
            i += 1
        else:
            raise ParseError(f"stream at offset {pos}: no end of line after 'stream'")
        m = re.compile(rb"[\r\n]{0,2}endstream").match(d, i + length)
        if not m:
            raise ParseError(f"stream at offset {pos}: /Length {length} does not end at 'endstream'")
        self.pos = m.end()


def parse(data):
    """Every top-level object, as {(num, gen): value}, and the trailer dictionaries."""
    # Lengths given as indirect objects ("/Length 12 0 R"), found before parsing.
    direct_ints = {}
    for m in re.finditer(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\s*(\d+)\s*endobj", data):
        direct_ints.setdefault((int(m.group(1)), int(m.group(2))), set()).add(int(m.group(3)))
    lx = Lexer(data)
    objs, trailers = {}, []
    while True:
        t = lx.next()
        if t is None:
            break
        kind, v, pos = t
        if kind == "int":
            g, o = lx.next(), lx.next()
            if not (g and g[0] == "int" and o and o[0] == "kw" and o[1] == "obj"):
                raise ParseError(f"expected 'n g obj' at offset {pos}")
            key = (v, g[1])
            if key in objs:
                raise ParseError(f"object {v} {g[1]} is defined twice (an incremental update)")
            val = lx.value(lx.next())
            e = lx.next()
            if e and e[0] == "kw" and e[1] == "stream":
                if not isinstance(val, PDict) or len(val.values("Length")) != 1:
                    raise ParseError(f"stream without one /Length at offset {pos}")
                n = val.values("Length")[0]
                if isinstance(n, Ref):
                    found = direct_ints.get(n, set())
                    if len(found) != 1:
                        raise ParseError(f"stream at offset {pos}: cannot resolve its /Length")
                    n = next(iter(found))
                if not isinstance(n, int) or n < 0:
                    raise ParseError(f"stream at offset {pos}: bad /Length")
                lx.skip_stream(n, pos)
                e = lx.next()
            if not (e and e[0] == "kw" and e[1] == "endobj"):
                raise ParseError(f"object {v} {g[1]} at offset {pos} does not end with 'endobj'")
            objs[key] = val
        elif kind == "kw" and v == "xref":
            while True:
                p = lx.peek()
                if p is None or (p[0] == "kw" and p[1] == "trailer"):
                    break
                p = lx.next()
                if not (p[0] == "int" or (p[0] == "kw" and p[1] in ("n", "f"))):
                    raise ParseError(f"bad cross-reference table entry at offset {p[2]}")
        elif kind == "kw" and v == "trailer":
            trailers.append(lx.value(lx.next()))
        elif kind == "kw" and v == "startxref":
            n = lx.next()
            if not n or n[0] != "int":
                raise ParseError(f"'startxref' without an offset at offset {pos}")
        else:
            raise ParseError(f"unexpected {kind} {v!r} at offset {pos}")
    return objs, trailers


def show(v):
    if isinstance(v, Str):
        return repr(bytes(v).decode("latin-1"))[:120]
    return type(v).__name__ if v is not None else "nothing"


def problems(objs, trailers):
    out = []

    def resolve(v):
        seen = set()
        while isinstance(v, Ref):
            if v in seen:
                return None
            seen.add(v)
            v = objs.get(v)
        return v

    def walk(v, where):
        if isinstance(v, Name):
            if v in REFUSED:
                out.append(f"{where}: /{v}")
        elif isinstance(v, list):
            for x in v:
                walk(x, where)
        elif isinstance(v, PDict):
            for k, x in v.items:
                if k in REFUSED:
                    out.append(f"{where}: /{k}")
                walk(x, where)
            for x in v.values("URI"):
                s = resolve(x)
                if not (isinstance(s, Str) and re.match(rb"(?i)https?://", s)):
                    out.append(f"{where}: link to {show(s)} (only http:// and https:// links)")
            for x in v.values("Annots"):
                arr = resolve(x)
                if not isinstance(arr, list):
                    out.append(f"{where}: /Annots is not an array")
                    continue
                for a in arr:
                    ad = resolve(a)
                    sub = [resolve(s) for s in ad.values("Subtype")] if isinstance(ad, PDict) else []
                    if not sub or any(s != "Link" or not isinstance(s, Name) for s in sub):
                        out.append(f"{where}: an annotation that is not a link "
                                   f"({', '.join('/' + s if isinstance(s, Name) else show(s) for s in sub) or 'no /Subtype'})")

    for (num, gen), v in sorted(objs.items()):
        walk(v, f"object {num} {gen}")
    for i, t in enumerate(trailers, 1):
        walk(t, f"trailer {i}")
    if not trailers:
        out.append("no trailer (a cross-reference stream, which is not read)")
    return list(dict.fromkeys(out))


def main(argv):
    if len(argv) < 2 or any(a.startswith("-") for a in argv[1:]):
        print(__doc__)
        return 2
    bad = False
    for path in argv[1:]:
        try:
            data = Path(path).read_bytes()
        except OSError as e:
            print(f"{path}: cannot read: {e}")
            bad = True
            continue
        if not data.startswith(b"%PDF-"):
            print(f"{path}: not a PDF")
            bad = True
            continue
        try:
            found = problems(*parse(data))
        except ParseError as e:
            print(f"{path}: cannot parse: {e}")
            bad = True
            continue
        for p in found[:40]:
            print(f"{path}: {p}")
        if len(found) > 40:
            print(f"{path}: ... {len(found) - 40} more")
        bad = bad or bool(found)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
