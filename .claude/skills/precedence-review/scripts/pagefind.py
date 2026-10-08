"""Find the PDF page of a phrase in pdftotext output, or print a page.

pdftotext ends every page with a form feed (\\f), so a match on "p.N" is on the
N-th page of the PDF: N is 1 + the number of form feeds before it. N is the PDF
page index, not necessarily the number printed on the page. The two differ when
the PDF has an unnumbered title or cover page, or carries journal page numbers
(a reprint whose first page is p. 695). Locators use the printed number, so for
each page with a hit the script also shows that page's first and last non-empty
lines, where the printed page number usually sits; read it from there.

Usage:
  python -I -X utf8 pagefind.py <file.txt> <regex> [<regex> ...] [--context N]
  python -I -X utf8 pagefind.py <file.txt> --page N [--page M ...]

Output per hit:
  [<regex>] p.N: ...context...
      (p.N first: <first line> | last: <last line>)    once per page and regex
--page N prints the N-th PDF page in full.

Whitespace in the text is collapsed within each page before matching, so
phrases that wrap across lines still match (not across pages). Regexes are
Python syntax, case-sensitive unless they start with (?i).

A text of more than 3000 characters with no form feed is rejected with exit
status 2: it was extracted without page breaks (e.g. pdftotext -nopgbrk), and
every hit would be reported on p.1.
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def edges(page, width=70):
    lines = [l.strip() for l in page.splitlines() if l.strip()]
    if not lines:
        return "(empty page)"

    def cut(s):
        return s if len(s) <= width else s[:width - 3] + "..."

    return f"first: {cut(lines[0])} | last: {cut(lines[-1])}"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    path, args = argv[1], argv[2:]
    context, pages, patterns = 160, [], []
    i = 0
    while i < len(args):
        if args[i] == "--context":
            context = int(args[i + 1])
            i += 2
        elif args[i] == "--page":
            pages.append(int(args[i + 1]))
            i += 2
        else:
            patterns.append(args[i])
            i += 1
    text = open(path, encoding="utf-8", errors="replace").read()
    if "\f" not in text and len(text) > 3000:
        print(f"error: {path} has no form feeds (\\f), so it has no page breaks. Re-extract it with "
              f"plain `pdftotext -enc UTF-8 <file.pdf> <file.txt>` (not -nopgbrk).", file=sys.stderr)
        return 2
    split = text.split("\f")
    if pages:
        for p in pages:
            print(f"===== page {p}")
            print(split[p - 1] if 0 < p <= len(split) else "(no such page)")
        return 0
    # Collapse whitespace within pages, keeping the form feeds.
    flat = "\f".join(re.sub(r"\s+", " ", page) for page in split)
    for pat in patterns:
        hits = list(re.finditer(pat, flat))
        if not hits:
            print(f"[{pat}] NOT FOUND")
        last_page = None
        for m in hits:
            page = flat.count("\f", 0, m.start()) + 1
            a, b = max(0, m.start() - context), min(len(flat), m.end() + context)
            snippet = flat[a:b].replace("\f", " | ")
            print(f"[{pat}] p.{page}: ...{snippet}...")
            if page != last_page:
                print(f"    (p.{page} {edges(split[page - 1])})")
                last_page = page
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
