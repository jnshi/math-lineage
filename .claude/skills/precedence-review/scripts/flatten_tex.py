"""Inline every \\input{...} of a LaTeX main file into one self-contained file.

Usage: python -I -X utf8 flatten_tex.py <main.tex> <out.tex>

Paths in \\input are resolved relative to the main file's directory. Lines of the
form "% BIB <Key>: ..." (inputs to make_bib.py) are dropped, since the generated
bibliography is inlined. Other comments are kept, so check them for working
notes before publishing. Compile the result from a clean directory with three
pdflatex passes and diff its pdftotext output against the original build.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

INPUT_RE = re.compile(r"^(\s*)\\input\{([^}]+)\}\s*$")


def expand(path, root, depth=0):
    if depth > 5:
        raise RuntimeError(f"input nesting too deep at {path}")
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = INPUT_RE.match(line)
        if m and not line.lstrip().startswith("%"):
            name = m.group(2)
            child = root / (name if name.endswith(".tex") else name + ".tex")
            out.extend(expand(child, root, depth + 1))
        else:
            out.append(line)
    return out


main = Path(sys.argv[1])
dest = Path(sys.argv[2])
lines = [l for l in expand(main, main.parent) if not re.match(r"\s*%\s*BIB\s", l)]
text = "\n".join(lines) + "\n"
if "\\input{" in text:
    sys.exit("an \\input remains unexpanded (inline or commented form?); check the main file")
dest.parent.mkdir(parents=True, exist_ok=True)
# open() rather than Path.write_text(newline=...), which needs Python 3.10.
with open(dest, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print(f"wrote {dest} ({len(lines)} lines)")
