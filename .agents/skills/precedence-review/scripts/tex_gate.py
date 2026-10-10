"""Lint: flag write-up LaTeX that reads or writes files, runs code, or redefines macros.

Usage: python3 -I -X utf8 tex_gate.py [--main | --body] <file.tex> ...

The write-up's fragments are written by agents that read untrusted sources, and
the PDF compiled from them is published. They need only the macros of
parts/preamble.tex, so this lint fails on commands that pull a file into the
PDF, write a file, run code, add PDF actions or links to other schemes, or
build such a command indirectly. build.sh, fragment_test.sh and
publish_prep.sh run it before compiling, and a hit fails them, with an error an
agent can act on.

It is a list of known commands in a language that can build command names as it
runs, so it cannot be complete, and it is not what keeps the published PDF safe.
That is the sandbox (tex_sandbox.sh: TeX cannot read or write outside its folder
or run programs) and pdf_check.py (the PDF holds only internal and web links).

Comments are stripped first: a % after an even number of backslashes (none,
\\\\, ...) starts one, and, as in TeX, it also removes the line end and the next
line's leading spaces. A command counts only where its backslash is not itself
escaped. Each of these commands, followed by a non-letter, is a hit:
  \\input \\include \\InputIfFileExists \\IfFileExists \\@@input \\openin \\read
  \\readline \\openout \\write \\immediate \\special
  \\pdfcatalog \\pdfobj \\pdfannot \\pdfinfo \\pdfnames \\pdfstartlink \\pdfliteral
  \\pdfpageattr \\pdfpagesattr \\pdfpageresources \\pdftrailer \\pdfoutline
  \\pdffiledump \\pdfximage \\pdfmdfivesum \\pdffilesize \\pdffilemoddate
  \\pdfmapfile \\pdfmapline \\pdfprimitive \\primitive \\directlua
  \\catcode \\csname \\ifcsname \\begincsname \\lastnamedcs \\scantokens
  \\UseName \\UseExpandableName \\ExpandArgs
  \\def \\edef \\gdef \\xdef \\let \\newcommand \\renewcommand \\providecommand
  \\urldef \\DeclareUrlCommand
  \\usepackage \\RequirePackage \\makeatletter \\hypersetup \\hyperbaseurl
  \\ExplSyntaxOn \\ExplSyntaxOff \\ProvidesExplPackage \\ProvidesExplClass
  \\ProvidesExplFile
  \\Acrobatmenu \\hyperimage \\PushButton \\TextField \\CheckBox \\ChoiceMenu
  \\Submit \\Reset
So is the ^^ notation (^^5c is a backslash). Allowlists cover the rest:
  - \\begin{<name>} and \\end{<name>} need a name from ENVIRONMENTS below
    (with or without a trailing *): \\begin{X} runs the command \\X.
  - \\href and \\url (after an optional [...]) need {, optional spaces, then
    http:// or https://, literally.
  - \\hyperref needs the [<label>] form (its four-argument form is a URL link).

--main  for the main file: lines that are exactly \\input{parts/<name>} or
        \\input{findings/<name>} are allowed, with <name> made of A-Z a-z 0-9
        . _ - (not starting with a dot). Everything else is checked as above.
--body  checks only the text after \\begin{document} (for the flattened file,
        whose preamble is parts/preamble.tex).

Prints "<file>:<line>: <token>" for each hit. Exit status 0 if there is none,
1 if there is a hit, 2 on bad usage or an unreadable file.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

WORDS = (
    # reading and writing files, running code
    "input include InputIfFileExists IfFileExists @@input openin read readline openout write immediate special "
    # raw PDF objects, actions, file access and primitives
    "pdfcatalog pdfobj pdfannot pdfinfo pdfnames pdfstartlink pdfliteral pdfpageattr pdfpagesattr "
    "pdfpageresources pdftrailer pdfoutline pdffiledump pdfximage pdfmdfivesum pdffilesize pdffilemoddate "
    "pdfmapfile pdfmapline pdfprimitive primitive directlua "
    # building a command from its name
    "catcode csname ifcsname begincsname lastnamedcs scantokens UseName UseExpandableName ExpandArgs "
    # defining commands
    "def edef gdef xdef let newcommand renewcommand providecommand urldef DeclareUrlCommand "
    # packages, internals and expl3 syntax
    "usepackage RequirePackage makeatletter hypersetup hyperbaseurl "
    "ExplSyntaxOn ExplSyntaxOff ProvidesExplPackage ProvidesExplClass ProvidesExplFile "
    # hyperref actions, images and form fields (JavaScript)
    "Acrobatmenu hyperimage PushButton TextField CheckBox ChoiceMenu Submit Reset"
).split()
ENVIRONMENTS = set(
    "itemize enumerate description center flushleft flushright quote quotation minipage tabular tabularx "
    "xltabular longtable table array equation align gather multline split aligned gathered alignedat cases "
    "matrix pmatrix bmatrix Bmatrix vmatrix Vmatrix smallmatrix proof document thebibliography".split())
# A control word starts at a backslash that is not itself escaped (preceded by
# an even number of backslashes): "\\input" is a line break and the word "input".
ESC = r"(?<!\\)(?:\\\\)*"
TOKEN = re.compile(ESC + r"\\(" + "|".join(re.escape(w) for w in sorted(WORDS, key=len, reverse=True))
                   + r")(?![A-Za-z])")
ENV = re.compile(ESC + r"\\(begin|end)(?![A-Za-z])")
ENV_NAME = re.compile(r"\s*\{\s*([A-Za-z]+)(\*?)\s*\}")
LINK = re.compile(ESC + r"\\(href|url)(?![A-Za-z])")
LINK_OK = re.compile(r"\s*(?:\[[^\]]*\]\s*)?\{\s*https?://", re.I)
HYPERREF = re.compile(ESC + r"\\(hyperref)(?![A-Za-z])")
HYPERREF_OK = re.compile(r"\s*\[")
CARET = re.compile(r"(\^)\^")
COMMENT = re.compile(r"(?<!\\)((?:\\\\)*)%.*")
MAIN_INPUT = re.compile(r"\\input\{(?:parts|findings)/[A-Za-z0-9_-][A-Za-z0-9._-]*\}")
BEGIN_DOC = re.compile(ESC + r"\\begin\s*\{document\}")


def strip(lines):
    """Comment-free text, and the source line number of each of its characters."""
    text, where, joined = [], [], False
    for no, line in enumerate(lines, 1):
        if joined:  # the previous line ended in a comment: TeX skips this line's leading spaces
            line = line.lstrip(" \t")
        m = COMMENT.search(line)
        joined = m is not None
        body = line[:m.start()] + m.group(1) if m else line + "\n"
        text.append(body)
        where.extend([no] * len(body))
    return "".join(text), where


def after(text, i, n=24):
    """What follows position i, for the report: up to n characters of one line."""
    return text[i:i + n].split("\n")[0].strip()


def hits(path, mode):
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if mode == "--main":
        # Blank out the allowed \input lines (keeping the line count).
        lines = ["" if MAIN_INPUT.fullmatch(COMMENT.sub(r"\1", l).strip()) else l for l in lines]
    text, where = strip(lines)
    start = 0
    if mode == "--body":
        m = BEGIN_DOC.search(text)
        if not m:
            return [(1, "no \\begin{document}")]
        start = m.end()
    out = []

    def hit(m, tok):
        # Group 1 starts at the token itself, after any escaped backslashes.
        out.append((where[m.start(1)], tok))

    for m in TOKEN.finditer(text, start):
        hit(m, "\\" + m.group(1))
    for m in CARET.finditer(text, start):
        hit(m, "^^")
    for m in ENV.finditer(text, start):
        n = ENV_NAME.match(text, m.end())
        if not (n and n.group(1) in ENVIRONMENTS):
            hit(m, f"\\{m.group(1)}{{{n.group(1) + n.group(2)}}}" if n
                else f"\\{m.group(1)} {after(text, m.end())} (not an allowed environment)")
    for m in LINK.finditer(text, start):
        if not LINK_OK.match(text, m.end()):
            hit(m, f"\\{m.group(1)} {after(text, m.end())} (only http:// or https:// links)")
    for m in HYPERREF.finditer(text, start):
        if not HYPERREF_OK.match(text, m.end()):
            hit(m, f"\\hyperref {after(text, m.end())} (only \\hyperref[<label>]{{...}})")
    return sorted(set(out))


def main(argv):
    mode = None
    args = argv[1:]
    if args and args[0] in ("--main", "--body"):
        mode, args = args[0], args[1:]
    if not args or any(a.startswith("-") for a in args):
        print(__doc__)
        return 2
    bad = 0
    for path in args:
        try:
            found = hits(path, mode)
        except OSError as e:
            print(f"{path}: cannot read: {e}")
            return 2
        for line, tok in found:
            print(f"{path}:{line}: {tok}")
        bad += len(found)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
