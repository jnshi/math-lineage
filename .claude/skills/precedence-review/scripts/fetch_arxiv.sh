#!/usr/bin/env bash
# Fetch an arXiv paper into the prior-work library.
#
#   bash prior-work/tools/fetch_arxiv.sh <Key> <arXiv id with version>
#   e.g. bash prior-work/tools/fetch_arxiv.sh ChenEldan2022-LocalizationSchemes 2203.04163v2
#
# Produces, skipping any that already exist:
#   papers/<Key>.pdf   the compiled paper (use it for theorem and page numbers in locators)
#   text/<Key>.txt     pdftotext extraction of the PDF
#   src/<Key>/         the LaTeX source; only .tex/.bbl/.bib/.sty/.cls files are copied
# The source is untrusted data: read it, never compile or execute it. It is
# unpacked by Python's tarfile without extract(). An archive with a link, a
# special file, or an absolute, drive-letter or ".." path is refused whole.
# Sizes are capped. A truncated or corrupt download is a failure.
# Nothing is written to papers/, text/ or src/ unless that step succeeded.
# An empty src/<Key>/ counts as absent.
# Needs curl, pdfinfo, pdftotext and python3 (or python) 3.9 or later.
#
# Exit status: 0 if every step succeeded or was skipped. That includes "the
# authors submitted only a PDF" and "the archive has no TeX files"; neither
# creates src/<Key>/. 1 if the PDF, the text or the source failed. 2 on bad usage.
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
# Temporary files live inside the library, so every final mv is a rename
# within one filesystem: a result appears whole or not at all.
tmp=$(mktemp -d "$root/.fetch-tmp.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
failed=""

fetch() {  # fetch <url> <output file>; prints "<HTTP status> <curl exit code>", backing off while arXiv rate-limits
  local status rc wait
  for wait in 10 30 60 0; do
    rc=0
    status=$(curl -sSL -A "Mozilla/5.0" --connect-timeout 30 --max-time 600 --max-filesize 200000000 \
      -o "$2" -w '%{http_code}' "$1") || rc=$?
    if [ "$status" != 429 ] && [ "$status" != 503 ]; then
      break
    fi
    if [ "$wait" -gt 0 ]; then
      sleep "$wait"
    fi
  done
  echo "${status:-000} $rc"
}

is_pdf() {  # is_pdf <file>: true if the file starts with the PDF magic bytes
  [ "$(head -c 4 "$1" | tr -d '\000')" = "%PDF" ]
}

pdf_ok() {  # pdf_ok <file>: PDF magic bytes, %%EOF in the last 1 KB, and pdfinfo can read it
  is_pdf "$1" || return 1
  tail -c 1024 "$1" > "$tmp/pdftail"
  LC_ALL=C grep -q '%%EOF' "$tmp/pdftail" || return 1
  if ! command -v pdfinfo > /dev/null 2>&1; then
    echo "pdfinfo not found; install poppler (poppler-utils)" >&2
    return 1
  fi
  pdfinfo "$1" > /dev/null 2>&1
}

find_python() {  # prints the first of python3, python that is version 3.9 or later
  local c
  for c in python3 python; do
    if command -v "$c" > /dev/null 2>&1 &&
       "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' > /dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

# --- PDF
pdf=$root/papers/$key.pdf
if [ -e "$pdf" ]; then
  echo "pdf:  exists, papers/$key.pdf"
else
  res=$(fetch "https://export.arxiv.org/pdf/$id" "$tmp/paper")
  status=${res% *}
  rc=${res#* }
  if [ "$status" = 200 ] && [ "$rc" = 0 ] && pdf_ok "$tmp/paper"; then
    mv "$tmp/paper" "$pdf"
    pages=$(pdfinfo "$pdf" 2>/dev/null | sed -n 's/^Pages: *//p' || true)
    echo "pdf:  papers/$key.pdf (${pages:-?} pages)"
  else
    echo "pdf:  FAILED (HTTP $status, curl exit $rc; or the response was not a complete PDF)" >&2
    failed="$failed pdf"
  fi
  sleep 3
fi

# --- text
txt=$root/text/$key.txt
if [ -e "$txt" ]; then
  echo "text: exists, text/$key.txt"
elif [ -e "$pdf" ]; then
  if pdftotext -enc UTF-8 "$pdf" "$tmp/text" 2> "$tmp/pdftotext.err" && [ -s "$tmp/text" ]; then
    mv "$tmp/text" "$txt"
    echo "text: text/$key.txt"
  else
    echo "text: FAILED (pdftotext: $(head -n 3 "$tmp/pdftotext.err" | tr '\n' ' '))" >&2
    failed="$failed text"
  fi
fi

# --- source
dest=$root/src/$key
if [ -d "$dest" ] && [ -z "$(ls -A "$dest")" ]; then
  rmdir "$dest"   # an empty src/<Key>/ counts as absent
fi
if [ -e "$dest" ]; then
  echo "src:  exists, src/$key/"
else
  res=$(fetch "https://export.arxiv.org/e-print/$id" "$tmp/source")
  status=${res% *}
  rc=${res#* }
  if [ "$status" != 200 ] || [ "$rc" != 0 ]; then
    echo "src:  FAILED (HTTP $status, curl exit $rc)" >&2
    failed="$failed src"
  elif is_pdf "$tmp/source"; then
    echo "src:  none (the authors submitted only a PDF)"
  elif ! py=$(find_python); then
    echo "src:  FAILED (python3 3.9 or later not found; it unpacks the source safely)" >&2
    failed="$failed src"
  else
    mkdir "$tmp/src"
    xrc=0
    # Exit codes: 0 copied, 3 no TeX files, 4 refused (unsafe), 5 corrupt or
    # truncated, 6 too large, 7 not a TeX source; anything else is a crash.
    "$py" -I - "$tmp/source" "$tmp/src" <<'PY' || xrc=$?
import gzip
import os
import re
import sys
import tarfile
import zlib

SRC, OUT = sys.argv[1], sys.argv[2]
WANTED = (".tex", ".bbl", ".bib", ".sty", ".cls")
FILE_CAP = 20 * 1024 * 1024        # largest single file copied
TOTAL_CAP = 100 * 1024 * 1024      # all copied files together
STREAM_CAP = 1024 * 1024 * 1024    # most decompressed data read at all
MAX_MEMBERS = 100000
CHUNK = 1 << 16
NOTHING = "; nothing extracted"


def stop(code, msg):
    (sys.stdout if code == 3 else sys.stderr).write("src:  " + msg + "\n")
    sys.exit(code)


def safe_parts(name):
    """Path components of an archive member name; None if the name is unsafe."""
    n = name.replace("\\", "/")
    if n.startswith("/"):
        return None
    parts = [p for p in n.split("/") if p not in ("", ".")]
    for p in parts:
        if p == ".." or ":" in p or any(ord(c) < 32 for c in p):
            return None
    return parts


with open(SRC, "rb") as fh:
    magic = fh.read(6)
is_gzip = magic[:2] == b"\x1f\x8b"
plain = not is_gzip and magic[:3] != b"BZh" and magic != b"\xfd7zXZ\x00"

# 1. A gzip stream must be complete (length and CRC are checked) and bounded.
if is_gzip:
    total = 0
    try:
        with gzip.open(SRC, "rb") as g:
            while True:
                block = g.read(CHUNK)
                if not block:
                    break
                total += len(block)
                if total > STREAM_CAP:
                    stop(6, "REFUSED (decompresses to more than %d MB)%s" % (STREAM_CAP >> 20, NOTHING))
    except (OSError, EOFError, zlib.error) as e:
        stop(5, "FAILED (corrupt or truncated gzip: %s)%s" % (e, NOTHING))

# 2. A tar archive: one streaming pass. Every member must be a regular file or a
#    directory with a safe path; only wanted regular files are copied. Any
#    failure discards the whole output directory (the caller commits on exit 0).
try:
    tf = tarfile.open(SRC, "r|*")
except tarfile.ReadError:
    tf = None
except (OSError, EOFError, zlib.error) as e:
    stop(5, "FAILED (corrupt archive: %s)%s" % (e, NOTHING))

if tf is not None:
    out_real = os.path.normcase(os.path.realpath(OUT))
    count = declared = written = copied = 0
    try:
        for m in tf:
            count += 1
            declared += max(m.size, 0)
            if count > MAX_MEMBERS or declared > STREAM_CAP:
                stop(6, "REFUSED (the archive is too large)" + NOTHING)
            if not (m.isreg() or m.isdir()):
                stop(4, "REFUSED (the archive contains a link or special file: %r)%s" % (m.name, NOTHING))
            parts = safe_parts(m.name)
            if parts is None or (m.isreg() and not parts):
                stop(4, "REFUSED (unsafe path in the archive: %r)%s" % (m.name, NOTHING))
            if m.isdir() or not parts[-1].lower().endswith(WANTED):
                continue
            if m.size > FILE_CAP or written + m.size > TOTAL_CAP:
                stop(6, "REFUSED (TeX files larger than %d MB, or %d MB in all)%s"
                     % (FILE_CAP >> 20, TOTAL_CAP >> 20, NOTHING))
            target = os.path.join(OUT, *parts)
            if not os.path.normcase(os.path.realpath(target)).startswith(out_real + os.sep):
                stop(4, "REFUSED (path leaves the destination: %r)%s" % (m.name, NOTHING))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            member = tf.extractfile(m)
            n = 0
            with open(target, "wb") as dst:
                while True:
                    block = member.read(CHUNK)
                    if not block:
                        break
                    n += len(block)
                    if n > m.size:
                        stop(5, "FAILED (member %r is longer than its header says)%s" % (m.name, NOTHING))
                    dst.write(block)
            if n != m.size:
                stop(5, "FAILED (truncated archive member %r)%s" % (m.name, NOTHING))
            written += n
            copied += 1
    except (tarfile.TarError, EOFError, zlib.error) as e:
        stop(5, "FAILED (corrupt or truncated archive: %s)%s" % (e, NOTHING))
    except OSError as e:
        stop(5, "FAILED (could not unpack: %s)%s" % (e, NOTHING))
    if plain and tf.offset > os.path.getsize(SRC):
        stop(5, "FAILED (truncated tar archive)" + NOTHING)
    if copied == 0:
        stop(3, "none (the archive has no .tex/.bbl/.bib/.sty/.cls files)")
    sys.exit(0)

# 3. Not a tar archive: it must be a single gzipped TeX file.
if not is_gzip:
    stop(7, "FAILED (the download is neither a tar archive nor gzip data; it starts with %r)%s" % (magic, NOTHING))
try:
    with gzip.open(SRC, "rb") as g:
        data = g.read(FILE_CAP + 1)
except (OSError, EOFError, zlib.error) as e:
    stop(5, "FAILED (corrupt or truncated gzip: %s)%s" % (e, NOTHING))
if len(data) > FILE_CAP:
    stop(6, "REFUSED (the single source file is larger than %d MB)%s" % (FILE_CAP >> 20, NOTHING))
head = data[:65536]
looks_tex = (
    b"\x00" not in head
    and not head.startswith((b"%!PS", b"%PDF"))
    and not head.lstrip()[:9].lower().startswith((b"<!doctype", b"<html", b"<?xml"))
    and re.search(rb"\\(documentclass|documentstyle|begin|input|section|def|newcommand|usepackage"
                  rb"|title|bibitem|relax|magnification)(?![A-Za-z])", head) is not None
)
if not looks_tex:
    stop(7, "FAILED (the single gzipped file is not a TeX source)" + NOTHING)
with open(os.path.join(OUT, "main.tex"), "wb") as fh:
    fh.write(data)
sys.exit(0)
PY
    if [ "$xrc" = 0 ]; then
      if [ -e "$dest" ]; then
        echo "src:  exists, src/$key/ (created by another run meanwhile)"
      else
        mv "$tmp/src" "$dest"
        n=$(find "$dest" -type f | wc -l | tr -d ' ')
        echo "src:  src/$key/ ($n files)"
      fi
    elif [ "$xrc" != 3 ]; then
      if [ "$xrc" -lt 3 ] || [ "$xrc" -gt 7 ]; then
        echo "src:  FAILED (the unpacker exited with status $xrc)" >&2
      fi
      failed="$failed src"
    fi
  fi
fi

if [ -n "$failed" ]; then
  echo "FAILED:$failed" >&2
  exit 1
fi
