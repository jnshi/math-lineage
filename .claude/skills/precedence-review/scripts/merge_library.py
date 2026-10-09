"""Seed this review's paper library from a library kept elsewhere.

Usage: python3 -I -X utf8 merge_library.py <source prior-work dir> <target prior-work dir> <tag>

<tag> names the review the source library came from, e.g. critical-mixing-SK.

1. Copies papers/, text/ and src/ from the source into the target, never
   overwriting a file that exists.
2. Merges the source INDEX.md rows into the target INDEX.md: "Downloaded papers"
   rows whose key isn't in the target yet, and all "Checked but not downloaded"
   rows. The "Cited by the preprint?" and "Added by" cells get a "<tag>: "
   prefix, because the source's "Cited by" refers to another preprint. A dated
   note above the table explains the tag.
3. Checks that each imported key has papers/<key>.pdf in the target.

Rows with an unexpected number of cells (usually a literal | in a cell) are
skipped and printed; fix them by hand. Run it before the first agent downloads
anything, and read only the source folder the user pointed you to.
"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) != 4:
    sys.exit(__doc__)
src_dir, dst_dir, tag = sys.argv[1], sys.argv[2], sys.argv[3]
src_index = os.path.join(src_dir, "INDEX.md")
dst_index = os.path.join(dst_dir, "INDEX.md")
for p in (src_index, dst_index):
    if not os.path.isfile(p):
        sys.exit(f"not found: {p} (create the target INDEX.md from assets/INDEX-template.md first)")


def copy_tree(sub):
    copied = kept = 0
    root = os.path.join(src_dir, sub)
    if not os.path.isdir(root):
        return 0, 0
    for dirpath, _, files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        out = os.path.join(dst_dir, sub, rel)
        os.makedirs(out, exist_ok=True)
        for name in files:
            target = os.path.join(out, name)
            if os.path.exists(target):
                kept += 1
            else:
                shutil.copy2(os.path.join(dirpath, name), target)
                copied += 1
    return copied, kept


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def table_rows(lines, heading):
    """Rows of the first table after `heading`, without header and separator."""
    i = next((k for k, l in enumerate(lines) if l.strip() == heading), None)
    if i is None:
        sys.exit(f"heading {heading!r} not found")
    rows, seen_sep = [], False
    for l in lines[i + 1:]:
        if l.startswith("## "):
            break
        if l.startswith("|---"):
            seen_sep = True
            continue
        if seen_sep and l.startswith("|"):
            rows.append(l)
        elif seen_sep and rows and not l.strip():
            break
    return rows


def retag(row, ncols, prefix_cols):
    cells = row.strip().strip("|").split("|")
    if len(cells) != ncols:
        return None
    cells = [c.strip() for c in cells]
    for c in prefix_cols:
        cells[c] = f"{tag}: {cells[c]}"
    return "| " + " | ".join(cells) + " |"


def key_of(row):
    return row.split("|")[1].strip().strip("`")


def insert_after_sep(lines, heading, new_rows):
    i = next(k for k, l in enumerate(lines) if l.strip() == heading)
    j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("|---"))
    return lines[: j + 1] + new_rows + lines[j + 1:]


for sub in ("papers", "text", "src"):
    c, k = copy_tree(sub)
    print(f"{sub}/: {c} files copied, {k} already present (kept)")

src = read(src_index)
down = table_rows(src, "## Downloaded papers")
chk = table_rows(src, "## Checked but not downloaded")
bad, down_t, chk_t = [], [], []
for r in down:
    t = retag(r, 6, [3, 4])
    (down_t.append(t) if t else bad.append(r))
for r in chk:
    t = retag(r, 5, [4])
    (chk_t.append(t) if t else bad.append(r))

dst = read(dst_index)
existing = {key_of(l) for l in table_rows(dst, "## Downloaded papers")}
down_t = [r for r in down_t if key_of(r) not in existing]

note = (f"- **Imported rows.** Rows whose \"Added by\" starts with `{tag}:` were copied on "
        f"{datetime.date.today().isoformat()}, with their files, from the library of the `{tag}` review. "
        f"In those rows the \"Cited by the preprint?\" cell refers to that review's preprint, not to this one.")
if down_t or chk_t:
    k = next(k for k, l in enumerate(dst) if l.strip() == "## Downloaded papers")
    dst = dst[:k - 1] + [note] + dst[k - 1:]
    dst = insert_after_sep(dst, "## Downloaded papers", down_t)
    dst = insert_after_sep(dst, "## Checked but not downloaded", chk_t)
    with open(dst_index, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(dst))

print(f"downloaded rows imported: {len(down_t)} (source had {len(down)}; already present rows skipped)")
print(f"checked-not-downloaded rows imported: {len(chk_t)} (source had {len(chk)})")
print(f"rows skipped (unexpected cell count): {len(bad)}")
for r in bad:
    print("  SKIPPED:", r[:200])
missing = [key_of(r) for r in down_t if not os.path.isfile(os.path.join(dst_dir, "papers", key_of(r) + ".pdf"))]
print(f"imported keys without papers/<key>.pdf: {len(missing)}")
for m in missing:
    print("  NO PDF:", m)
