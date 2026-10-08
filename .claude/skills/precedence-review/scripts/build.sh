#!/usr/bin/env bash
# Build the write-up PDF and print the QA summary.
#
#   bash build.sh <writeup dir> <prior-work/INDEX.md> [main .tex, default precedence-findings.tex]
#
# Steps: regenerate parts/bibliography.tex (make_bib.py, next to this script);
# run pdflatex three times into <writeup>/build (from a clean build/ the table of
# contents settles only on the third pass); dump the PDF text to build/full.txt;
# report errors, undefined references, overfull boxes, page count, and any
# forbidden strings in the text. A build is fit to send when: no missing keys,
# exit 0, 0 undefined refs, no "??", overfull boxes under 10pt, no forbidden hits.
set -uo pipefail
if [ $# -lt 2 ]; then
  echo "usage: $0 <writeup dir> <prior-work/INDEX.md> [main.tex]" >&2
  exit 2
fi
here=$(cd "$(dirname "$0")" && pwd)
writeup=$1
index=$2
main=${3:-precedence-findings.tex}
python -I -X utf8 "$here/make_bib.py" "$writeup" "$index" "$main" || exit 1
cd "$writeup" || exit 1
mkdir -p build
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build "$main" > "build/${main%.tex}.pass$pass.log" 2>&1
  status=$?
done
log="build/${main%.tex}.log"
pdf="build/${main%.tex}.pdf"
echo "pdflatex exit: $status"
grep -n -E '^!' "$log" | head -20
echo "undefined refs: $(grep -c -E 'Warning: (Citation|Reference) .* undefined' "$log")"
echo "overfull boxes:"
grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' "$log" | sort | uniq -c
if [ -f "$pdf" ]; then
  pdfinfo "$pdf" 2>/dev/null | grep Pages
  pdftotext -enc UTF-8 "$pdf" build/full.txt
  echo "forbidden strings in the PDF text (expect none):"
  grep -n -i -E '\.tex\b|tex:|\b(prof|cap|sec|eq|lem|thm|f):[a-z0-9]|\?\?|citation status|caveat|not verified|consulted|regrad|skeptic|subagent|coordinator|the library|case-insensitive|author copy|saved as|\bTable [0-9]' build/full.txt | head -20
fi
true
