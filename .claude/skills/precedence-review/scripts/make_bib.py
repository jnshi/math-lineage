"""Build <writeup>/parts/bibliography.tex from the citations the write-up uses.

Usage: python3 -I -X utf8 make_bib.py <writeup dir> <prior-work/INDEX.md> [<main .tex>]

Keys are collected from \\cite{...} and \\sloc{Key}{...} in reading order: the
main file's \\input / \\fragment lines if it is given, otherwise every .tex in
parts/ and findings/. Each key is resolved from, in order:
  1. a comment line "% BIB <Key>: <full citation>" in any document file. Use
     this for the preprint and its companions (OAI-...) and for works outside
     the library (NL-...). The text is used as TeX.
  2. the "## Downloaded papers" table of prior-work/INDEX.md
     (columns: Key | Citation | arXiv / DOI | ...). The text is treated as
     plain text and escaped.
Working notes must be marked "[note: ...]" in INDEX cells; those marks are
removed, as are ";"-separated clauses of a parenthetical that contain a URL or a
file path. Nothing else is guessed: every other parenthetical that reaches the
bibliography and has three or more words, or no digits, is listed for review.
If one is a working note, mark it "[note: ...]" in INDEX.md and rerun.

Exit status 1 (after writing the file) if a key is unresolved, an INDEX row is
malformed, or an \\input target does not exist.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
writeup, index_path = sys.argv[1], sys.argv[2]
main_file = sys.argv[3] if len(sys.argv) > 3 else None
problems = []

# A ";"-separated clause of a parenthetical is dropped if it contains a URL or a file path.
URL_CLAUSE = re.compile(
    r"https?://|\bwww\.|\b[\w-]+\.(?:edu|org|com|net|gov|ac\.[a-z]{2})/|[\w.~-]+/[\w.~/-]+\.(?:pdf|ps|html?|txt|tex)\b",
    re.I,
)

UNICODE = {
    "\u2013": "--", "\u2014": "---", "\u2018": "`", "\u2019": "'", "\u201c": "``", "\u201d": "''",
    "\u2264": "$\\le$", "\u2265": "$\\ge$", "\u2016": "$\\|$", "\u2026": "\\dots{}", "\u00a0": "~",
    "\u03b1": "$\\alpha$", "\u03b2": "$\\beta$", "\u03b3": "$\\gamma$", "\u03bb": "$\\lambda$",
    "\u2212": "-", "\u00d7": "$\\times$", "\u2202": "$\\partial$",
}


def tex_escape(s):
    """Escape plain text for TeX. Backslashes and braces are escaped too, so INDEX
    text can never run TeX commands (e.g. \\input) in the bibliography."""
    s = s.replace("\\", "\x00").replace("{", "\\{").replace("}", "\\}")
    s = re.sub(r"([&%#_$])", r"\\\1", s)
    s = s.replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")
    s = s.replace("\x00", "\\textbackslash{}")
    for u, t in UNICODE.items():
        s = s.replace(u, t)
    return s


def split_top(inner, sep):
    """Split at top-level occurrences of sep (not inside nested parentheses)."""
    parts, buf, depth = [], "", 0
    for ch in inner:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and ch == sep:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return parts


def filter_parenthetical(inner):
    """Return None if no clause has a URL or path, else the remaining clauses ('' if none)."""
    clauses = split_top(inner, ";")
    if not any(URL_CLAUSE.search(c) for c in clauses):
        return None
    return "; ".join(c.strip() for c in clauses if c.strip() and not URL_CLAUSE.search(c))


def strip_note_marks(s):
    """Remove every "[note: ...]" mark, allowing nested brackets inside it."""
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == "[" and s[i + 1:i + 6].lower() == "note:":
            depth, j = 0, i
            while j < n:
                if s[j] == "[":
                    depth += 1
                elif s[j] == "]":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= n:
                problems.append("unterminated [note: ...] in: " + s[:80])
                break
            while out and out[-1] in " \t":
                out.pop()
            i = j + 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def strip_notes(s):
    s = strip_note_marks(s)
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] != "(":
            out.append(s[i])
            i += 1
            continue
        depth, j = 0, i
        while j < n:
            if s[j] == "(":
                depth += 1
            elif s[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n:  # unbalanced: keep the rest as is
            out.append(s[i:])
            break
        kept = filter_parenthetical(s[i + 1:j])
        if kept is None:
            out.append(s[i:j + 1])
        elif kept:
            out.append("(" + kept + ")")
        i = j + 1
    text = re.sub(r"[ \t]{2,}", " ", "".join(out))
    return re.sub(r"\s+([.,;:])", r"\1", text).strip()


def document_files():
    """Document files in reading order."""
    skip = ("preamble", "bibliography")
    if main_file:
        text = io.open(os.path.join(writeup, main_file), encoding="utf-8-sig").read()
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        paths = []
        for m in re.finditer(r"\\input\{([^}]+)\}|\\fragment\{([^}]+)\}", text):
            rel = m.group(1) or ("findings/" + m.group(2))
            if "#" in rel:  # a macro parameter, e.g. \input{findings/#1} inside a \newcommand
                continue
            stem = rel[:-4] if rel.endswith(".tex") else rel
            if stem.endswith(skip):
                continue
            p = os.path.join(writeup, stem + ".tex")
            if os.path.isfile(p):
                paths.append(p)
            elif m.group(1):  # \fragment may point at a draft that doesn't exist yet; \input may not
                problems.append(f"\\input target not found: {stem}.tex")
        return paths
    paths = []
    for sub in ("parts", "findings"):
        d = os.path.join(writeup, sub)
        for name in sorted(os.listdir(d)):
            if name.endswith(".tex") and not name[:-4].endswith(skip):
                paths.append(os.path.join(d, name))
    return paths


def used_keys():
    keys, explicit = [], {}
    for path in document_files():
        text = io.open(path, encoding="utf-8-sig").read()
        for m in re.finditer(r"(?m)^\s*%\s*BIB\s+([A-Za-z0-9._:-]+)\s*:\s*(.+)$", text):
            explicit.setdefault(m.group(1), m.group(2).strip())
        body = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        for m in re.finditer(r"\\cite(?:\[[^\]]*\])?\{([^}]*)\}", body):
            keys += [k.strip() for k in m.group(1).split(",")]
        for m in re.finditer(r"\\sloc\{([^}]*)\}", body):
            keys.append(m.group(1).strip())
    seen, ordered = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            ordered.append(k)
    return ordered, explicit


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def index_table():
    """Rows of the "## Downloaded papers" table: key -> (citation, ids), or None if malformed."""
    rows = {}
    lines = io.open(index_path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    in_section, ncols = False, None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            in_section, ncols = line.startswith("## Downloaded papers"), None
            continue
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue  # separator row
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if ncols is None:
            if re.match(r"^\s*\|\s*:?-{3,}", nxt):
                ncols = len(cells)  # header row
            continue
        key = cells[0].strip("`").strip()
        if len(cells) != ncols:
            rows.setdefault(key, None)
            problems.append(f"INDEX.md line {i + 1}: {len(cells)} cells, expected {ncols} "
                            f"(a literal '|' in a cell?); key {key[:60]!r}")
            continue
        rows[key] = (cells[1], cells[2])
    return rows


keys, explicit = used_keys()
rows = index_table()
missing, items, review = [], [], []
for k in keys:
    if k in explicit:
        cit = strip_notes(explicit[k])
        review += [f"{k}: {p}" for p in re.findall(r"\([^()]*\)", cit)
                   if not re.search(r"\d", p) or len(p.split()) >= 3]
        # Explicit entries are written as TeX (e.g. \emph{...}); escape only if they look like plain text.
        items.append((k, cit if "\\" in cit else tex_escape(cit)))
    elif rows.get(k):
        cit, ids = (strip_notes(c) for c in rows[k])
        review += [f"{k}: {p}" for p in re.findall(r"\([^()]*\)", cit + " " + ids)
                   if not re.search(r"\d", p) or len(p.split()) >= 3]
        entry = tex_escape(cit.rstrip(" ."))
        if ids:
            entry += ". " + tex_escape(ids)
        items.append((k, entry + "."))
    else:
        missing.append(k + (" (malformed INDEX row)" if k in rows else ""))
        items.append((k, "\\textbf{[missing bibliography entry for key " + tex_escape(k) + "]}"))

out = ["\\begin{thebibliography}{99}", "\\small"]
out += ["\\bibitem{%s} %s" % (k, text) for k, text in items]
out.append("\\end{thebibliography}")
with io.open(os.path.join(writeup, "parts", "bibliography.tex"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(out) + "\n")
print("keys:", len(keys), "missing:", missing)
if review:
    print("parentheticals kept in the bibliography (check none is a working note; if one is, mark it "
          "[note: ...] in INDEX.md):")
    for r in review:
        print("  " + r)
if problems:
    print("problems:")
    for p in problems:
        print("  " + p)
if missing or problems:
    sys.exit(1)
