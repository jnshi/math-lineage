#!/usr/bin/env bash
# Build the write-up PDF and print the QA summary.
#
#   bash build.sh <writeup dir> <prior-work/INDEX.md> [main .tex, default precedence-findings.tex]
#
# Steps: regenerate parts/bibliography.tex (make_bib.py, next to this script;
# the build stops if it reports a problem); delete the previous PDF, logs and
# text; run pdflatex three times into <writeup>/build (from a clean build/ the
# table of contents settles only on the third pass); dump the PDF text to
# build/full.txt; check the gates.
#
# Exit status 0 only if every gate passes: pdflatex exit 0, no "!" errors, a
# PDF, no undefined reference or citation (including \hyperref targets and
# warnings wrapped in the log), no overfull box over 10pt, and no hit from
# forbidden-patterns.txt (next to this script). Hits from warning-patterns.txt
# are printed for review but do not fail the build.
set -uo pipefail
if [ $# -lt 2 ]; then
  echo "usage: $0 <writeup dir> <prior-work/INDEX.md> [main.tex]" >&2
  exit 2
fi
here=$(cd "$(dirname "$0")" && pwd)
writeup=$1
index=$2
main=${3:-precedence-findings.tex}
base=${main%.tex}
for f in forbidden-patterns.txt warning-patterns.txt make_bib.py; do
  if [ ! -f "$here/$f" ]; then
    echo "missing $here/$f" >&2
    exit 2
  fi
done
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
"$py" -I -X utf8 "$here/make_bib.py" "$writeup" "$index" "$main" || exit 1
cd "$writeup" || exit 1
mkdir -p build || exit 1
rm -f "build/$base.pdf" "build/$base.log" "build/$base".pass*.log build/full.txt
# Pattern files without comments, blank lines or CRs.
for tier in forbidden warning; do
  tr -d '\r' < "$here/$tier-patterns.txt" | sed -e '/^#/d' -e '/^[[:space:]]*$/d' -e 's/^@build //' > "build/$tier.pat" || exit 1
done

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

status=0
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build "$main" > "build/$base.pass$pass.log" 2>&1
  status=$?
done
log="build/$base.log"
pdf="build/$base.pdf"
fail=""

echo "pdflatex exit: $status"
if [ "$status" != 0 ]; then
  fail="$fail pdflatex-exit"
fi
if [ ! -f "$log" ]; then
  echo "no $log: pdflatex did not run (see build/$base.pass3.log):"
  head -5 "build/$base.pass3.log"
  fail="$fail no-log"
else
  grep -n -E '^!' "$log" | head -20
  if grep -q '^!' "$log"; then
    fail="$fail errors"
  fi
  # TeX wraps log lines at 79 characters; join them before matching warnings.
  LC_ALL=C awk '{ if (length($0) == 79) { buf = buf $0 } else { print buf $0; buf = "" } }
    END { if (buf != "") print buf }' "$log" > "build/$base.log-joined"
  undef=$(grep -E '(Citation|Reference|Hyper reference) .*undefined' "build/$base.log-joined")
  n_undef=0
  if [ -n "$undef" ]; then
    n_undef=$(printf '%s\n' "$undef" | wc -l | tr -d ' ')
  fi
  echo "undefined refs: $n_undef"
  if [ -n "$undef" ]; then
    printf '%s\n' "$undef" | head -10
  fi
  if [ "$n_undef" -gt 0 ] || grep -q -E 'There were undefined (references|citations)' "build/$base.log-joined"; then
    fail="$fail undefined-refs"
  fi
  echo "overfull boxes:"
  grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' "$log" | sort | uniq -c
  big=$(grep -o 'Overfull \\hbox ([0-9.]*pt too wide)' "$log" | sed 's/^[^(]*(\([0-9.]*\)pt.*$/\1/' | awk '$1 + 0 > 10' | wc -l | tr -d ' ')
  if [ "$big" -gt 0 ]; then
    echo "$big over 10pt"
    fail="$fail overfull"
  fi
fi

if [ -f "$pdf" ]; then
  pdfinfo "$pdf" 2>/dev/null | grep Pages
  if pdftotext -enc UTF-8 "$pdf" build/full.txt; then
    echo "forbidden strings in the PDF text (expect none):"
    hits=$(pattern_hits build/full.txt build/forbidden.pat)
    if [ -n "$hits" ]; then
      printf '%s\n' "$hits" | head -40
      fail="$fail forbidden-strings"
    fi
    echo "warnings (check each; remove it unless it is legitimate):"
    pattern_hits build/full.txt build/warning.pat | head -40
  else
    echo "pdftotext failed"
    fail="$fail pdftotext"
  fi
else
  echo "NO PDF PRODUCED"
  fail="$fail no-pdf"
fi

if [ -n "$fail" ]; then
  echo "result: FAIL ($(echo $fail))"
  exit 1
fi
echo "result: PASS"
