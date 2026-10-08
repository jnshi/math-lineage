"""Find the compiled page of a phrase in pdftotext output, or print a page.

pdftotext separates pages with form feeds (\\f), so the page of a match is
1 + the number of form feeds before it.

Usage:
  python -I -X utf8 pagefind.py <file.txt> <regex> [<regex> ...] [--context N]
  python -I -X utf8 pagefind.py <file.txt> --page N [--page M ...]

Whitespace in the text is collapsed before matching, so phrases that wrap
across lines still match. Regexes are Python syntax, case-sensitive unless
they start with (?i).
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


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
    if pages:
        split = text.split("\f")
        for p in pages:
            print(f"===== page {p}")
            print(split[p - 1] if 0 < p <= len(split) else "(no such page)")
        return 0
    # Collapse whitespace within pages, keeping the form feeds.
    flat = "\f".join(re.sub(r"\s+", " ", page) for page in text.split("\f"))
    for pat in patterns:
        hits = list(re.finditer(pat, flat))
        if not hits:
            print(f"[{pat}] NOT FOUND")
        for m in hits:
            page = flat.count("\f", 0, m.start()) + 1
            a, b = max(0, m.start() - context), min(len(flat), m.end() + context)
            snippet = flat[a:b].replace("\f", " | ")
            print(f"[{pat}] p.{page}: ...{snippet}...")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
