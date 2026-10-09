"""Seed this review's paper library from a library kept elsewhere.

Usage: python3 -I -X utf8 merge_library.py <source prior-work dir> <target prior-work dir> <tag>

<tag> names the review the source library came from, e.g. critical-mixing-SK
(ASCII letters, digits and . _ - only).

1. Reads both INDEX.md files first. The target needs a "## Downloaded papers"
   and a "## Checked but not downloaded" table (the heading, a header row and a
   |---| row); if either is missing, it stops before copying anything. Rows
   are split like make_bib.py: one leading and one trailing | are removed, and
   cells are split at every | not written \\|. A row with an unexpected number
   of cells (usually a literal | in a cell), or a downloaded row whose key is
   not 1-60 ASCII letters, digits and . _ -, is skipped and printed; fix it by
   hand.
2. Picks the rows to import: "Downloaded papers" rows whose key isn't in the
   target yet, and "Checked but not downloaded" rows the target doesn't have
   yet (compared cell by cell, with spaces collapsed and any "<tag>: "
   prefixes removed from the "Added by" cell). A second run imports nothing.
3. Copies files for the imported downloaded rows only, never overwriting a
   file: papers/<key>.pdf, and text/<key>.txt and src/<key>/ (only .tex .bbl
   .bib .sty .cls files) when the target has no papers/<key>.pdf or this run
   copied it, so a PDF and its text always come from the same library.
   Symbolic links (and, on Python 3.12 or later, junctions) are skipped.
4. Merges the rows into the target INDEX.md. The "Cited by the preprint?" and
   "Added by" cells get a "<tag>: " prefix, because the source's "Cited by"
   refers to another preprint. A dated note above the table explains the tag;
   it is added once per tag.
5. Reports imported keys without papers/<key>.pdf in the target. A file that
   could not be copied is reported and makes the exit status 1.

Run it before the first agent downloads anything, and read only the source
folder the user pointed you to.
"""
import datetime
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

TAG_RE = re.compile(r"[A-Za-z0-9._-]+")
KEY_RE = re.compile(r"[A-Za-z0-9._-]{1,60}")
SRC_EXT = (".tex", ".bbl", ".bib", ".sty", ".cls")
DOWN, CHECKED = "## Downloaded papers", "## Checked but not downloaded"
DOWN_COLS, CHECKED_COLS = 6, 5
isjunction = getattr(os.path, "isjunction", lambda p: False)

if len(sys.argv) != 4:
    sys.exit(__doc__)
src_dir, dst_dir, tag = sys.argv[1], sys.argv[2], sys.argv[3]
if not TAG_RE.fullmatch(tag):
    sys.exit(f"bad tag {tag!r}: use ASCII letters, digits and . _ - only")
src_index = os.path.join(src_dir, "INDEX.md")
dst_index = os.path.join(dst_dir, "INDEX.md")
for p in (src_index, dst_index):
    if not os.path.isfile(p):
        sys.exit(f"not found: {p} (create the target INDEX.md from assets/INDEX-template.md first)")


def read(p):
    with open(p, encoding="utf-8-sig", errors="replace") as f:
        return f.read().split("\n")


def split_row(line):
    """Cells of a table row, as make_bib.py splits them (\\| stays escaped)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def is_sep(cells):
    return any(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c)


def table(lines, heading):
    """(index of the |---| line, [row lines]) of the table under heading, or None."""
    i = next((k for k, l in enumerate(lines) if l.strip() == heading), None)
    if i is None:
        return None
    sep, rows = None, []
    for k in range(i + 1, len(lines)):
        l = lines[k]
        if l.startswith("## "):
            break
        if sep is None:
            if l.lstrip().startswith("|") and is_sep(split_row(l)):
                sep = k
            continue
        if not l.lstrip().startswith("|"):
            break
        rows.append(l)
    return None if sep is None else (sep, rows)


def key_of(cells):
    return cells[0].strip("`").strip()


def checked_id(cells):
    """A checked row's identity: cells with spaces collapsed, tag prefixes off "Added by"."""
    cells = [" ".join(c.split()) for c in cells]
    cells[4] = re.sub(r"^(?:[A-Za-z0-9._-]+: )+", "", cells[4])
    return tuple(cells)


def retag(cells, cols):
    cells = list(cells)
    for c in cols:
        cells[c] = f"{tag}: {cells[c]}"
    return "| " + " | ".join(cells) + " |"


# ---------------------------------------------------------------- 1. read both indexes
src = read(src_index)
dst = read(dst_index)
for heading in (DOWN, CHECKED):
    if table(dst, heading) is None:
        sys.exit(f"{dst_index} has no {heading!r} table (the heading, a header row and a |---| row); "
                 f"add it from assets/INDEX-template.md. Nothing was copied.")
src_down = table(src, DOWN)
src_chk = table(src, CHECKED)
for heading, t in ((DOWN, src_down), (CHECKED, src_chk)):
    if t is None:
        print(f"note: {src_index} has no {heading!r} table; nothing imported from it")
down = src_down[1] if src_down else []
chk = src_chk[1] if src_chk else []

