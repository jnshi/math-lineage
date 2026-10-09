"""Print each finding's ID, slug, title and Summary paragraph, in document order.

Usage: python3 -I -X utf8 print_summaries.py <writeup dir> [<main .tex>]
  (the main file defaults to precedence-findings.tex)

Fragments are read in the order of the main file's \\input{findings/<slug>} lines
(commented-out lines are skipped). Each fragment opens with
\\finding[<short title>]{<title>}{<slug>}. IDs (F1, F2, ...) are assigned by
LaTeX, so they are read from build/<main>.aux, which build.sh writes: build
first. Without the aux, or for a fragment it doesn't know, the ID is "?" and a
warning is printed. Useful for drafting the summary table,
precedence-findings.json and the README.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(2)
writeup = sys.argv[1]
main = sys.argv[2] if len(sys.argv) > 2 else "precedence-findings.tex"
COMMENT = re.compile(r"(?m)(?<!\\)%.*$")


def read(path):
    with io.open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def group(text, i, closing):
    """text[i] opens a group closed by `closing` ("}" or "]"); return (contents,
    index after the closing character). Braces nest, a "]" inside braces does not
    close, and escaped characters (\\{, \\}, \\]) are skipped."""
    depth, j = 0, i + 1
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            if depth == 0 and closing == "}":
                return text[i + 1:j], j + 1
            depth -= 1
        elif c == closing and depth == 0:
            return text[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced group")


def parse_finding(text):
    """Return (short, title, slug) of the first \\finding[...]{...}{...}, or None."""
    m = re.search(r"\\finding(?![A-Za-z@])\s*", text)
    if not m:
        return None
    i, short = m.end(), ""
    if text[i:i + 1] == "[":
        short, i = group(text, i, "]")
    args = []
    for _ in range(2):
        while i < len(text) and text[i].isspace():
            i += 1
        if text[i:i + 1] != "{":
            return None
        arg, i = group(text, i, "}")
        args.append(arg)
    return short, args[0], args[1].strip()


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


main_path = os.path.join(writeup, main)
main_text = COMMENT.sub("", read(main_path))
slugs = [m.group(1) or m.group(2) for m in
         re.finditer(r"\\input\s*\{\s*(?:\./)?findings/([^}]+?)\s*\}|\\fragment\s*\{\s*([^}]+?)\s*\}", main_text)]
slugs = [s[:-4] if s.endswith(".tex") else s for s in slugs]

aux = os.path.join(writeup, "build", os.path.splitext(main)[0] + ".aux")
ids = {}
if os.path.isfile(aux):
    for m in re.finditer(r"\\newlabel\{f:([^}]*)\}\{\{([^{}]*)\}", read(aux)):
        ids[m.group(1)] = m.group(2)
    newer = [p for p in [main_path] + [os.path.join(writeup, "findings", s + ".tex") for s in slugs]
             if os.path.isfile(p) and os.path.getmtime(p) > os.path.getmtime(aux)]
    if newer:
        print(f"warning: {aux} is older than {len(newer)} source file(s), e.g. "
              f"{os.path.relpath(newer[0], writeup)}; rebuild if findings were added, removed or reordered")
else:
    print(f"warning: {aux} not found; IDs print as '?' (run build.sh first)")

for slug in slugs:
    path = os.path.join(writeup, "findings", slug + ".tex")
    if not os.path.isfile(path):
        print("=" * 10, "? ", slug, "(no file findings/" + slug + ".tex)")
        continue
    text = COMMENT.sub("", read(path))
    parsed = parse_finding(text)
    if parsed is None:
        print("=" * 10, "? ", slug, "(no \\finding{<title>}{<slug>} line)")
        continue
    short, title, label = parsed
    fid = ids.get(label, "?")
    if ids and label not in ids:
        print(f"warning: f:{label} is not in the aux; rebuild")
    if label != slug:
        print(f"warning: findings/{slug}.tex has \\finding slug {label!r}; use the file name")
    print("=" * 10, fid, " ", slug)
    print("TITLE:", squash(title))
    if short:
        print("SHORT TITLE:", squash(short))
    summ = re.search(r"\\paragraph\{Summary\.\}(.*?)(?=\\paragraph\{|\\finding(?![A-Za-z@])|\\subsection|\Z)", text, re.S)
    print(squash(summ.group(1)) if summ else "?")
