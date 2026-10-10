#!/usr/bin/env bash
# Test-compile one write-up fragment against the shared preamble, then check
# the PDF text for strings that must never reach the reader.
#
#   bash fragment_test.sh <preamble.tex> <fragment.tex> <scratch dir>
#
# The fragment first goes through the lint tex_gate.py (next to this script):
# a command the write-up has no use for (reading or writing files, running
# code, defining macros) fails the test before anything is compiled. The
# scratch dir is created (use your own subfolder; never the writeup folder).
# Files are copied in and pdflatex runs there, confined to that folder
# (tex_sandbox.sh), with relative names, which avoids Windows/MSYS path
# mangling. The PDF goes through pdf_check.py. Outputs of an earlier run in
# the same folder are deleted first. Undefined citations and references are
# expected in this standalone test and are not checked.
#
# Exit status 0 only if: no lint hit, the sandbox check passes, no "!" errors,
# a PDF was produced and passes pdf_check.py, no overfull box over 10pt, and no
# hit from forbidden-patterns.txt (next to this script). Hits from
# warning-patterns.txt are printed for review but do not fail the test.
set -uo pipefail
if [ $# -ne 3 ]; then
  echo "usage: $0 <preamble.tex> <fragment.tex> <scratch dir>" >&2
  exit 2
fi
here=$(CDPATH= cd "$(dirname "$0")" && pwd)
for f in forbidden-patterns.txt warning-patterns.txt tex_gate.py tex_sandbox.sh pdf_check.py; do
  if [ ! -f "$here/$f" ]; then
    echo "missing $here/$f" >&2
    exit 2
  fi
done
preamble=$1
fragment=$2
dir=$3
py=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 &&
     "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    py=$c
    break
  fi
done
if [ -z "$py" ]; then
  echo "python3 (3.9 or later) not found" >&2
  exit 1
fi
echo "--- source gate:"
if ! "$py" -I -X utf8 "$here/tex_gate.py" "$fragment"; then
  echo "the commands above are not allowed in a fragment (only the macros of parts/preamble.tex)"
  echo "--- result: FAIL (tex-gate)"
  exit 1
fi
mkdir -p "$dir" || exit 1
cp "$preamble" "$dir/preamble.tex" || exit 1
cp "$fragment" "$dir/fragment.tex" || exit 1
# Pattern files without comments, blank lines, CRs or build-only patterns.
for tier in forbidden warning; do
  tr -d '\r' < "$here/$tier-patterns.txt" | sed -e '/^#/d' -e '/^[[:space:]]*$/d' -e '/^@build /d' > "$dir/$tier.pat" || exit 1
done
cd "$dir" || exit 1
rm -f test.aux test.out test.toc test.log test.pdf test.txt pass1.log pass2.log

# pattern_hits <text file> <pattern file>: print "p.<page>: <match>" for each
# match. Each page (pages end at \f) is joined into one line, once keeping and
# once removing line-end hyphens, so strings broken across lines still match.
pattern_hits() {
  local mode
  for mode in keep join; do
    awk -v mode="$mode" '
      function emit(s) {
        if (s ~ /-$/) { if (mode == "join") sub(/-$/, "", s); printf "%s", s }
        else if (s != "") printf "%s ", s
      }
      {
        line = $0
        while ((i = index(line, "\f")) > 0) {
          emit(substr(line, 1, i - 1)); printf "\n"; line = substr(line, i + 1)
        }
        emit(line)
      }
      END { printf "\n" }' "$1" | grep -n -o -i -E -f "$2"
  done | sed 's/^\([0-9]*\):[[:space:](]*/p.\1: /' | awk '!seen[$0]++'
}

printf '%s\n' '\documentclass[11pt]{article}' '\input{preamble}' '\begin{document}' \
  '\section{Test}\label{sec:overview}\label{sec:about}' '\input{fragment}' '\end{document}' > test.tex
. "$here/tex_sandbox.sh"
if ! sandbox_check; then
  echo "--- result: FAIL (sandbox)"
  exit 1
fi
sandbox_pdflatex -interaction=nonstopmode test.tex > pass1.log 2>&1
[ $? = 124 ] || sandbox_pdflatex -interaction=nonstopmode test.tex > pass2.log 2>&1
fail=""

echo "--- errors:"
if [ ! -f test.log ]; then
  echo "no test.log: pdflatex did not run (see pass2.log):"
  head -5 pass2.log
  fail="$fail no-log"
else
  grep -n '^!' test.log | head -20
  if grep -q '^!' test.log; then
    fail="$fail errors"
  fi
  echo "--- overfull boxes (fix any over 10pt):"
  grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' test.log | sort | uniq -c
  big=$(grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' test.log | sed 's/^[^(]*(\([0-9.]*\)pt.*$/\1/' | awk '$1 + 0 > 10' | wc -l | tr -d ' ')
  if [ "$big" -gt 0 ]; then
    echo "$big over 10pt"
    fail="$fail overfull"
  fi
fi

echo "--- output:"
if [ -f test.pdf ]; then
  grep 'Output written' test.log
  pdfinfo test.pdf 2>/dev/null | grep Pages
  echo "--- PDF objects (only internal and web links allowed):"
  if ! "$py" -I -X utf8 "$here/pdf_check.py" test.pdf; then
    fail="$fail pdf-check"
  fi
  if pdftotext -enc UTF-8 test.pdf test.txt; then
    echo "--- forbidden strings in the PDF text (expect none):"
    hits=$(pattern_hits test.txt forbidden.pat)
    if [ -n "$hits" ]; then
      printf '%s\n' "$hits" | head -40
      fail="$fail forbidden-strings"
    fi
    echo "--- warnings: check each and remove it unless it is legitimate:"
    pattern_hits test.txt warning.pat | head -40
    # Source check: \ploc{((5.27), p.~39)} prints doubled parentheses.
    grep -n -F '\ploc{((' fragment.tex | cut -c1-160 | sed 's/^/doubled parentheses in \\ploc, line /'
  else
    echo "pdftotext failed"
    fail="$fail pdftotext"
  fi
else
  echo "NO PDF PRODUCED"
  fail="$fail no-pdf"
fi

if [ -n "$fail" ]; then
  echo "--- result: FAIL ($(echo $fail))"
  exit 1
fi
echo "--- result: PASS"
