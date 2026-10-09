# Publishing: deliverables and the pull request

Every finished review ends with five files next to the preprint, in a pull request against [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage). The format is fixed, because a tool compiles these files across all reviewed preprints into one summary. Reuse the schema exactly, and bump `format_version` if you ever have to change it.

```
preprints/<preprint>/
  precedence-findings.pdf     the final write-up, "Missing citations in “<preprint title>”"
  precedence-findings.tex     its source, flattened into one standalone file
  precedence-findings.json    machine-readable findings  (format math-lineage/precedence-findings, v2)
  precedence-stats.json       counts derived from the JSON (format math-lineage/precedence-stats, v2)
  README.md                   replaced by a short summary of the findings that links to the PDF
```

**Version 1 is superseded.** Version 1 used categories A/B/C and grades Strong/Partial/Major/Moderate. The validator now rejects a version 1 file with a request to update it. Reviews published in version 1 need their JSON, summary table and README redone in version 2. That takes judgment (relationship, centrality, form of inclusion), not just a mechanical conversion. A version 1 Partial with indirect credit through a companion becomes credited content, which is no longer a finding unless its novelty is overstated.

## 1. PDF and flattened source
1. **Set the title-page date** in `writeup/precedence-findings.tex` to the date of the final revision.
2. **Fill in the Provenance paragraph** at the end of `parts/about.tex`, then run the full build.
   - The model: the one that ran the agents. If unsure, count the `"model":"…"` fields in the session transcript.
   - The skill's commit: `git log -1 --format=%h -- .claude/skills/precedence-review`, from the version that ran the review. Check that the commit is on the remote (`git merge-base --is-ancestor <commit> origin/main`), since the README links to it.
   - The person who ran the job, and in one clause any input of theirs that shaped a finding, such as leads they supplied.
   - Any disclosure the operator asks you to add, verbatim.

   Keep it to these facts. The user cut a sentence describing this run's departures from the skill as overexplaining. There is no conflict-of-interest section by default: as the user put it, people who write surveys don't flag that they cite themselves.

`scripts/publish_prep.sh <writeup dir> <preprint dir> <scratch>/flat` runs steps 3–6 and the stats of §3 in one go, and stops at the first failure. The steps are:

3. **Flatten the source.** Run `python3 -I -X utf8 <skill>/scripts/flatten_tex.py writeup/precedence-findings.tex <scratch>/flat/precedence-findings.tex`. This inlines every `\input` and drops the `% BIB` comment lines, which are redundant once the bibliography is inlined. `\ploc`'s hidden file:line arguments stay; they never print.
4. **Check that the flat file compiles to the same document.** Compile it in `<scratch>/flat/` with **three** pdflatex passes: from a clean directory the table of contents only settles on the third. Then compare `pdftotext -layout` of both PDFs (`diff -q`).
5. **Check the comments.** Grep the flat file's comments for working notes, such as "paywalled", "not read" or instructions meant for agents, and remove any you find. The script prints comment lines that contain such words; it doesn't remove them.
6. **Copy** the flat `.tex` and `writeup/build/precedence-findings.pdf` into `preprints/<preprint>/`, and the PDF to `writeup/precedence-findings.pdf`.

Rerun it after every change to the write-up that should reach the deliverables. In the second run this sequence was typed by hand about six times.

## 2. `precedence-findings.json`
See `<skill>/assets/precedence-findings.example.json` for a complete example. Its structure:

- `format`: `"math-lineage/precedence-findings"`.
- `format_version`: `2`.
- `preprint`: `{id, title, date, path, companions: [{id, cited_as}]}`.
  - `id` is `"OAI:<preprint folder name>"`, or the bibtex key given in the preprint's README.
- `review`: `{date, report_pdf, report_tex, locator_convention}`.
- `definitions`: the text of every relationship, centrality, form of inclusion, credit status and flag. Copy these verbatim from the example so every file carries the same definitions.
- `sources`: a map from key to `{authors[], title, year, venue, arxiv, doi, in_preprint_bibliography, preprint_bib_key?}`. Each earlier work appears once. Use the library keys from INDEX.md, not short names of your own.
  - **year** is the year of the first public version.
  - **arxiv and doi** may each be null. Give at least one when it exists, because tools match the same work across preprints by these.