# ---------------------------------------------------------------- 2. rows to import
bad = []
have_keys = {key_of(c) for c in map(split_row, table(dst, DOWN)[1]) if len(c) == DOWN_COLS}
have_chk = {checked_id(c) for c in map(split_row, table(dst, CHECKED)[1]) if len(c) == CHECKED_COLS}
down_new, keys, present = [], [], 0
for r in down:
    cells = split_row(r)
    if len(cells) != DOWN_COLS:
        bad.append((r, f"{len(cells)} cells, expected {DOWN_COLS}"))
        continue
    key = key_of(cells)
    if not KEY_RE.fullmatch(key):
        bad.append((r, f"key {key[:70]!r} is not 1-60 ASCII letters, digits and . _ -"))
        continue
    if key in have_keys:
        present += 1
        continue
    have_keys.add(key)
    keys.append(key)
    down_new.append(retag(cells, [3, 4]))
chk_new, chk_present = [], 0
for r in chk:
    cells = split_row(r)
    if len(cells) != CHECKED_COLS:
        bad.append((r, f"{len(cells)} cells, expected {CHECKED_COLS}"))
        continue
    if checked_id(cells) in have_chk:
        chk_present += 1
        continue
    have_chk.add(checked_id(cells))
    chk_new.append(retag(cells, [4]))

# ---------------------------------------------------------------- 3. files of the imported rows
stats = {sub: {"copied": 0, "kept": 0, "link": 0} for sub in ("papers", "text", "src")}
failed = []


def is_link(p):
    return os.path.islink(p) or isjunction(p)


def copy_file(sub, src_path, dst_path):
    """Copy one regular file unless the target exists; returns True if it was copied."""
    if not os.path.lexists(src_path):
        return False
    if is_link(src_path) or not os.path.isfile(src_path):
        stats[sub]["link"] += 1
        print(f"  skipped (a link or not a regular file): {src_path}")
        return False
    if os.path.lexists(dst_path):
        stats[sub]["kept"] += 1
        return False
    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src_path, dst_path)
    except OSError as e:
        failed.append(f"{src_path}: {e}")
        return False
    stats[sub]["copied"] += 1
    return True


linked_dirs = [sub for sub in ("papers", "text", "src") if is_link(os.path.join(src_dir, sub))]
for sub in linked_dirs:
    print(f"  skipped {os.path.join(src_dir, sub)}: it is a link")
for key in keys:
    pdf = os.path.join(dst_dir, "papers", key + ".pdf")
    copied = "papers" not in linked_dirs and copy_file(
        "papers", os.path.join(src_dir, "papers", key + ".pdf"), pdf)
    if not copied and os.path.lexists(pdf):
        continue  # the target keeps its own PDF, so its own text and source too
    if "text" not in linked_dirs:
        copy_file("text", os.path.join(src_dir, "text", key + ".txt"), os.path.join(dst_dir, "text", key + ".txt"))
    root = os.path.join(src_dir, "src", key)
    if "src" in linked_dirs or not os.path.lexists(root):
        continue
    if is_link(root) or not os.path.isdir(root):
        stats["src"]["link"] += 1
        print(f"  skipped (a link or not a folder): {root}")
        continue
    for dirpath, dirnames, files in os.walk(root):
        for d in list(dirnames):
            if is_link(os.path.join(dirpath, d)):
                dirnames.remove(d)
                stats["src"]["link"] += 1
                print(f"  skipped (a link): {os.path.join(dirpath, d)}")
        for name in files:
            if name.lower().endswith(SRC_EXT):
                s = os.path.join(dirpath, name)
                copy_file("src", s, os.path.join(dst_dir, "src", key, os.path.relpath(s, root)))

# ---------------------------------------------------------------- 4. the target INDEX.md
note_start = f"- **Imported rows.** Rows whose \"Added by\" starts with `{tag}:`"
note = (f"{note_start} were copied on "
        f"{datetime.date.today().isoformat()}, with their files, from the library of the `{tag}` review. "
        f"In those rows the \"Cited by the preprint?\" cell refers to that review's preprint, not to this one.")
if down_new or chk_new:
    if not any(l.startswith(note_start) for l in dst):
        k = next(k for k, l in enumerate(dst) if l.strip() == DOWN)
        if k > 0 and not dst[k - 1].strip():  # before the blank line above the heading
            dst = dst[:k - 1] + [note] + dst[k - 1:]
        else:
            dst = dst[:k] + [note, ""] + dst[k:]
    for heading, new in ((DOWN, down_new), (CHECKED, chk_new)):
        j = table(dst, heading)[0]
        dst = dst[:j + 1] + new + dst[j + 1:]
    with open(dst_index, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(dst))

# ---------------------------------------------------------------- 5. report
for sub, s in stats.items():
    print(f"{sub}/: {s['copied']} files copied, {s['kept']} already present (kept), {s['link']} links skipped")
print(f"downloaded rows imported: {len(down_new)} (source had {len(down)}; {present} already present)")
print(f"checked-not-downloaded rows imported: {len(chk_new)} (source had {len(chk)}; {chk_present} already present)")
print(f"rows skipped: {len(bad)}")
for r, why in bad:
    print(f"  SKIPPED ({why}):", r[:200])
missing = [k for k in keys if not os.path.isfile(os.path.join(dst_dir, "papers", k + ".pdf"))]
print(f"imported keys without papers/<key>.pdf: {len(missing)}")
for m in missing:
    print("  NO PDF:", m)
if failed:
    print(f"files that could not be copied: {len(failed)}")
    for x in failed:
        print("  FAILED:", x)
    sys.exit(1)
