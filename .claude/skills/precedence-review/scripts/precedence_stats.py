"""Validate a precedence-findings.json and write precedence-stats.json beside it.

Usage: python -I -X utf8 precedence_stats.py <preprint dir> [<writeup dir>]

<preprint dir> holds precedence-findings.json and build/ (the preprint's TeX).
<writeup dir> is the review's built writeup/ folder. Its parts/summary.tex is
checked against build/precedence-findings.aux. A path to parts/summary.tex is
also accepted.

An empty <preprint dir> argument, or a folder without precedence-findings.json,
is refused and nothing is deleted. A file that does not parse, or is not
format version 2, fails without touching precedence-stats.json. Once the file
is known to be version 2, any old precedence-stats.json is deleted, and a new
one is written only if every check passes.

Hard checks (format version 2). Any failure prints "VALIDATION FAILED" and the
errors and exits 1.
  - A version 1 file (categories A/B/C and grades; format_version the integer
    1) fails with a request to update it to version 2; it is not validated
    further.
  - The JSON parses (UTF-8, BOM allowed), has no duplicate keys, and every
    documented field is present with its documented type. These strings are
    non-empty: preprint.id, each source's title, and each finding's slug,
    technique, summary, credit_in_preprint and each source role; these lists
    are non-empty: preprint_locations, sources and each source's authors.
  - format, format_version and definitions equal the canonical ones.
  - Finding ids, slugs and preprint_bib_key values are unique, and a finding
    lists each source key once.
  - Every relationship, centrality, form_of_inclusion and credit_status is
    defined, and every source key resolves. A weaker result is never main
    result.
  - A finding in the report has an id F1, F2, ... (running without gaps) and a
    form_of_inclusion other than none. A finding kept in the JSON only has
    in_report false, id null and form_of_inclusion none.
  - Magnitude order: the findings in the report, in ID order, have
    non-decreasing (centrality rank, relationship rank). Centrality ranks:
    main result, central, supporting, peripheral. Relationship ranks: same
    result, same technique, adapted, proof shortcut, same route, fragment,
    weaker result.
  - attribution_gap equals its definition: relationship same technique,
    adapted or same result; centrality main result, central or supporting;
    and the principal source (the first listed in sources) not_cited or
    cited_for_other_content.
  - overstated_novelty (the one case where credited content is reported) needs
    every source credited, credited_elsewhere or credited_in_part, a
    novelty_claim, and a form_of_inclusion other than citation (the forms then
    describe revising the abstract or framing); credit_status credited appears
    only with it.
  - Credit statuses agree with in_preprint_bibliography: not_cited needs false;
    every other status needs true.
  - A source with in_preprint_bibliography true has a preprint_bib_key that is
    cited in build/**/*.tex by a \\cite-family command or \\nocite.
    \\nocite{*} cites every key of every .bib under build/.
    A source with false has no preprint_bib_key.
  - With <writeup dir>: the \\newlabel{f:<slug>} labels in
    build/precedence-findings.aux (the findings printed in the report) are
    exactly the slugs of the JSON's findings in the report, with the same IDs.
    Each summary row starts "\\ref{f:<slug>} & \\rel{<relationship>} &
    <centrality> &", and is mapped to an ID by \\newlabel{f:<slug>}{{<ID>}...}.
    IDs, slugs, relationships and centralities must equal those of the JSON's
    findings in the report, both ways, and a row contains \\attrgap exactly
    when attribution_gap is true and \\overstated exactly when
    overstated_novelty is true.

Warnings, printed but never fatal: a source marked not in the bibliography
whose arXiv id or DOI (as a whole token), or whose exact normalized title,
appears in a .bib, .bbl or \\bibitem under build/. These are hints to check by
hand. A .bib entry that is never cited is not in the bibliography.

The stats count the findings in the report, except by_form_of_inclusion, which
counts every finding, JSON-only ones included (they are its "none" count).
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
FORMAT_VERSION = 2
# Version 1 (categories A/B/C, grades Strong/Partial/Major/Moderate) is
# superseded: a version 1 file fails with a request to update it.

# Version 2: relationship types replace categories and grades. A reported
# finding is content whose citation is missing where it is used, so credit
# statuses mostly describe kinds of missing citation; content the preprint
# credits there, directly or through a cited location that credits it, is not
# a finding. The one exception is overstated novelty: the earlier work is
# cited for the content, but the abstract or framing presents it as new.
DEFINITIONS = {
    "relationship": {
        "same technique": "The earlier technique, construction or theory is reused essentially intact, possibly in a new setting or with new ingredients around it.",
        "adapted": "The earlier technique's structure is followed, with a change at its core: a different object, or a key step replaced.",
        "fragment": "One identifiable piece of the earlier technique is reused.",
        "same route": "An earlier paper proposed the proof strategy, even heuristically, and the preprint carries it out.",
        "same result": "An earlier paper, or several earlier papers together, prove essentially the same statement.",
        "weaker result": "An earlier paper proves a weaker, special-case or partial-range version of a statement the preprint proves.",
        "proof shortcut": "A published result would replace or substantially shorten a large part of the argument.",
    },
    "centrality": {
        "main result": "Best-effort judgment: the earlier work covers the main result itself, or most of it. Never a weaker result.",
        "central": "Best-effort judgment: much of the main argument depends on it.",
        "supporting": "Best-effort judgment: the main argument depends on it, but less.",
        "peripheral": "Best-effort judgment: little of the main argument depends on it.",
    },
    "form_of_inclusion": {
        "none": "As judged by the author-persona check: not worth a pointer, or for overstated novelty no change to the abstract or framing. Recorded here only, not in the report.",
        "citation": "As judged by the author-persona check: a citation at the point of use.",
        "sentence": "As judged by the author-persona check: a clause or a sentence; for overstated novelty, a clause or sentence changed in the abstract, contribution statements or framing.",
        "paragraph": "As judged by the author-persona check: a short paragraph; for overstated novelty, a larger revision of the abstract or framing.",
    },
    "credit_status": {
        "not_cited": "The work is not in the preprint's bibliography.",
        "cited_for_other_content": "The work is in the preprint's bibliography but is not cited for this content.",
        "credited_elsewhere": "The preprint cites the work for this content at other locations, but not where the content is used.",
        "credited_in_part": "The preprint cites the work for part of this content only.",
        "credited": "The preprint cites the work for this content. Allowed only in a finding with overstated novelty.",
    },
    "flags": {
        "attribution_gap": "True when the relationship is same technique, adapted or same result; the centrality is main result, central or supporting; and the principal earlier work (listed first among the sources) is not cited for this content anywhere (not_cited or cited_for_other_content).",
        "overstated_novelty": "True when the preprint cites the earlier work for this content, but its abstract, a statement of its contributions, or the framing of a main result presents that content as new, explicitly or in the way a reader would reasonably take it. It is the one case in which content the preprint credits is reported. novelty_claim says where the claim is made.",
    },
}
GAP_RELATIONSHIPS = {"same technique", "adapted", "same result"}
GAP_CENTRALITY = {"main result", "central", "supporting"}
# Magnitude order of the findings in the report: (centrality rank, relationship rank).
CENTRALITY_RANK = {"main result": 0, "central": 1, "supporting": 2, "peripheral": 3}
RELATIONSHIP_RANK = {"same result": 0, "same technique": 1, "adapted": 2, "proof shortcut": 3,
                     "same route": 4, "fragment": 5, "weaker result": 6}
GAP_STATUSES = {"not_cited", "cited_for_other_content"}
NEEDS_BIB = {"cited_for_other_content", "credited_elsewhere", "credited_in_part", "credited"}
OVERSTATED_STATUSES = {"credited", "credited_elsewhere", "credited_in_part"}
ID_RE = re.compile(r"F[1-9][0-9]*")
MIN_TITLE = 12  # normalized characters; shorter titles give no title warning

STR, INT, BOOL, LIST, DICT, NULL = str, int, bool, list, dict, type(None)


# ---------------------------------------------------------------- reading

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def strip_comments(t):
    """Remove TeX comments: a % after an even number of backslashes (\\% is a
    percent sign, \\\\% a line break and then a comment)."""
    return re.sub(r"(?<!\\)((?:\\\\)*)%[^\n]*", r"\1", t)


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
    def field(obj, name, types, where, required=True, nonempty=False):
        if name not in obj:
            if required:
                errors.append(f"{where}: missing field {name!r}")
            return None
        v = obj[name]
        if not has_type(v, types):
            errors.append(f"{where}.{name}: expected {type_name(types)}, got {json.dumps(v, ensure_ascii=False)[:60]}")
            return None
        if nonempty and ((isinstance(v, str) and not v.strip()) or (isinstance(v, list) and not v)):
            errors.append(f"{where}.{name} is empty")
        return v

    def str_list(obj, name, where):
        v = field(obj, name, (LIST,), where, nonempty=True)
        for i, x in enumerate(v or []):
            if not isinstance(x, str):
                errors.append(f"{where}.{name}[{i}]: expected string, got {json.dumps(x, ensure_ascii=False)[:60]}")
            elif not x.strip():
                errors.append(f"{where}.{name}[{i}] is empty")

    if not isinstance(data, dict):
        errors.append("the top level is not a JSON object")
        return
    field(data, "format", (STR,), "file")
    field(data, "format_version", (INT,), "file")
    pre = field(data, "preprint", (DICT,), "file")
    if pre is not None:
        for k in ("id", "title", "date", "path"):
            field(pre, k, (STR,), "preprint", nonempty=(k == "id"))
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
        field(s, "title", (STR,), w, nonempty=True)
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
        fid = f.get("id") or f.get("slug")
        if isinstance(fid, str):
            w = f"finding {fid}"
        field(f, "id", (STR, NULL), w)
        for k in ("slug", "relationship", "centrality", "form_of_inclusion", "technique", "summary",
                  "credit_in_preprint"):
            field(f, k, (STR,), w, nonempty=k in ("slug", "technique", "summary", "credit_in_preprint"))
        field(f, "in_report", (BOOL,), w)
        field(f, "attribution_gap", (BOOL,), w)
        field(f, "overstated_novelty", (BOOL,), w)
        field(f, "novelty_claim", (STR, NULL), w, required=False)
        str_list(f, "preprint_locations", w)
        srcs = field(f, "sources", (LIST,), w, nonempty=True)
        keys = []
        for j, s in enumerate(srcs or []):
            ws = f"{w}.sources[{j}]"
            if not isinstance(s, dict):
                errors.append(f"{ws}: expected object")
                continue
            keys.append(field(s, "key", (STR,), ws))
            field(s, "locators", (STR, NULL), ws)
            field(s, "role", (STR,), ws, nonempty=True)
            field(s, "credit_status", (STR,), ws)
        for k, n in Counter(k for k in keys if k is not None).items():
            if n > 1:
                errors.append(f"{w}: source {k} is listed {n} times (list each source once)")


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

def summary_inputs(wdir, errors):
    """The summary table (comments stripped) and {slug: printed ID} from the .aux."""
    if wdir.is_file() and wdir.name == "summary.tex":
        wdir = wdir.parent.parent
    summ_p = wdir / "parts" / "summary.tex"
    aux_p = wdir / "build" / "precedence-findings.aux"
    for p in (summ_p, aux_p):
        if not p.is_file():
            errors.append(f"summary check: {p} not found (give the built writeup dir)")
    if errors:
        return None, None, aux_p
    summ = strip_comments(read(summ_p))
    aux = read(aux_p)
    labels = {}
    for m in re.finditer(r"\\newlabel\{f:([^{}@]+)\}\{\{", aux):
        j = close_of(aux, m.end() - 1)
        labels[m.group(1)] = re.sub(r"\\[A-Za-z]+\*?|[{}\s~]", "", aux[m.end():j])
    return summ, labels, aux_p


def id_key(fid):
    return (len(fid), fid)


def summary_errors(wdir, findings):
    """The aux's f: labels (the findings printed in the report) are the slugs of
    the JSON's findings in the report, with the same IDs. Each summary row starts
    "\\ref{f:<slug>} & \\rel{<relationship>} & <centrality> &", and contains
    \\attrgap and \\overstated exactly when the finding's flags are true."""
    errors = []
    summ, labels, aux_p = summary_inputs(wdir, errors)
    if summ is None:
        return errors
    rep = {f["slug"]: f["id"] for f in findings if f["in_report"]}
    for slug in sorted(set(labels) - set(rep)):
        errors.append(f"{labels[slug]} (f:{slug}) is printed in the report ({aux_p.name} has its label), but is "
                      f"not a finding in the report in the JSON (missing, or in_report is false); remove its "
                      f"\\input line or add it to the JSON and the summary table")
    for slug in sorted(set(rep) - set(labels)):
        errors.append(f"{rep[slug] or slug}: in_report is true in the JSON, but the report prints no finding "
                      f"f:{slug} (no \\newlabel{{f:{slug}}} in {aux_p.name}; add its \\input line and rebuild)")
    for slug in sorted(set(rep) & set(labels)):
        if isinstance(rep[slug], str) and rep[slug] != labels[slug]:
            errors.append(f"f:{slug} is {labels[slug]} in the report ({aux_p.name}) but {rep[slug]} in the JSON")
    table = {}
    row_re = re.compile(r"\\ref\*?\{f:([^{}]+)\}\s*&\s*\\rel\{([^{}]*)\}\s*&\s*([^&\\]+?)\s*&")
    for m in row_re.finditer(summ):
        slug, rel, cen = m.group(1), " ".join(m.group(2).split()), " ".join(m.group(3).split())
        end = summ.find("\\\\", m.end())
        row = summ[m.start():end if end >= 0 else len(summ)]
        if slug not in labels:
            errors.append(f"summary row \\ref{{f:{slug}}}: no \\newlabel{{f:{slug}}} in {aux_p.name} (rebuild the write-up)")
            continue
        fid = labels[slug]
        if fid in table:
            errors.append(f"summary table: {fid} has more than one row")
        table[fid] = (slug, rel, cen, "\\attrgap" in row, "\\overstated" in row)
    # Findings without a valid id are reported by finding_errors.
    mine = {f["id"]: (f["slug"], f["relationship"], f["centrality"], f["attribution_gap"], f["overstated_novelty"])
            for f in findings if f["in_report"] and isinstance(f["id"], str) and ID_RE.fullmatch(f["id"])}
    names = ("slug", "relationship", "centrality", "attribution gap (\\attrgap in the row)",
             "overstated novelty (\\overstated in the row)")
    for fid in sorted(set(mine) | set(table), key=id_key):
        if fid not in table:
            errors.append(f"{fid}: in the JSON but not in the summary table")
        elif fid not in mine:
            errors.append(f"{fid}: in the summary table but not in the JSON (or in_report is false)")
        else:
            for name, a, b in zip(names, mine[fid], table[fid]):
                if a != b:
                    errors.append(f"{fid}: {name} {a!r} in the JSON, {b!r} in the summary table")
    return errors


