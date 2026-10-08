"""Validate a precedence-findings.json and write precedence-stats.json beside it.

Usage: python -I -X utf8 precedence_stats.py <preprint dir> [<writeup dir>]

<preprint dir> holds precedence-findings.json and build/ (the preprint's TeX).
<writeup dir> is the review's built writeup/ folder. Its parts/summary.tex is
checked against build/precedence-findings.aux. A path to parts/summary.tex is
also accepted.

Hard checks. Any failure prints "VALIDATION FAILED" and the errors, exits 1,
and leaves no precedence-stats.json behind.
  - The JSON parses (UTF-8, BOM allowed), has no duplicate keys, and every
    documented field is present with its documented type.
  - format, format_version and definitions equal the canonical ones.
  - Finding ids and preprint_bib_key values are unique.
  - Every category, grade and status is defined. Grades fit categories
    (A/B: Strong/Partial; C: Major/Moderate). Every source key resolves.
  - Statuses agree with in_preprint_bibliography: not_cited needs false;
    cited_for_other_content, credited_in_part and credited_elsewhere need true.
  - A source with in_preprint_bibliography true has a preprint_bib_key that is
    cited in build/**/*.tex by a \\cite-family command or \\nocite.
    \\nocite{*} cites every key of every .bib under build/.
    A source with false has no preprint_bib_key.
  - With <writeup dir>: each summary row "\\ref{f:<slug>} & \\grade{G}", with
    an optional " (B)" or " (C)", is mapped to an ID by
    \\newlabel{f:<slug>}{{<ID>}...} in the .aux. The IDs, grades and categories
    must equal the JSON's, both ways. An unmarked row is category A.

Warnings, printed but never fatal: a source marked not in the bibliography
whose arXiv id or DOI (as a whole token), or whose exact normalized title,
appears in a .bib, .bbl or \\bibitem under build/. These are hints to check by
hand. A .bib entry that is never cited is not in the bibliography.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding="utf-8")

FORMAT = "math-lineage/precedence-findings"
FORMAT_VERSION = 1
DEFINITIONS = {
    "category": {
        "A": "Unattributed reuse: a technique, construction, identity, estimate or body of theory from an identifiable earlier paper is reused without credit for that content.",
        "B": "Same-problem precedence: earlier, uncited partial progress on the same problem, such as a weaker or special-case version of a statement the preprint proves.",
        "C": "Structural: a published result would replace or substantially shorten a large part of the argument.",
    },
    "grade": {
        "Strong": "(A/B) The earlier technique is reused essentially intact without credit for that content.",
        "Partial": "(A/B) Only a fragment is reused, or the credit is present but only indirect.",
        "Major": "(C) A route, a section, or a component of the main theorem becomes a citation.",
        "Moderate": "(C) A multi-page chain of lemmas becomes a citation.",
    },
    "source_status": {
        "not_cited": "The work is not in the preprint's bibliography.",
        "cited_for_other_content": "The work is in the preprint's bibliography but is not cited for this content.",
        "credited_in_part": "The preprint cites the work for part of this content only.",
        "credited_elsewhere": "The preprint cites the work for this content at other locations, but not where the content is used.",
        "credited_indirectly": "The preprint cites a location (e.g. a companion lemma) that itself credits the work for this content.",
    },
}
NEEDS_BIB = {"cited_for_other_content", "credited_in_part", "credited_elsewhere"}
MIN_TITLE = 12  # normalized characters; shorter titles give no title warning

STR, INT, BOOL, LIST, DICT, NULL = str, int, bool, list, dict, type(None)


# ---------------------------------------------------------------- reading

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def strip_comments(t):
    return re.sub(r"(?<!\\)%[^\n]*", "", t)


def close_of(s, i):
    """s[i] is one of { [ ( ; return the index of its matching closer, or len(s)."""
    opener = s[i]
    closer = {"{": "}", "[": "]", "(": ")"}[opener]
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return n


def load_json(path, errors):
    dups = []

    def hook(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                dups.append(k)
            obj[k] = v
        return obj

    try:
        text = path.read_text(encoding="utf-8-sig")
        data = json.loads(text, object_pairs_hook=hook)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        errors.append(f"cannot read {path}: {e}")
        return None
    for k in dups:
        errors.append(f"duplicate JSON key {k!r} (a JSON parser keeps only the last one)")
    return data


# ---------------------------------------------------------------- types

def type_name(types):
    names = {str: "string", int: "integer", bool: "boolean", list: "list", dict: "object", NULL: "null"}
    return " or ".join(names[t] for t in types)


def has_type(v, types):
    if isinstance(v, bool):
        return bool in types
    return isinstance(v, types)


def check_types(data, errors):
    def field(obj, name, types, where, required=True):
        if name not in obj:
            if required:
                errors.append(f"{where}: missing field {name!r}")
            return None
        v = obj[name]
        if not has_type(v, types):
            errors.append(f"{where}.{name}: expected {type_name(types)}, got {json.dumps(v, ensure_ascii=False)[:60]}")
            return None
        return v

    def str_list(obj, name, where):
        v = field(obj, name, (LIST,), where)
        for i, x in enumerate(v or []):
            if not isinstance(x, str):
                errors.append(f"{where}.{name}[{i}]: expected string, got {json.dumps(x, ensure_ascii=False)[:60]}")

    if not isinstance(data, dict):
        errors.append("the top level is not a JSON object")
        return
    field(data, "format", (STR,), "file")
    field(data, "format_version", (INT,), "file")
    pre = field(data, "preprint", (DICT,), "file")
    if pre is not None:
        for k in ("id", "title", "date", "path"):
            field(pre, k, (STR,), "preprint")
        comps = field(pre, "companions", (LIST,), "preprint")
        for i, c in enumerate(comps or []):
            if not isinstance(c, dict):
                errors.append(f"preprint.companions[{i}]: expected object")
                continue
            for k in ("id", "cited_as"):
                field(c, k, (STR,), f"preprint.companions[{i}]")
    rev = field(data, "review", (DICT,), "file")
    if rev is not None:
        for k in ("date", "report_pdf", "report_tex", "locator_convention"):
            field(rev, k, (STR,), "review")
    field(data, "definitions", (DICT,), "file")
    sources = field(data, "sources", (DICT,), "file")
    for key, s in (sources or {}).items():
        w = f"sources.{key}"
        if not isinstance(s, dict):
            errors.append(f"{w}: expected object")
            continue
        str_list(s, "authors", w)
        field(s, "title", (STR,), w)
        field(s, "year", (INT,), w)
        field(s, "venue", (STR, NULL), w)
        field(s, "arxiv", (STR, NULL), w)
        field(s, "doi", (STR, NULL), w)
        field(s, "in_preprint_bibliography", (BOOL,), w)
        field(s, "preprint_bib_key", (STR,), w, required=False)
    findings = field(data, "findings", (LIST,), "file")
    for i, f in enumerate(findings or []):
        w = f"findings[{i}]"
        if not isinstance(f, dict):
            errors.append(f"{w}: expected object")
            continue
        fid = f.get("id")
        if isinstance(fid, str):
            w = f"finding {fid}"
        for k in ("id", "category", "grade", "technique", "summary"):
            field(f, k, (STR,), w)
        str_list(f, "preprint_locations", w)
        field(f, "credit_in_preprint", (STR, NULL), w)
        field(f, "impact", (STR,), w, required=False)
        srcs = field(f, "sources", (LIST,), w)
        if srcs is not None and not srcs:
            errors.append(f"{w}: sources is empty")
        for j, s in enumerate(srcs or []):
            ws = f"{w}.sources[{j}]"
            if not isinstance(s, dict):
                errors.append(f"{ws}: expected object")
                continue
            field(s, "key", (STR,), ws)
            field(s, "locators", (STR, NULL), ws)
            field(s, "role", (STR,), ws)
            field(s, "status", (STR,), ws)


# ---------------------------------------------------------------- citations

CITE = re.compile(r"\\([A-Za-z]*[cC]ite[A-Za-z]*|nocite)(?![A-Za-z])\*?")


def cited_keys(tex):
    """Keys of every \\cite-family command and \\nocite: optional arguments,
    starred forms, several keys, and biblatex's \\cites{a}{b}."""
    keys, n = set(), len(tex)
    for m in CITE.finditer(tex):
        multi = m.group(1).endswith("cites")
        i = m.end()
        while True:
            while True:
                while i < n and tex[i] in " \t\r\n":
                    i += 1
                if i < n and (tex[i] == "[" or (multi and tex[i] == "(")):
                    i = close_of(tex, i) + 1
                else:
                    break
            if i < n and tex[i] == "{":
                j = close_of(tex, i)
                keys.update(k.strip() for k in tex[i + 1:j].split(",") if k.strip())
                i = j + 1
                if multi:
                    continue
            break
    return keys


def bib_file_keys(text):
    return {m.group(2) for m in re.finditer(r"@\s*(\w+)\s*[{(]\s*([^,\s{}()]+)\s*,", text)
            if m.group(1).lower() not in ("string", "comment", "preamble")}


# ---------------------------------------------------------------- warnings (hints only)

GREEK = set("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron "
            "pi rho sigma tau upsilon phi chi psi omega".split())
TEX_LETTERS = {"ss": "ss", "o": "o", "O": "o", "l": "l", "L": "l", "ae": "ae", "AE": "ae",
               "oe": "oe", "OE": "oe", "aa": "a", "AA": "a", "i": "i", "j": "j"}
UNI_LETTERS = {"ß": "ss", "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "æ": "ae", "Æ": "ae",
               "œ": "oe", "Œ": "oe", "ı": "i"}


def _tex_word(m):
    w = m.group(1)
    if w in TEX_LETTERS:
        return TEX_LETTERS[w]
    w = w.lower()
    if w.startswith("var") and w[3:] in GREEK:
        w = w[3:]
    return w if w in GREEK else ""


def _uni_char(ch):
    if ch in UNI_LETTERS:
        return UNI_LETTERS[ch]
    name = unicodedata.name(ch, "")
    if name.startswith("GREEK"):
        for w in name.lower().split():
            if w in GREEK:
                return w
    return ch


def norm_title(s):
    """Lowercase ASCII letters and digits only: TeX accents and Unicode
    diacritics stripped, Greek letters spelled out (\\beta and β -> beta)."""
    s = re.sub(r"\\([A-Za-z]+)", _tex_word, s)
    s = re.sub(r"\\.", "", s)
    s = "".join(_uni_char(c) for c in unicodedata.normalize("NFKC", s))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


OLD_ARCHIVES = sorted(
    "acc-phys adap-org alg-geom ao-sci astro-ph atom-ph bayes-an chao-dyn chem-ph cmp-lg comp-gas "
    "cond-mat cs dg-ga funct-an gr-qc hep-ex hep-lat hep-ph hep-th math math-ph mtrl-th nlin nucl-ex "
    "nucl-th patt-sol physics plasm-ph q-alg q-bio q-fin quant-ph solv-int stat supr-con".split(),
    key=len, reverse=True)
ARXIV_NEW = re.compile(r"(?<!\d)(?<!\d\.)(\d\d)(\d\d)\.(\d{4,5})(?:v\d+)?(?![\d.]\d)(?!\d)")
ARXIV_OLD = re.compile(r"(?<![A-Za-z-])(" + "|".join(re.escape(a) for a in OLD_ARCHIVES)
                       + r")(?:\.[A-Za-z]{2})?/(\d\d)(\d\d)(\d{3})(?:v\d+)?(?!\d)", re.I)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>{}\\]+")


def arxiv_ids(text):
    """arXiv ids in text, as whole tokens, without version: 2203.05093, math/0505690."""
    out = set()
    for m in ARXIV_NEW.finditer(text):
        yy, mm, num = m.group(1), m.group(2), m.group(3)
        if not 1 <= int(mm) <= 12 or int(yy) < 7:
            continue
        if len(num) != (4 if (int(yy), int(mm)) < (15, 1) else 5):
            continue
        out.add(f"{yy}{mm}.{num}")
    for m in ARXIV_OLD.finditer(text):
        if 1 <= int(m.group(3)) <= 12:
            out.add(f"{m.group(1).lower()}/{m.group(2)}{m.group(3)}{m.group(4)}")
    return out


def canon_doi(d):
    d = unquote(d.strip()).lower()
    d = re.sub(r"^(?:https?://)?(?:dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d).rstrip(".,;:")
    while d.endswith(")") and d.count(")") > d.count("("):
        d = d[:-1]
    return d


def dois(text):
    return {canon_doi(m.group(0)) for m in DOI_RE.finditer(unquote(text))}


def tex_clean(t):
    return t.replace("{\\_}", "_").replace("\\_", "_").replace("\\%", "%")


def bib_records(text):
    """(key, entry text, {normalized title}) for each .bib entry."""
    starts = [m for m in re.finditer(r"@\s*(\w+)\s*[{(]\s*([^,\s{}()]+)\s*,", text)
              if m.group(1).lower() not in ("string", "comment", "preamble")]
    for k, m in enumerate(starts):
        body = text[m.start():starts[k + 1].start() if k + 1 < len(starts) else len(text)]
        titles = set()
        t = re.search(r"(?<![A-Za-z])title\s*=\s*([{\"])", body, re.I)
        if t:
            if t.group(1) == "{":
                j = close_of(body, t.end() - 1)
                titles.add(norm_title(body[t.end():j]))
            else:
                q = re.match(r"((?:[^\"\\]|\\.)*)\"", body[t.end():])
                if q:
                    titles.add(norm_title(q.group(1)))
        yield m.group(2), body, titles


def item_records(text):
    """(key, item text, {normalized title candidates}) for each \\bibitem."""
    marks = list(re.finditer(r"\\bibitem(?![A-Za-z])", text))
    for k, m in enumerate(marks):
        i, n = m.end(), len(text)
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i < n and text[i] == "[":
            i = close_of(text, i) + 1
            while i < n and text[i] in " \t\r\n":
                i += 1
        if not (i < n and text[i] == "{"):
            continue
        j = close_of(text, i)
        key = text[i + 1:j].strip()
        end = marks[k + 1].start() if k + 1 < len(marks) else n
        e = text.find("\\end{thebibliography}", j)
        if 0 <= e < end:
            end = e
        body = text[j + 1:end]
        segs = re.split(r"\\newblock", body)
        for em in re.finditer(r"\\(?:emph|textit|textsl)\s*\{", body):
            segs.append(body[em.end():close_of(body, em.end() - 1)])
        segs += re.findall(r"``(.*?)''", body, re.S)
        for seg in list(segs):
            segs += re.split(r",\s", seg)
        yield key, body, {norm_title(x) for x in segs} - {""}


def bibliography_hints(build, sources, cited, base):
    records = []  # (where, key, text, titles, is_bib)
    for p in sorted(build.rglob("*")):
        suf = p.suffix.lower()
        if suf not in (".bib", ".bbl", ".tex") or not p.is_file():
            continue
        text = read(p)
        where = p.relative_to(base).as_posix()
        if suf == ".bib":
            records += [(where, k, tex_clean(b), t, True) for k, b, t in bib_records(text)]
        elif "\\bibitem" in text:
            records += [(where, k, tex_clean(b), t, False) for k, b, t in item_records(strip_comments(text))]
    rec_ids = [(r, arxiv_ids(r[2]), dois(r[2])) for r in records]
    hints = []
    for key, s in sources.items():
        if s["in_preprint_bibliography"]:
            continue
        ax = set()
        if s.get("arxiv"):
            ax = arxiv_ids(s["arxiv"]) or {re.sub(r"v\d+$", "", re.sub(r"^\s*arxiv:\s*", "", s["arxiv"].strip().lower()))}
        dz = {canon_doi(s["doi"])} if s.get("doi") else set()
        title = norm_title(s["title"])
        for (where, rkey, _text, titles, is_bib), rax, rdoi in rec_ids:
            what = []
            if ax & rax:
                what.append("arXiv id " + ", ".join(sorted(ax & rax)))
            if dz & rdoi:
                what.append("DOI " + ", ".join(sorted(dz & rdoi)))
            if len(title) >= MIN_TITLE and title in titles:
                what.append("title")
            if what:
                note = ""
                if is_bib:
                    note = "; the TeX cites that key" if rkey in cited else "; the TeX never cites that key"
                hints.append(f"WARNING (check by hand): {key} is marked not in the bibliography, but "
                             f"{where} entry {rkey!r} has the same {' and '.join(what)}{note}.")
    return hints


# ---------------------------------------------------------------- summary table

def summary_errors(wdir, findings):
    errors = []
    if wdir.is_file() and wdir.name == "summary.tex":
        wdir = wdir.parent.parent
    summ_p = wdir / "parts" / "summary.tex"
    aux_p = wdir / "build" / "precedence-findings.aux"
    for p in (summ_p, aux_p):
        if not p.is_file():
            errors.append(f"summary check: {p} not found (give the built writeup dir)")
    if errors:
        return errors
    summ = strip_comments(read(summ_p))
    aux = read(aux_p)
    labels = {}
    for m in re.finditer(r"\\newlabel\{f:([^{}@]+)\}\{\{", aux):
        j = close_of(aux, m.end() - 1)
        labels[m.group(1)] = re.sub(r"\\[A-Za-z]+\*?|[{}\s~]", "", aux[m.end():j])
    table = {}
    for slug, grade, cat in re.findall(r"\\ref\*?\{f:([^{}]+)\}\s*&\s*\\grade\{([^{}]*)\}(?:\s*\(([ABC])\))?", summ):
        if slug not in labels:
            errors.append(f"summary row \\ref{{f:{slug}}}: no \\newlabel{{f:{slug}}} in {aux_p.name} (rebuild the write-up)")
            continue
        fid = labels[slug]
        if fid in table:
            errors.append(f"summary table: {fid} has more than one row")
        table[fid] = (grade.strip(), cat or "A")
    mine = {f["id"]: (f["grade"], f["category"]) for f in findings}
    for fid in sorted(set(mine) | set(table)):
        if fid not in table:
            errors.append(f"{fid}: in the JSON but not in the summary table")
        elif fid not in mine:
            errors.append(f"{fid}: in the summary table but not in the JSON")
        else:
            (g, c), (tg, tc) = mine[fid], table[fid]
            if g != tg:
                errors.append(f"{fid}: grade {g} in the JSON, {tg} in the summary table")
            if c != tc:
                errors.append(f"{fid}: category {c} in the JSON, {tc} in the summary table "
                              f"(the table marks B and C with \" (B)\" / \" (C)\" after \\grade{{}}; no mark means A)")
    return errors


# ---------------------------------------------------------------- main

def fail(errors):
    print("VALIDATION FAILED")
    print("\n".join(errors))
    sys.exit(1)


def main(argv):
    if len(argv) not in (2, 3) or argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    d = Path(argv[1])
    out = d / "precedence-stats.json"
    try:
        out.unlink()
    except FileNotFoundError:
        pass

    errors = []
    data = load_json(d / "precedence-findings.json", errors)
    if data is None:
        fail(errors)
    check_types(data, errors)
    if errors:
        fail(errors)

    if data["format"] != FORMAT or data["format_version"] != FORMAT_VERSION:
        errors.append(f"format must be {FORMAT!r}, version {FORMAT_VERSION}")
    got = data["definitions"]
    if got != DEFINITIONS:
        diff = []
        for part in sorted(set(DEFINITIONS) | set(got)):
            g = got.get(part)
            if not isinstance(g, dict):
                diff.append(part)
                continue
            want = DEFINITIONS.get(part, {})
            diff += [f"{part}.{k}" for k in sorted(set(want) | set(g)) if want.get(k) != g.get(k)]
        errors.append("definitions differ from the canonical ones (copy them verbatim from "
                      "assets/precedence-findings.example.json): " + ", ".join(diff))
    defs = DEFINITIONS
    sources = data["sources"]
    findings = data["findings"]

    for fid, n in Counter(f["id"] for f in findings).items():
        if n > 1:
            errors.append(f"finding id {fid} is used {n} times")
    for bk, n in Counter(s["preprint_bib_key"] for s in sources.values() if "preprint_bib_key" in s).items():
        if n > 1:
            errors.append(f"preprint_bib_key {bk!r} is used by {n} sources")

    # Which keys does the preprint's TeX cite?
    build = d / "build"
    tex_files = sorted(build.rglob("*.tex")) if build.is_dir() else []
    cited = set()
    for p in tex_files:
        cited |= cited_keys(strip_comments(read(p)))
    if "*" in cited:
        for p in sorted(build.rglob("*.bib")):
            cited |= bib_file_keys(read(p))
    if not tex_files and any(s["in_preprint_bibliography"] for s in sources.values()):
        errors.append(f"no .tex files under {build}: cannot check which keys the preprint cites")

    for key, s in sources.items():
        bk = s.get("preprint_bib_key")
        if s["in_preprint_bibliography"]:
            if bk is None:
                errors.append(f"{key}: in_preprint_bibliography is true but preprint_bib_key is missing")
            elif tex_files and bk not in cited:
                errors.append(f"{key}: preprint_bib_key {bk!r} is not cited in any build/**/*.tex "
                              f"(no \\cite or \\nocite of it), so it is not in the preprint's bibliography")
        elif bk is not None:
            errors.append(f"{key}: has preprint_bib_key {bk!r} but in_preprint_bibliography is false")

    for f in findings:
        fid = f["id"]
        if f["category"] not in defs["category"]:
            errors.append(f"{fid}: unknown category {f['category']}")
        if f["grade"] not in defs["grade"]:
            errors.append(f"{fid}: unknown grade {f['grade']}")
        elif (f["category"] == "C") != (f["grade"] in ("Major", "Moderate")):
            errors.append(f"{fid}: grade {f['grade']} does not fit category {f['category']}")
        for src in f["sources"]:
            k, st = src["key"], src["status"]
            if k not in sources:
                errors.append(f"{fid}: unknown source key {k}")
                continue
            if st not in defs["source_status"]:
                errors.append(f"{fid}/{k}: unknown status {st}")
            inbib = sources[k]["in_preprint_bibliography"]
            if st == "not_cited" and inbib:
                errors.append(f"{fid}/{k}: status not_cited but the work is in the bibliography")
            if st in NEEDS_BIB and not inbib:
                errors.append(f"{fid}/{k}: status {st} but the work is not in the bibliography")

    if len(argv) > 2:
        errors += summary_errors(Path(argv[2]), findings)

    if build.is_dir():
        for h in bibliography_hints(build, sources, cited, d):
            print(h)

    if errors:
        fail(errors)

    pairs = [(f["id"], s["key"], s["status"]) for f in findings for s in f["sources"]]
    cited_works = {k for _, k, _ in pairs}
    by_cat_grade = {}
    for f in findings:
        by_cat_grade.setdefault(f["category"], Counter())[f["grade"]] += 1

    stats = {
        "format": "math-lineage/precedence-stats",
        "format_version": 1,
        "preprint": data["preprint"]["id"],
        "generated_from": "precedence-findings.json",
        "review_date": data["review"]["date"],
        "findings": {
            "total": len(findings),
            "by_category": {c: sum(1 for f in findings if f["category"] == c) for c in defs["category"]},
            "by_grade": {g: sum(1 for f in findings if f["grade"] == g) for g in defs["grade"]},
            "by_category_and_grade": {
                c: {g: by_cat_grade.get(c, Counter())[g] for g in defs["grade"] if by_cat_grade.get(c, Counter())[g]}
                for c in defs["category"]
            },
            "ids_by_category_and_grade": {
                c: {g: [f["id"] for f in findings if f["category"] == c and f["grade"] == g]
                    for g in defs["grade"] if any(f["category"] == c and f["grade"] == g for f in findings)}
                for c in defs["category"]
            },
        },
        "earlier_works": {
            "distinct": len(cited_works),
            "not_in_preprint_bibliography": sum(1 for k in cited_works if not sources[k]["in_preprint_bibliography"]),
            "in_preprint_bibliography": sum(1 for k in cited_works if sources[k]["in_preprint_bibliography"]),
            "finding_source_pairs_by_status": {st: sum(1 for _, _, s in pairs if s == st) for st in defs["source_status"]},
        },
    }
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print("validation passed; wrote", out)
    print(json.dumps(stats["findings"]["by_category_and_grade"]), json.dumps(stats["earlier_works"]))


if __name__ == "__main__":
    main(sys.argv)
