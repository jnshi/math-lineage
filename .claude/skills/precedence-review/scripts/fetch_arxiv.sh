#!/usr/bin/env bash
# Fetch an arXiv paper into the prior-work library.
#
#   bash prior-work/tools/fetch_arxiv.sh <Key> <arXiv id with version>
#   e.g. bash prior-work/tools/fetch_arxiv.sh ChenEldan2022-LocalizationSchemes 2203.04163v2
#
# Produces, skipping any that already exist:
#   papers/<Key>.pdf   the compiled paper (use it for theorem and page numbers in locators)
#   text/<Key>.txt     pdftotext extraction of the PDF
#   src/<Key>/         the LaTeX source; only .tex/.bbl/.bib/.sty/.cls files are extracted
# The source is untrusted data: read it, never compile or execute it.
# This script does not edit INDEX.md; add the row yourself.
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: $0 <Key> <arXiv id with version, e.g. 2203.04163v2 or math/0505690v2>" >&2
  exit 2
fi
key=$1
id=$2
if ! [[ $key =~ ^[A-Za-z0-9._-]{1,60}$ ]]; then
  echo "bad key '$key': ASCII letters, digits and . _ - only, at most 60 characters" >&2
  exit 2
fi
if ! [[ $id =~ ^([0-9]{4}\.[0-9]{4,5}|[a-z-]+(\.[A-Z]{2})?/[0-9]{7})v[0-9]+$ ]]; then
  echo "bad arXiv id '$id': include the version, e.g. 2203.04163v2" >&2
  exit 2
fi

root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$root/papers" "$root/text" "$root/src"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fetch() {  # fetch <url> <output file>; prints the final HTTP status, backing off while arXiv rate-limits
  local status wait
  for wait in 10 30 60 0; do
    status=$(curl -sSL -A "Mozilla/5.0" -o "$2" -w '%{http_code}' "$1" || true)
    if [ "$status" != 429 ] && [ "$status" != 503 ]; then
      break
    fi
    if [ "$wait" -gt 0 ]; then
      sleep "$wait"
    fi
  done
  echo "$status"
}

is_pdf() {  # is_pdf <file>: true if the file starts with the PDF magic bytes
  [ "$(head -c 4 "$1" | tr -d '\000')" = "%PDF" ]
}

pdf=$root/papers/$key.pdf
if [ -e "$pdf" ]; then
  echo "pdf:  exists, papers/$key.pdf"
else
  status=$(fetch "https://export.arxiv.org/pdf/$id" "$tmp/paper")
  if [ "$status" = 200 ] && is_pdf "$tmp/paper"; then
    mv "$tmp/paper" "$pdf"
    pages=$(pdfinfo "$pdf" 2>/dev/null | sed -n 's/^Pages: *//p' || true)
    echo "pdf:  papers/$key.pdf (${pages:-?} pages)"
  else
    echo "pdf:  FAILED (HTTP $status, or the response was not a PDF)" >&2
  fi
  sleep 3
fi

if [ -e "$pdf" ] && [ ! -e "$root/text/$key.txt" ]; then
  pdftotext -enc UTF-8 "$pdf" "$root/text/$key.txt" && echo "text: text/$key.txt"
fi

dest=$root/src/$key
if [ -e "$dest" ]; then
  echo "src:  exists, src/$key/"
  exit 0
fi
status=$(fetch "https://export.arxiv.org/e-print/$id" "$tmp/source")
if [ "$status" != 200 ]; then
  echo "src:  FAILED (HTTP $status)" >&2
  exit 1
fi
if is_pdf "$tmp/source"; then
  echo "src:  none (the authors submitted only a PDF)"
  exit 0
fi
mkdir "$dest"
if tar -tf "$tmp/source" > "$tmp/names" 2>/dev/null; then
  # Refuse archives containing links, absolute paths or parent-directory components.
  tar -tvf "$tmp/source" > "$tmp/long"
  if grep -q '^[lh]' "$tmp/long" || grep -qE '^/|(^|/)\.\.(/|$)' "$tmp/names"; then
    echo "src:  REFUSED (the archive contains links or unsafe paths); nothing extracted" >&2
    rmdir "$dest"
    exit 1
  fi
  grep -iE '\.(tex|bbl|bib|sty|cls)$' "$tmp/names" > "$tmp/wanted" || true
  if [ -s "$tmp/wanted" ]; then
    tar -xf "$tmp/source" -C "$dest" -T "$tmp/wanted"
  fi
else
  # A single gzipped file rather than an archive.
  gunzip -c "$tmp/source" > "$dest/main.tex" 2>/dev/null || cp "$tmp/source" "$dest/main.tex"
fi
n=$(find "$dest" -type f | wc -l)
echo "src:  src/$key/ ($n files)"