# ---------------------------------------------------------------- findings

def finding_errors(findings, sources, defs):
    errors = []
    for f in findings:
        name = f["id"] or f["slug"]
        for k in ("relationship", "centrality", "form_of_inclusion"):
            if f[k] not in defs[k]:
                errors.append(f"{name}: unknown {k} {f[k]!r}")
        if f["relationship"] == "weaker result" and f["centrality"] == "main result":
            errors.append(f"{name}: a weaker result is never main result (it takes the centrality of the "
                          f"statement it precedes, at most central)")
        if f["in_report"]:
            if not (isinstance(f["id"], str) and ID_RE.fullmatch(f["id"])):
                errors.append(f"{name}: a finding in the report needs an id F1, F2, ...")
            if f["form_of_inclusion"] == "none":
                errors.append(f"{name}: form_of_inclusion is none, so in_report must be false "
                              f"(such findings stay in the JSON only)")
        else:
            if f["id"] is not None:
                errors.append(f"{name}: a finding not in the report has id null")
            if f["form_of_inclusion"] != "none":
                errors.append(f"{name}: in_report is false, so form_of_inclusion must be none")
        claim = f.get("novelty_claim")
        if f["overstated_novelty"] and not (isinstance(claim, str) and claim.strip()):
            errors.append(f"{name}: overstated_novelty is true, so novelty_claim must say where the claim is made")
        if not f["overstated_novelty"] and claim is not None:
            errors.append(f"{name}: novelty_claim is given, but overstated_novelty is false")
        if f["overstated_novelty"] and f["form_of_inclusion"] == "citation":
            errors.append(f"{name}: overstated_novelty is true, so form_of_inclusion cannot be citation (the forms "
                          f"then describe revising the abstract or framing: sentence, paragraph, or none)")
        statuses = []
        for src in f["sources"]:
            k, st = src["key"], src["credit_status"]
            if k not in sources:
                errors.append(f"{name}: unknown source key {k}")
                continue
            if st not in defs["credit_status"]:
                errors.append(f"{name}/{k}: unknown credit_status {st!r} (content credited where it is used, "
                              f"directly or through a cited location that credits it, is not a finding unless "
                              f"its novelty is overstated)")
                continue
            if f["overstated_novelty"] and st not in OVERSTATED_STATUSES:
                errors.append(f"{name}/{k}: overstated_novelty needs the preprint to cite the work for this content "
                              f"(credited, credited_elsewhere or credited_in_part), not {st}; uncited content is "
                              f"an ordinary finding")
            if st == "credited" and not f["overstated_novelty"]:
                errors.append(f"{name}/{k}: credit_status credited is allowed only with overstated_novelty "
                              f"(content credited where it is used is not otherwise a finding)")
            inbib = sources[k]["in_preprint_bibliography"]
            if st == "not_cited" and inbib:
                errors.append(f"{name}/{k}: credit_status not_cited but the work is in the bibliography")
            if st in NEEDS_BIB and not inbib:
                errors.append(f"{name}/{k}: credit_status {st} but the work is not in the bibliography")
            statuses.append(st)
        # The principal source is the first listed; the gap is judged on it alone.
        first = f["sources"][0]
        if first["key"] in sources and first["credit_status"] in defs["credit_status"]:
            gap = (f["relationship"] in GAP_RELATIONSHIPS and f["centrality"] in GAP_CENTRALITY
                   and first["credit_status"] in GAP_STATUSES)
            if f["attribution_gap"] != gap:
                errors.append(f"{name}: attribution_gap is {str(f['attribution_gap']).lower()}, but its definition "
                              f"gives {str(gap).lower()} (relationship {f['relationship']}, centrality "
                              f"{f['centrality']}, principal source {first['key']} {first['credit_status']})")
    rep = [f for f in findings if f["in_report"] and isinstance(f["id"], str) and ID_RE.fullmatch(f["id"])]
    nums = sorted(int(f["id"][1:]) for f in rep)
    if nums != list(range(1, len(nums) + 1)):
        errors.append(f"report ids should run F1..F{len(nums)} without gaps; got "
                      + ", ".join(f"F{n}" for n in nums))
    # Magnitude order: (centrality rank, relationship rank) never decreases from F1 on.
    rep = sorted((f for f in rep if f["centrality"] in CENTRALITY_RANK and f["relationship"] in RELATIONSHIP_RANK),
                 key=lambda f: id_key(f["id"]))
    for a, b in zip(rep, rep[1:]):
        ra = (CENTRALITY_RANK[a["centrality"]], RELATIONSHIP_RANK[a["relationship"]])
        rb = (CENTRALITY_RANK[b["centrality"]], RELATIONSHIP_RANK[b["relationship"]])
        if rb < ra:
            errors.append(f"{b['id']} ({b['centrality']}, {b['relationship']}) comes after {a['id']} "
                          f"({a['centrality']}, {a['relationship']}), against the magnitude order: by centrality "
                          f"(main result, central, supporting, peripheral), then relationship (same result, same "
                          f"technique, adapted, proof shortcut, same route, fragment, weaker result). Reorder the "
                          f"\\input lines, rebuild, and renumber the JSON")
    return errors


