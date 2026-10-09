"""Inline every \\input{...} of a LaTeX main file into one self-contained file.

Usage: python -I -X utf8 flatten_tex.py <main.tex> <out.tex>

Only lines that consist of \\input{<name>} are inlined. Paths are resolved
relative to the main file's directory, and a target outside that directory
(after resolving "..", links and absolute paths) is refused. After each
inlined file a line "\\space%" stands in for the end-of-line space that
followed \\input{...} in the parent, so a paragraph that continues across the
boundary is set exactly as in the input-based build.

Lines of the form "% BIB <Key>: ..." (inputs to make_bib.py) are dropped, since
the generated bibliography is inlined. Other comments are kept, so check them
for working notes before publishing. The script fails if any \\input,
\\include or \\@@input remains outside comments, or any "\\input{" remains at
all. Compile the result from a clean directory with three pdflatex passes and
diff its pdftotext output against the original build.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

INPUT_RE = re.compile(r"^(\s*)\\input\{([^}]+)\}\s*$")
COMMENT = re.compile(r"(?<!\\)((?:\\\\)*)%.*")
LEFT = re.compile(r"(?<!\\)(?:\\\\)*\\(input|include|@@input)(?![A-Za-z])")


def expand(path, root, depth=0):
    if depth > 5:
        sys.exit(f"input nesting too deep at {path}")
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = INPUT_RE.match(line)
        if m and not line.lstrip().startswith("%"):
            name = m.group(2).strip()
            child = root / (name if name.endswith(".tex") else name + ".tex")
            real = child.resolve()
            try:
                real.relative_to(root.resolve())
            except ValueError:
                sys.exit(f"refused: \\input{{{name}}} in {path.name} resolves to {real}, "
                         f"outside {root.resolve()}")
            if not real.is_file():
                sys.exit(f"\\input{{{name}}} in {path.name}: no file {child}")
            out.extend(expand(real, root, depth + 1))
            out.append("\\space%")
        else:
            out.append(line)
    return out


main = Path(sys.argv[1])
dest = Path(sys.argv[2])
lines = [l for l in expand(main, main.parent) if not re.match(r"\s*%\s*BIB\s", l)]
text = "\n".join(lines) + "\n"
left = sorted({"\\" + m.group(1) for l in lines for m in LEFT.finditer(COMMENT.sub(r"\1", l))})
if left:
    sys.exit(f"{', '.join(left)} remains after inlining (inline, primitive or nested form?); "
             f"only lines that are exactly \\input{{...}} are inlined")
if "\\input{" in text:
    sys.exit("an \\input remains unexpanded (inline or commented form?); check the main file")
dest.parent.mkdir(parents=True, exist_ok=True)
# open() rather than Path.write_text(newline=...), which needs Python 3.10.
with open(dest, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print(f"wrote {dest} ({len(lines)} lines)")
