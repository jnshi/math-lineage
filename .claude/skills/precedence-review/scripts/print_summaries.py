"""Print the title and Summary paragraph of each finding fragment.

Usage: python -I -X utf8 print_summaries.py <findings dir>

Order: Strong (S), then Partial (P), then Structural (C), by number. Useful for
drafting the summary table, precedence-findings.json and the README.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

d = sys.argv[1]
entries = []
for name in os.listdir(d):
    m = re.match(r"([SPC])([0-9]+)-.*\.tex$", name)
    if m and os.path.isfile(os.path.join(d, name)):
        entries.append(("SPC".index(m.group(1)), int(m.group(2)), name))
for _, _, name in sorted(entries):
    text = io.open(os.path.join(d, name), encoding="utf-8").read()
    title = re.search(r"\\subsection(?:\[[^\]]*\])?\{(.*?)\}\\label", text, re.S)
    summ = re.search(r"\\paragraph\{Summary\.\}(.*?)\\paragraph\{", text, re.S)
    print("=" * 10, name)
    print("TITLE:", re.sub(r"\s+", " ", title.group(1)).strip() if title else "?")
    print(re.sub(r"\s+", " ", summ.group(1)).strip() if summ else "?")