- `findings[]`: `{id, slug, in_report, relationship, centrality, form_of_inclusion, attribution_gap, overstated_novelty, novelty_claim?, technique, summary, preprint_locations[], credit_in_preprint, sources: [{key, locators, role, credit_status}]}`.
  - `id` is the printed ID (`F1`, `F2`, …, without gaps) for a finding in the report, and `null` for one kept in the JSON only.
  - `slug` is the fragment's slug, which also identifies a JSON-only finding.
  - `in_report` is false exactly when the persona's `form_of_inclusion` is `none`. Such findings stay here so the record of the missing citation survives.
  - `relationship`: `same technique`, `adapted`, `fragment`, `same route`, `same result`, `weaker result` or `subsuming result`.
  - `centrality`: `main result`, `central`, `supporting` or `peripheral` (best-effort). A weaker result is never `main result`.
  - `form_of_inclusion`: `citation`, `sentence`, `paragraph` or `none`, from the author-persona check.
  - `attribution_gap`: derived, and recomputed by the validator: relationship same technique, adapted, same route or same result; centrality main result, central or supporting; every source `not_cited` or `cited_for_other_content`.
  - `overstated_novelty`: the preprint cites the earlier work for this content, but its abstract, contribution statements or framing of a main result present it as new, explicitly or as a reader would reasonably take it. When true, `novelty_claim` says where (e.g. `"Abstract; framing of Theorem 1.1 (p. 2)"`), and every source is `credited`, `credited_elsewhere` or `credited_in_part`.
  - `technique` names the technique or result. Use the finding's title as printed, without the earlier works' names, and keep it in sync when titles change.
  - `preprint_locations` uses compiled numbering, for example `"§3 (p. 7)"` or `"Lemma 8.2 (pp. 31–32)"`.
  - `credit_in_preprint` is one sentence: what the preprint cites for this content, and where.
  - **credit_status** is one of:
    - `not_cited`: the work is not in the preprint's bibliography;
    - `cited_for_other_content`: it is in the bibliography, but not cited for this content;
    - `credited_elsewhere`: it is cited for this content at other locations, but not where the content is used;
    - `credited_in_part`: it is cited for part of this content only;
    - `credited`: it is cited for this content. Only with overstated novelty.

How to fill it in:
- **What the preprint cites.** Get this from the bibliography file, and grep the sections and the abstract for `\cite…{key}` to see what each work is cited for.
- **IDs, summaries and titles.** Take them from the final build: `python3 -I -X utf8 <skill>/scripts/print_summaries.py <writeup dir>` prints each finding's ID as LaTeX assigned it, with its slug, title and Summary. Take relationships, centralities, flags and locators from the summary table, and forms of inclusion from the author checks. The JSON's `id` must be the printed ID, not the slug.

## 3. `precedence-stats.json`
After a full build, run `python3 -I -X utf8 <skill>/scripts/precedence_stats.py preprints/<preprint> reviews/<slug>/writeup`.