def make_stats(data, findings, sources, defs):
    """Counts over the findings in the report, except by_form_of_inclusion, which
    counts every finding (JSON-only findings are its "none" count). JSON-only
    findings are also listed by slug."""
    rep = sorted((f for f in findings if f["in_report"]), key=lambda f: id_key(f["id"]))
    pairs = [(f["id"], s["key"], s["credit_status"]) for f in rep for s in f["sources"]]
    works = {k for _, k, _ in pairs}
    return {
        "format": "math-lineage/precedence-stats",
        "format_version": FORMAT_VERSION,
        "preprint": data["preprint"]["id"],
        "generated_from": "precedence-findings.json",
        "review_date": data["review"]["date"],
        "findings": {
            "in_report": len(rep),
            "json_only": [f["slug"] for f in findings if not f["in_report"]],
            "by_relationship": {r: sum(1 for f in rep if f["relationship"] == r) for r in defs["relationship"]},
            "by_centrality": {c: sum(1 for f in rep if f["centrality"] == c) for c in defs["centrality"]},
            "by_form_of_inclusion": {x: sum(1 for f in findings if f["form_of_inclusion"] == x)
                                     for x in defs["form_of_inclusion"]},
            "attribution_gaps": [f["id"] for f in rep if f["attribution_gap"]],
            "overstated_novelty": [f["id"] for f in rep if f["overstated_novelty"]],
            "ids_by_relationship": {r: [f["id"] for f in rep if f["relationship"] == r]
                                    for r in defs["relationship"] if any(f["relationship"] == r for f in rep)},
        },
        "earlier_works": {
            "distinct": len(works),
            "not_in_preprint_bibliography": sum(1 for k in works if not sources[k]["in_preprint_bibliography"]),
            "in_preprint_bibliography": sum(1 for k in works if sources[k]["in_preprint_bibliography"]),
            "finding_source_pairs_by_credit_status": {st: sum(1 for _, _, s in pairs if s == st)
                                                      for st in defs["credit_status"]},
        },
    }


