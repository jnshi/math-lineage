"""Build <writeup>/parts/bibliography.tex from the citations the write-up uses.

Usage: python -I -X utf8 make_bib.py <writeup dir> <prior-work/INDEX.md> [<main .tex>]

Keys are collected from \\cite{...} and \\sloc{Key}{...} in reading order: the
main file's \\input / \\fragment lines if it is given, otherwise every .tex in
findings/ and parts/. Each key is resolved from, in order:
  1. a comment line "% BIB <Key>: <full citation>" in any document file
     (use this for the preprint and its companions, OAI-..., and for works
     outside the library, NL-...);
  2. the "## Downloaded papers" table of prior-work/INDEX.md
     (columns: Key | Citation | arXiv / DOI | ...).
Parenthetical working notes ("(author copy from ...)", "(not read)", ...) are
stripped. Unresolved keys are printed and rendered as a bold placeholder.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

writeup, index_path = sys.argv[1], sys.argv[2]
main_file = sys.argv[3] if len(sys.argv) > 3 else None

# Parenthetical working notes to drop from citations. Extend the trigger words
# when a new kind of note slips through.
NOTE_RE = re.compile(
    r"\s*\((?=[^()]*(verified|version used|not read|consulted|checked|library|paywalled|as listed|"
    r"as cited|author copy|journal data|saved as|publisher PDF|text extraction|garbled))[^()]*\)",
    re.I,
)

UNICODE = {
    "\u2013": "--", "\u2014": "---", "\u2018": "`", "\u2019": "'", "\u201c": "``", "\u201d": "''",
    "\u2264": "$\\le$", "\u2265": "$\\ge$", "\u2016": "$\\|$", "\u2026": "\\dots{}", "\u00a0": "~",
    "\u03b1": "$\\alpha$", "\u03b2": "$\\beta$", "\u03b3": "$\\gamma$", "\u03bb": "$\\lambda$",
    "\u2212": "-", "\u00d7": "$\\times$", "\u2202": "$\\partial$",
}


def tex_escape(s):
    s = re.sub(r"([&%#_$])", r"\\\1", s)
    s = s.replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")
    for u, t in UNICODE.items():
        s = s.replace(u, t)
    return s


def document_files():
    """Document files in reading order."""
    skip = ("preamble", "bibliography")
    if main_file:
        text = io.open(os.path.join(writeup, main_file), encoding="utf-8").read()
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        paths = []
        for m in re.finditer(r"\\input\{([^}]+)\}|\\fragment\{([^}]+)\}", text):
            rel = m.group(1) or ("findings/" + m.group(2))
            stem = rel[:-4] if rel.endswith(".tex") else rel
            if stem.endswith(skip):
                continue
            p = os.path.join(writeup, rel if rel.endswith(".tex") else rel + ".tex")
            if os.path.isfile(p):
                paths.append(p)
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
        text = io.open(path, encoding="utf-8").read()
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


def index_table():
    rows, in_table = {}, False
    for line in io.open(index_path, encoding="utf-8"):
        if line.startswith("## "):
            in_table = line.startswith("## Downloaded papers")
            continue
        if in_table and line.startswith("| ") and not line.startswith("| Key") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if len(cells) >= 3:
                rows[cells[0].strip("`")] = (cells[1], cells[2])
    return rows


keys, explicit = used_keys()
rows = index_table()
missing, items = [], []
for k in keys:
    if k in explicit:
        cit = NOTE_RE.sub("", explicit[k])
        # Explicit entries may already be TeX (e.g. \emph{...}); escape only if they look like plain text.
        items.append((k, cit if "\\" in cit else tex_escape(cit)))
    elif k in rows:
        cit, ids = rows[k]
        cit = NOTE_RE.sub("", cit).rstrip(" .")
        items.append((k, tex_escape(cit) + ". " + tex_escape(ids) + "."))
    else:
        missing.append(k)
        items.append((k, "\\textbf{[missing bibliography entry for key " + tex_escape(k) + "]}"))

out = ["\\begin{thebibliography}{99}", "\\small"]
out += ["\\bibitem{%s} %s" % (k, text) for k, text in items]
out.append("\\end{thebibliography}")
with io.open(os.path.join(writeup, "parts", "bibliography.tex"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(out) + "\n")
print("keys:", len(keys), "missing:", missing)
