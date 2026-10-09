#!/usr/bin/env bash
# Prepare the published deliverables from a passing build.
#
#   bash publish_prep.sh <writeup dir> <preprint dir> <scratch flat dir> [main .tex, default precedence-findings.tex]
#
# Run build.sh first; this script uses its <writeup>/build/<main>.pdf. Steps:
# flatten the main file (flatten_tex.py) into <flat dir>, which is emptied
# first; compile the flat file there with three pdflatex passes; compare
# pdftotext -layout of both PDFs (they must be identical); print comment lines
# of the flat file that look like working notes (for review; not removed);
# copy the PDF to <writeup>/precedence-findings.pdf and <preprint dir>, and the
# flat .tex to <preprint dir>; validate the JSON and write the stats
# (precedence_stats.py <preprint dir> <writeup dir>).
#
# Exit status 0 only if every step succeeds; it prints "result: PASS" or
# "result: FAIL (<step>)" and stops at the first failure.
set -uo pipefail
if [ $# -lt 3 ]; then
  echo "usage: $0 <writeup dir> <preprint dir> <scratch flat dir> [main.tex]" >&2
  exit 2
fi
here=$(cd "$(dirname "$0")" && pwd)
writeup=$(cd "$1" && pwd)
preprint=$(cd "$2" && pwd)
flat=$3
main=${4:-precedence-findings.tex}
base=${main%.tex}
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
built="$writeup/build/$base.pdf"
[ -f "$built" ] || fail "no $built; run build.sh first"

rm -rf "$flat" && mkdir -p "$flat" || fail "cannot create $flat"
flat=$(cd "$flat" && pwd)
"$py" -I -X utf8 "$here/flatten_tex.py" "$writeup/$main" "$flat/precedence-findings.tex" || fail "flatten"

# pdflatex runs from inside the folder with a relative name (MSYS path rewriting).
( cd "$flat" &&
  for i in 1 2 3; do
    pdflatex -interaction=nonstopmode -halt-on-error precedence-findings.tex > "pass$i.log" 2>&1 || exit 1
  done ) || fail "flat compile (see $flat/pass*.log)"

pdftotext -layout "$built" "$flat/orig.txt" || fail "pdftotext of the build"
pdftotext -layout "$flat/precedence-findings.pdf" "$flat/flat.txt" || fail "pdftotext of the flat PDF"
diff -q "$flat/orig.txt" "$flat/flat.txt" >/dev/null || fail "flat PDF text differs from the build; compare $flat/orig.txt and $flat/flat.txt"
echo "flat text identical"

echo "comment lines that may be working notes (remove any that are):"
grep -n -i -E '(^|[^\\])%.*(paywall|not read|not verified|todo|fixme|agent|coordinator|subagent|garbled|saved as|author copy)' \
  "$flat/precedence-findings.tex" | cut -c1-200 || echo "  none"

cp "$built" "$writeup/precedence-findings.pdf" || fail "copy PDF to the writeup"
cp "$built" "$preprint/precedence-findings.pdf" || fail "copy PDF to the preprint folder"
cp "$flat/precedence-findings.tex" "$preprint/precedence-findings.tex" || fail "copy flat .tex"
echo "copied the PDF and the flat .tex to $preprint"

"$py" -I -X utf8 "$here/precedence_stats.py" "$preprint" "$writeup" || fail "JSON validation"
echo "result: PASS"
