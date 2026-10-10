#!/usr/bin/env bash
# Prepare the published deliverables from a passing build.
#
#   bash publish_prep.sh "<writeup dir>" "<preprint dir>" "<scratch flat dir>"
#
# The main file is always <writeup>/precedence-findings.tex. Run build.sh
# first: this script needs build/precedence-findings.pdf and the stamp
# build/precedence-findings.pass that build.sh writes only on "result: PASS",
# holding that PDF's sha256. A PDF from a failed build, or changed since, is
# refused.
#
# The flat dir is created if needed. Only the files this script writes there
# are deleted first (precedence-findings.{tex,pdf,aux,log,out,toc}, pass1-3.log,
# orig.txt, flat.txt); nothing else in it is touched. It must not be, or
# contain, the writeup or preprint dir, nor lie inside the preprint dir, nor be
# /, $HOME or the repository root.
#
# Steps, stopping at the first failure:
#  1. flatten the main file (flatten_tex.py) into <flat dir>/precedence-findings.tex;
#  2. the lint tex_gate.py on the flat file's body (after \begin{document});
#  3. check that TeX can be confined (sandbox_check, tex_sandbox.sh), compile
#     the flat file there with three pdflatex passes confined to the flat dir
#     (sandbox_pdflatex), check every object of both PDFs (pdf_check.py), and
#     compare pdftotext -layout of both PDFs (they must be identical);
#  4. fail if the flat .tex or the PDF text contains a local path (C:/Users,
#     /Users/, /home/, AppData, scratchpad) or an email address;
#  5. print comment lines of the flat file that look like working notes (for
#     review; not removed, and not a failure);
#  6. validate the JSON and write the stats (precedence_stats.py <preprint dir>
#     <writeup dir>), before anything is copied into the preprint folder;
#  7. copy the PDF to <writeup>/precedence-findings.pdf and <preprint dir>, and
#     the flat .tex to <preprint dir>.
#
# Exit status 0 only if every step succeeds; it prints "result: PASS" or
# "result: FAIL (<step>)". Bad arguments exit 2 before anything is written.
set -uo pipefail
usage() {
  echo "usage: $0 <writeup dir> <preprint dir> <scratch flat dir>" >&2
  [ -n "${1:-}" ] && echo "$1" >&2
  exit 2
}
[ $# -eq 3 ] || usage "expected 3 arguments, got $#"
[ -n "$1" ] && [ -n "$2" ] && [ -n "$3" ] || usage "an argument is empty"
here=$(CDPATH= cd "$(dirname "$0")" && pwd) || usage "cannot find the script's folder"
writeup=$(CDPATH= cd "$1" 2>/dev/null && pwd) || usage "not a directory: $1"
preprint=$(CDPATH= cd "$2" 2>/dev/null && pwd) || usage "not a directory: $2"
flat=$3
main=precedence-findings.tex
base=precedence-findings
[ -f "$writeup/$main" ] || usage "no $writeup/$main: the first argument must be the writeup dir"
fail() { echo "result: FAIL ($1)"; exit 1; }

py=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 &&
     "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    py=$c
    break
  fi
done
[ -n "$py" ] || fail "python3 (3.9 or later) not found"
for f in flatten_tex.py tex_gate.py tex_sandbox.sh pdf_check.py precedence_stats.py; do
  [ -f "$here/$f" ] || fail "missing $here/$f"
done

# sha256 <file>: the file's sha256 in hex, without a line end.
sha256() {
  "$py" -I -c 'import hashlib, sys; sys.stdout.write(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$1"
}
built="$writeup/build/$base.pdf"
stamp="$writeup/build/$base.pass"
[ -f "$built" ] || fail "no $built; run build.sh first"
[ -f "$stamp" ] || fail "no $stamp: the last build.sh run did not pass; fix it and rebuild"
want=$(tr -d ' \t\r\n' < "$stamp")
got=$(sha256 "$built") || fail "cannot hash $built"
[ -n "$want" ] && [ "$want" = "$got" ] || fail "$built is not the PDF of the last passing build; run build.sh again"

# The flat dir: never the writeup, the preprint folder, a folder holding
# either, a folder inside the preprint folder, /, $HOME or the repository root.
repo=$(CDPATH= cd "$here/../../../.." 2>/dev/null && pwd) || repo=""
top=$(git -C "$preprint" rev-parse --show-toplevel 2>/dev/null) || top=""
mkdir -p "$flat" || fail "cannot create $flat"
flat=$(CDPATH= cd "$flat" && pwd) || fail "cannot enter $flat"
# (Checked here too: Git Bash hands "/" to Windows programs as its install folder.)
[ "$flat" != / ] || fail "unsafe flat dir /"
"$py" -I - "$flat" "$writeup" "$preprint" "${HOME:-}" "$repo" "$top" <<'PY' || fail "unsafe flat dir $flat"
import os
import sys

flat, writeup, preprint, *roots = sys.argv[1:]


def same(a, b):
    try:
        return bool(a) and bool(b) and os.path.samefile(a, b)
    except OSError:
        return False


def chain(p):
    """p and each of its parents."""
    p = os.path.abspath(p)
    while True:
        yield p
        q = os.path.dirname(p)
        if q == p:
            return
        p = q


why = ""
if os.path.dirname(os.path.abspath(flat)) == os.path.abspath(flat):
    why = "it is a filesystem root"
elif any(same(flat, r) for r in roots):
    why = "it is $HOME or the repository root"
elif any(same(p, flat) for d in (writeup, preprint) for p in chain(d)):
    why = "it is, or contains, the writeup or the preprint folder"
elif any(same(p, preprint) for p in chain(flat)):
    why = "it is inside the preprint folder"
if why:
    sys.stderr.write("refusing the flat dir %s: %s; give an empty scratch folder\n" % (flat, why))
    sys.exit(1)
PY
( cd "$flat" &&
  rm -f "$base.tex" "$base.pdf" "$base.aux" "$base.log" "$base.out" "$base.toc" \
        pass1.log pass2.log pass3.log orig.txt flat.txt ) || fail "cannot clean $flat"

"$py" -I -X utf8 "$here/flatten_tex.py" "$writeup/$main" "$flat/$base.tex" || fail "flatten"
"$py" -I -X utf8 "$here/tex_gate.py" --body "$flat/$base.tex" || fail "tex gate: the commands above are not allowed in the write-up"

# pdflatex runs confined to the flat dir (tex_sandbox.sh), from inside it with
# a relative name (MSYS path rewriting).
. "$here/tex_sandbox.sh"
sandbox_check || fail "sandbox"
( cd "$flat" &&
  for i in 1 2 3; do
    sandbox_pdflatex -interaction=nonstopmode -halt-on-error "$base.tex" > "pass$i.log" 2>&1 || exit 1
  done ) || fail "flat compile (see $flat/pass*.log)"
"$py" -I -X utf8 "$here/pdf_check.py" "$built" "$flat/$base.pdf" ||
  fail "pdf check: a PDF holds more than text, internal links and web links"

pdftotext -layout "$built" "$flat/orig.txt" || fail "pdftotext of the build"
pdftotext -layout "$flat/$base.pdf" "$flat/flat.txt" || fail "pdftotext of the flat PDF"
diff -q "$flat/orig.txt" "$flat/flat.txt" >/dev/null || fail "flat PDF text differs from the build; compare $flat/orig.txt and $flat/flat.txt"
echo "flat text identical"

# Local paths and email addresses must not be published, in comments or text.
leaks=$(cd "$flat" &&
  grep -n -E '[A-Za-z]:[/\\][Uu]sers|/Users/|/home/|[Aa]pp[Dd]ata|[Ss]cratchpad|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' \
    "$base.tex" flat.txt | cut -c1-200)
if [ -n "$leaks" ]; then
  printf '%s\n' "$leaks" | head -20
  fail "local path or email address in the flat .tex or the PDF text (above); remove it from the source and rebuild"
fi
echo "no local paths or email addresses"

echo "comment lines that may be working notes (remove any that are):"
grep -n -i -E '(^|[^\\])%.*(paywall|not read|not verified|todo|fixme|agent|coordinator|subagent|garbled|saved as|author copy)' \
  "$flat/$base.tex" | cut -c1-200 || echo "  none"

"$py" -I -X utf8 "$here/precedence_stats.py" "$preprint" "$writeup" || fail "JSON validation"

cp "$built" "$writeup/precedence-findings.pdf" || fail "copy PDF to the writeup"
cp "$built" "$preprint/precedence-findings.pdf" || fail "copy PDF to the preprint folder"
cp "$flat/$base.tex" "$preprint/precedence-findings.tex" || fail "copy flat .tex"
echo "copied the PDF and the flat .tex to $preprint"
echo "result: PASS"
