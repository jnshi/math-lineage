"""Validate a precedence-findings.json and write precedence-stats.json beside it.

Usage: python -I -X utf8 precedence_stats.py <preprint dir> [<writeup>/parts/summary.tex]

Checks:
  - every source key used by a finding exists in "sources";
  - categories, grades and statuses are defined, and grades fit categories
    (A/B: Strong/Partial; C: Major/Moderate);
  - in_preprint_bibliography agrees with the preprint's bibliography
    (build/references.bib, any build/*.bib, or \\bibitem keys in build/*.tex),
    matched by key, arXiv id, DOI and title;
  - statuses are consistent with bibliography membership;
  - if summary.tex is given, its grades match the JSON.
On failure prints "VALIDATION FAILED" and the errors, and exits 1.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

d = Path(sys.argv[1])
data = json.loads((d / "precedence-findings.json").read_text(encoding="utf-8"))

bib_text, bib_keys = "", set()
for f in sorted((d / "build").glob("*.bib")):
    t = f.read_text(encoding="utf-8", errors="replace")
    bib_text += t
    bib_keys |= set(re.findall(r"^@\w+\{([^,\s]+),", t, re.M))
for f in sorted((d / "build").glob("*.tex")):
    t = f.read_text(encoding="utf-8", errors="replace")
    keys = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", t))
    if keys:
        bib_text += t
        bib_keys |= keys
if not bib_keys:
    sys.exit(f"no bibliography found under {d / 'build'}")
bib_norm = re.sub(r"[^a-z0-9]", "", bib_text.lower())

errors = []
defs = data["definitions"]
sources = data["sources"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


for key, s in sources.items():
    hits = [x for x in (s.get("arxiv"), s.get("doi")) if x and norm(x) in bib_norm]
    title_hit = norm(s["title"])[:40] in bib_norm
    if s["in_preprint_bibliography"]:
        if s.get("preprint_bib_key") not in bib_keys:
            errors.append(f"{key}: preprint_bib_key {s.get('preprint_bib_key')!r} not in the preprint's bibliography")
    elif hits or title_hit:
        errors.append(f"{key}: marked not in bibliography, but the bibliography matches it")

needs_bib = {"cited_for_other_content", "credited_in_part", "credited_elsewhere"}
for f in data["findings"]:
    fid = f["id"]
    if f["category"] not in defs["category"]:
        errors.append(f"{fid}: unknown category {f['category']}")
    if f["grade"] not in defs["grade"]:
        errors.append(f"{fid}: unknown grade {f['grade']}")
    structural = f["category"] == "C"
    if structural != (f["grade"] in ("Major", "Moderate")):
        errors.append(f"{fid}: grade {f['grade']} does not fit category {f['category']}")
    for src in f["sources"]:
        k, st = src["key"], src["status"]
        if k not in sources:
            errors.append(f"{fid}: unknown source key {k}")
            continue
        if st not in defs["source_status"]:
            errors.append(f"{fid}/{k}: unknown status {st}")
        inbib = sources[k]["in_preprint_bibliography"]
        if st == "not_cited" and inbib:
            errors.append(f"{fid}/{k}: status not_cited but the work is in the bibliography")
        if st in needs_bib and not inbib:
            errors.append(f"{fid}/{k}: status {st} but the work is not in the bibliography")

if len(sys.argv) > 2:
    summ = Path(sys.argv[2]).read_text(encoding="utf-8")
    table = dict(re.findall(r"\\hyperref\[f:(\w+)\]\{\w+\}\s*&\s*\\grade\{(\w+)\}", summ))
    mine = {f["id"]: f["grade"] for f in data["findings"]}
    if table != mine:
        errors.append(f"grades differ from the summary table: {table} vs {mine}")

if errors:
    print("VALIDATION FAILED")
    print("\n".join(errors))
    sys.exit(1)

findings = data["findings"]
pairs = [(f["id"], s["key"], s["status"]) for f in findings for s in f["sources"]]
cited_keys = {k for _, k, _ in pairs}
by_cat_grade = {}
for f in findings:
    by_cat_grade.setdefault(f["category"], Counter())[f["grade"]] += 1

stats = {
    "format": "math-lineage/precedence-stats",
    "format_version": 1,
    "preprint": data["preprint"]["id"],
    "generated_from": "precedence-findings.json",
    "review_date": data["review"]["date"],
    "findings": {
        "total": len(findings),
        "by_category": {c: sum(1 for f in findings if f["category"] == c) for c in defs["category"]},
        "by_grade": {g: sum(1 for f in findings if f["grade"] == g) for g in defs["grade"]},
        "by_category_and_grade": {
            c: {g: by_cat_grade.get(c, Counter())[g] for g in defs["grade"] if by_cat_grade.get(c, Counter())[g]}
            for c in defs["category"]
        },
        "ids_by_category_and_grade": {
            c: {g: [f["id"] for f in findings if f["category"] == c and f["grade"] == g]
                for g in defs["grade"] if any(f["category"] == c and f["grade"] == g for f in findings)}
            for c in defs["category"]
        },
    },
    "earlier_works": {
        "distinct": len(cited_keys),
        "not_in_preprint_bibliography": sum(1 for k in cited_keys if not sources[k]["in_preprint_bibliography"]),
        "in_preprint_bibliography": sum(1 for k in cited_keys if sources[k]["in_preprint_bibliography"]),
        "finding_source_pairs_by_status": {st: sum(1 for _, _, s in pairs if s == st) for st in defs["source_status"]},
    },
}
out = d / "precedence-stats.json"
out.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("validation passed; wrote", out)
print(json.dumps(stats["findings"]["by_category_and_grade"]), json.dumps(stats["earlier_works"]))
