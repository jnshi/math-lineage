#!/usr/bin/env bash
# Test-compile one write-up fragment against the shared preamble, then check
# the PDF text for strings that must never reach the reader.
#
#   bash fragment_test.sh <preamble.tex> <fragment.tex> <scratch dir>
#
# The scratch dir is created (use your own subfolder; never the writeup folder).
# Files are copied in and pdflatex runs there with relative names, which avoids
# Windows/MSYS path mangling. Undefined citations and references are expected
# in this standalone test; fix every "!" error and any overfull box over 10pt.
set -uo pipefail
if [ $# -ne 3 ]; then
  echo "usage: $0 <preamble.tex> <fragment.tex> <scratch dir>" >&2
  exit 2
fi
preamble=$1
fragment=$2
dir=$3
mkdir -p "$dir" || exit 1
cp "$preamble" "$dir/preamble.tex" || exit 1
cp "$fragment" "$dir/fragment.tex" || exit 1
cd "$dir" || exit 1
rm -f test.aux test.out test.toc
printf '%s\n' '\documentclass[11pt]{article}' '\input{preamble}' '\begin{document}' \
  '\section{Test}\label{sec:overview}\label{sec:about}' '\input{fragment}' '\end{document}' > test.tex
pdflatex -interaction=nonstopmode test.tex > pass1.log 2>&1
pdflatex -interaction=nonstopmode test.tex > pass2.log 2>&1
echo "--- errors:"
grep -n '^!' test.log | head -20
echo "--- overfull boxes (fix any over 10pt):"
grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' test.log | sort | uniq -c
echo "--- output:"
grep 'Output written' test.log || echo "NO PDF PRODUCED"
if [ -f test.pdf ]; then
  pdfinfo test.pdf 2>/dev/null | grep Pages
  pdftotext -enc UTF-8 test.pdf test.txt
  echo "--- forbidden strings in the PDF text (expect none):"
  grep -n -i -E '\.tex\b|tex:|\b(prof|cap|sec|eq|lem|thm):[a-z]|citation status|caveat|not verified|consulted|regrad|skeptic|subagent|coordinator|the library|case-insensitive|\bTable [0-9]' test.txt | head -20
fi
true