# ---------------------------------------------------------------- main

def fail(errors):
    print("VALIDATION FAILED")
    print("\n".join(errors))
    sys.exit(1)


def main(argv):
    if len(argv) not in (2, 3) or argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    if not argv[1].strip() or (len(argv) > 2 and not argv[2].strip()):
        print("an argument is empty: give the preprint dir (and the writeup dir)")
        sys.exit(2)
    d = Path(argv[1])
    src = d / "precedence-findings.json"
    out = d / "precedence-stats.json"
    if not src.is_file():
        # Nothing is deleted: this may not be a preprint folder at all.
        fail([f"{src} not found (the first argument must be the preprint folder holding it)"])

    errors = []
    data = load_json(src, errors)
    if data is None:
        fail(errors)
    version = data.get("format_version") if isinstance(data, dict) else None
    if type(version) is int and version == 1:
        fail([f"{src} is in format version 1 (categories A/B/C and grades), "
              f"which is superseded. Update it to version {FORMAT_VERSION}: relationship types, centrality, "
              f"form of inclusion, credit statuses and flags (see references/publish.md and "
              f"assets/precedence-findings.example.json). The write-up's summary table and README need the "
              f"same update."])
    if type(version) is int and version == FORMAT_VERSION:
        # A version 2 file: its old stats go now, and come back only if it validates.
        try:
            out.unlink()
        except FileNotFoundError:
            pass
    check_types(data, errors)
    if errors:
        fail(errors)
    if data["format"] != FORMAT or data["format_version"] != FORMAT_VERSION:
        fail([f"format must be {FORMAT!r}, version {FORMAT_VERSION}"])

    defs = DEFINITIONS
    got = data["definitions"]
    if got != defs:
        diff = []
        for part in sorted(set(defs) | set(got)):
            g = got.get(part)
            if not isinstance(g, dict):
                diff.append(part)
                continue
            want = defs.get(part, {})
            diff += [f"{part}.{k}" for k in sorted(set(want) | set(g)) if want.get(k) != g.get(k)]
        errors.append("definitions differ from the canonical ones (copy them verbatim from "
                      "assets/precedence-findings.example.json): " + ", ".join(diff))
    sources = data["sources"]
    findings = data["findings"]

    for fid, n in Counter(f["id"] for f in findings if f["in_report"] and isinstance(f["id"], str)).items():
        if n > 1:
            errors.append(f"finding id {fid} is used {n} times")
    for slug, n in Counter(f["slug"] for f in findings).items():
        if n > 1:
            errors.append(f"finding slug {slug} is used {n} times")
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

    errors += finding_errors(findings, sources, defs)
    if len(argv) > 2:
        errors += summary_errors(Path(argv[2]), findings)

    if build.is_dir():
        for h in bibliography_hints(build, sources, cited, d):
            print(h)

    if errors:
        fail(errors)

    stats = make_stats(data, findings, sources, defs)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print("validation passed; wrote", out)
    print(json.dumps(stats["findings"]["by_relationship"]),
          "attribution gaps:", json.dumps(stats["findings"]["attribution_gaps"]),
          "overstated novelty:", json.dumps(stats["findings"]["overstated_novelty"]),
          json.dumps(stats["earlier_works"]))


if __name__ == "__main__":
    main(sys.argv)
