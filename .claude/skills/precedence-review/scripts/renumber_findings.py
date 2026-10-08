"""Renumber finding IDs in the write-up, e.g. after a merge or a withdrawal.

Usage: python -I -X utf8 renumber_findings.py <writeup dir> OLD=NEW [OLD=NEW ...]
  e.g. renumber_findings.py writeup S4=S3 S5=S4 P5=P4 P6=P5

All IDs change at once (through placeholders, so S5=S4 and S4=S3 don't clash), in
every .tex directly under <writeup>/findings and <writeup>/parts:
  - subsection titles, including optional short titles: "S4. " -> "S3. ";
  - labels and refs: f:S4 -> f:S3;
  - "Finding S4" / "finding S4" in text and comments;
and renames fragment files: findings/S4-slug.tex -> findings/S3-slug.tex.
Move retired fragments out of findings/ (to findings/retired/) first.
Afterwards, grep \\label{f:, \\ref{f: and \\subsection{ to confirm.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
writeup = sys.argv[1]
MAP = dict(arg.split("=", 1) for arg in sys.argv[2:])
for old, new in MAP.items():
    if not re.fullmatch(r"[SPC][0-9]+", old) or not re.fullmatch(r"[SPC][0-9]+", new):
        sys.exit(f"bad mapping {old}={new}: IDs look like S3, P12, C1")


def renumber(text):
    for old in MAP:
        ph = "@@" + old + "@@"
        text = re.sub(r"f:" + old + r"\b", "f:" + ph, text)
        text = re.sub(r"(\\subsection\{)" + old + r"\. ", r"\g<1>" + ph + ". ", text)
        text = re.sub(r"(\\subsection\[)" + old + r"\. ", r"\g<1>" + ph + ". ", text)
        text = re.sub(r"(\]\{)" + old + r"\. ", r"\g<1>" + ph + ". ", text)
        text = re.sub(r"([Ff]inding~?\s?)" + old + r"\b", r"\g<1>" + ph, text)
    for old, new in MAP.items():
        text = text.replace("@@" + old + "@@", new)
    return text


for sub in ("findings", "parts"):
    d = os.path.join(writeup, sub)
    for name in sorted(os.listdir(d)):
        path = os.path.join(d, name)
        if not name.endswith(".tex") or not os.path.isfile(path):
            continue
        text = io.open(path, encoding="utf-8").read()
        new = renumber(text)
        if new != text:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new)
            print("updated", os.path.join(sub, name))

# Rename in increasing order of the new ID, so P5->P4 happens before P6->P5.
fdir = os.path.join(writeup, "findings")
renames = []
for name in os.listdir(fdir):
    m = re.match(r"([SPC][0-9]+)-(.*\.tex)$", name)
    if m and m.group(1) in MAP:
        new_id = MAP[m.group(1)]
        renames.append(((new_id[0], int(new_id[1:])), name, new_id + "-" + m.group(2)))
for _, old, new in sorted(renames):
    target = os.path.join(fdir, new)
    if os.path.exists(target):
        sys.exit(f"refusing to overwrite {new}; rename order would collide")
    os.rename(os.path.join(fdir, old), target)
    print("renamed", old, "->", new)