The script validates the JSON before writing the stats. It fails, and deletes any old stats file, on:
- a version 1 file (with a request to update it);
- schema errors (field types);
- duplicate JSON keys, finding IDs, slugs or `preprint_bib_key`s;
- definitions that differ from the canonical ones;
- unknown relationship, centrality, form of inclusion or credit status, and a weaker result marked `main result`;
- report IDs that don't run F1, F2, … without gaps; a finding in the report with form `none`, or a JSON-only finding with an ID or another form;
- an `attribution_gap` that disagrees with its definition;
- `overstated_novelty` without a `novelty_claim`, or with an uncited source; `credited` without `overstated_novelty`;
- unknown source keys, and credit statuses inconsistent with `in_preprint_bibliography`;
- a `preprint_bib_key` that the preprint's TeX never `\cite`s. A `.bib` entry that is never cited is not in the bibliography;
- any disagreement between the summary table (resolved through the build's `.aux`) and the JSON on IDs, slugs, relationships, centralities, or the `\attrgap` and `\overstated` tags.

It does not decide by itself whether an earlier work is in the bibliography: that is a fact the review established by reading the preprint. If a source marked not in the bibliography matches a bibliography entry by arXiv id, DOI or exact title, the script prints a `WARNING (check by hand)` line. Each one is only a hint, but look at every one.

Two gaps remain:
- A source can be given the wrong cited key, for example the bib key of another paper the preprint does cite. Check each `preprint_bib_key` against the bibliography entry yourself.
- The script needs the preprint's TeX (`build/`) to check citations.

Fix every reported error, then rerun. The stats it writes, over the findings in the report, are:
- the counts by relationship (with IDs), by centrality and by form of inclusion;
- the IDs with an attribution gap, and with overstated novelty;
- the slugs of the JSON-only findings;
- the number of distinct earlier works, and how many are not in the bibliography;
- the number of finding–source pairs with each credit status.

## 4. README
Overwrite the preprint folder's `README.md` from `<skill>/assets/README-template.md`. It contains:
- a link to the preprint and a prominent link to the write-up PDF;
- one sentence with the counts: findings, overstated novelty, attribution gaps, and earlier works absent from the bibliography;
- one table row per finding (ID | Relationship | Centrality | Technique or result | Earlier work | Cited in the preprint?). The "Earlier work" cell names each work as "Authors Year", linked to its arXiv or DOI page. The links also tell apart two works with the same authors and year. The last cell gives the credit status in a few words and the flags in bold;
- one-line definitions of the terms;
- links to the `.tex` and the two JSON files;
- **last**, the one-line provenance: "**Provenance:** generated by LLM agents (<model>) running the [precedence-review](https://github.com/jnshi/math-lineage/tree/<commit>/.claude/skills/precedence-review) skill (commit <commit>); makes no claim of completeness and has not been vetted by a human. Run by <name>", plus any disclosure the operator asked for in About.

The old README is still in git if anyone wants it back.

## 5. Pull request against `jnshi/math-lineage`
**Ask the user before you create the branch, commit or push.** They may want to hold publication while checks are open. In the second run they dismissed the first publish prompt for that reason.

1. **Confirm the publishing setup before committing:** which remote to push to, and which commit author to use. `git ls-remote <remote>` tests access without changing anything. In the second run, the push failed on a stale HTTPS token. The user then switched the remote to an SSH alias for an agent account and set a local commit author, and the finished commit had to be amended with `--reset-author`. Settle this first.
2. **Check access.** Run `gh auth status`, then `gh repo view jnshi/math-lineage --json viewerPermission -q .viewerPermission`.
   - **`ADMIN`, `MAINTAIN` or `WRITE`:** push branches to the remote that points at `jnshi/math-lineage`.
   - **Anything else:** fork first with `gh repo fork jnshi/math-lineage --remote`. This adds your fork as `origin` and keeps the original as `upstream`. Push to the fork.
3. **Branch from the current upstream default branch.**
   - `git fetch <remote-for-jnshi/math-lineage>`, then `git switch -c review/<short-preprint-name> <that-remote>/main`.
   - The deliverables are untracked files, so they carry over.
   - If the base moved since the review started, check that it didn't change the reviewed preprint or its companions: `git diff --stat <old> <new> -- preprints/<preprint> preprints/<companion>…`. If it did, the locators may be stale; tell the user.
4. **Stage only the deliverables.** Stage the five files above, plus `.gitignore` if you added `prior-work/` and `reviews/` to it.
   - In a sparse clone, use `git add --sparse -- <files>`: the PDF falls outside a `!*.pdf` pattern, and plain `git add` refuses it.
   - Run `git diff --cached --name-status` and confirm all five files are there and nothing from `prior-work/` or `reviews/` is.
   - `git check-ignore -q prior-work/INDEX.md` should succeed.
5. **Commit.** The message is "Add precedence review: <preprint title>". Its body gives the counts (e.g. "9 findings: 4 same technique, 2 fragment, 1 same route, 1 weaker result, 1 subsuming result; 3 attribution gaps, 1 overstated novelty; 12 of 15 earlier works not in the preprint's bibliography"). End it with whatever attribution trailer the environment specifies for commits.
6. **Push** with `git push -u <remote> <branch>`.
7. **Open the PR.** Write the body to `reviews/<slug>/pr-body.md`, which is gitignored, and which the user can open. Then run `gh pr create --repo jnshi/math-lineage --base main --head <owner>:<branch> --title "Precedence review: <preprint title>" --body-file reviews/<slug>/pr-body.md`. The body holds:
   - the README's summary and table, with its links made absolute (relative links break in a PR body);
   - the list of files added;
   - one sentence on how the review was done: section-by-section reading against a library of earlier papers, verification against the downloaded sources, and an author-persona check of every finding;
   - the provenance line;
   - the attribution line the environment specifies for PR bodies.
8. **Report the PR link to the user.** If the environment provides PR or CI tools, use them to check the PR's status. Never enable auto-merge unless asked.

### Without `gh`
If `gh` is not installed or not signed in, open the PR through the GitHub website instead. Never try to work around authentication. Steps 1 and 3–5 above (setup, branch, stage, commit) are the same. The push and the PR then depend on whether the user can push to `jnshi/math-lineage`. Ask them if you don't know. Otherwise, try the push: a "Permission … denied" or 403 error means they can't.

- **With push access:**
  1. Push the branch to the remote that points at `jnshi/math-lineage`.
  2. Give the user `https://github.com/jnshi/math-lineage/compare/main...<branch>?quick_pull=1&title=<title>&body=<body>`, with the title and body URL-encoded. The link opens the new-PR form pre-filled, and the user only clicks **Create pull request**. A body with the findings table makes the URL about 6,000 characters long. In that case give the title-only link, and point the user to `reviews/<slug>/pr-body.md` to paste.
- **Without push access, which is the usual case for anyone but the repository's owner:**
  1. Ask the user to fork the repository on GitHub, at `https://github.com/jnshi/math-lineage/fork`. Forking is an action on their account, so they do it themselves.
  2. Add their fork as a remote and push the branch there: `git remote add fork https://github.com/<their-user>/math-lineage.git`, then `git push -u fork <branch>`. Use their fork's actual name if they renamed it. Their existing git credentials must allow the push; if they don't, stop and say so.
  3. Give them the cross-fork link `https://github.com/jnshi/math-lineage/compare/main...<their-user>:<branch>?quick_pull=1&title=<title>&body=<body>`, URL-encoded the same way.

Users who know from the start that they have no push access can fork first and clone their fork instead (setup, step 0.1). In that case, add `jnshi/math-lineage` as `upstream` with `git remote add upstream https://github.com/jnshi/math-lineage.git`, and branch from `upstream/main` in step 2.
