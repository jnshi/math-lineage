# Publishing: deliverables and the pull request

Every finished review ends with five files next to the preprint, in a pull request against [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage). The format is fixed, because a tool compiles these files across all reviewed preprints into one summary. Reuse the schema exactly, and bump `format_version` if you ever have to change it.

```
preprints/<preprint>/
  precedence-findings.pdf     the final write-up
  precedence-findings.tex     its source, flattened into one standalone file
  precedence-findings.json    machine-readable findings  (format math-lineage/precedence-findings, v1)
  precedence-stats.json       counts derived from the JSON (format math-lineage/precedence-stats, v1)
  README.md                   replaced by a short summary of the findings that links to the PDF
```

## 1. PDF and flattened source
1. **Set the title-page date** in `writeup/precedence-findings.tex` to the date of the final revision, then run the full build.
2. **Flatten the source.** Run `python -I -X utf8 <skill>/scripts/flatten_tex.py writeup/precedence-findings.tex <scratch>/flat/precedence-findings.tex`. This inlines every `\input` and drops the `% BIB` comment lines, which are redundant once the bibliography is inlined. `\ploc`'s hidden file:line arguments stay; they never print.
3. **Check that the flat file compiles to the same document.** Compile it in `<scratch>/flat/` with **three** pdflatex passes: from a clean directory the table of contents only settles on the third. Then compare `pdftotext -layout` of both PDFs (`diff -q`).
4. **Check the comments.** Grep the flat file's comments for working notes, such as "paywalled", "not read" or instructions meant for agents, and remove any you find.
5. **Copy** the flat `.tex` and `writeup/build/precedence-findings.pdf` into `preprints/<preprint>/`.

## 2. `precedence-findings.json`
See `<skill>/assets/precedence-findings.example.json` for a complete example. Its structure:

- `format`: `"math-lineage/precedence-findings"`.
- `format_version`: `1`.
- `preprint`: `{id, title, date, path, companions: [{id, cited_as}]}`.
  - `id` is `"OAI:<preprint folder name>"`, or the bibtex key given in the preprint's README.
- `review`: `{date, report_pdf, report_tex, locator_convention}`.
- `definitions`: the text of every category, grade and source status. Copy these verbatim from the example so every file carries the same definitions.
- `sources`: a map from key to `{authors[], title, year, venue, arxiv, doi, in_preprint_bibliography, preprint_bib_key?}`. Each earlier work appears once.
  - **year** is the year of the first public version.
  - **arxiv and doi** may each be null. Give at least one when it exists, because tools match the same work across preprints by these.
- `findings[]`: `{id, category, grade, technique, summary, preprint_locations[], credit_in_preprint, impact?, sources: [{key, locators, role, status}]}`.
  - `category` is `A`, `B` or `C`.
  - `grade`:
    - for A and B: `Strong` or `Partial`;
    - for C: `Major` or `Moderate`.
  - `technique` names the technique, or the result for (B).
  - `preprint_locations` uses compiled numbering, for example `"§3 (p. 7)"` or `"Lemma 8.2 (pp. 31–32)"`.
  - `credit_in_preprint` is one sentence, or `null` for (C).
  - `impact` is for (C) only.
  - **status** is one of:
    - `not_cited`: the work is not in the preprint's bibliography;
    - `cited_for_other_content`: it is in the bibliography, but not cited for this content;
    - `credited_in_part`: it is cited for part of this content only;
    - `credited_elsewhere`: it is cited for this content at other locations, but not where the content is used;
    - `credited_indirectly`: the preprint cites a location, such as a companion lemma, that credits the work.

How to fill it in:
- **What the preprint cites.** Get this from `build/references.bib` (or `references.tex`), and grep the sections for `\cite…{key}` to see what each work is cited for.
- **Summaries and titles.** Take the summaries, titles, grades and locators from the final fragments (`scripts/print_summaries.py`) and the summary table.

## 3. `precedence-stats.json`
`python -I -X utf8 <skill>/scripts/precedence_stats.py preprints/<preprint> reviews/<slug>/writeup/parts/summary.tex`

The script validates the JSON before writing the stats:
- every source key resolves;
- every category, grade and status is defined, and each grade fits its category;
- `in_preprint_bibliography` matches the preprint's bibliography (by key, arXiv id, DOI and title);
- each status is consistent with the bibliography;
- the grades match the summary table.

Fix every reported error, then rerun. The stats it writes are:
- the number of findings by category, by grade, and by category and grade, with IDs;
- the number of distinct earlier works, and how many are not in the bibliography;
- the number of finding–source pairs with each status.

## 4. README
Overwrite the preprint folder's `README.md` from `<skill>/assets/README-template.md`. It contains:
- a link to the preprint and a prominent link to the write-up PDF;
- the three kinds of finding, with counts;
- one table row per finding (ID | Grade | Technique or result | Earlier work);
- one-line grade definitions;
- links to the `.tex` and the two JSON files.

The old README is still in git if anyone wants it back.

## 5. Pull request against `jnshi/math-lineage`
1. **Check access.** Run `gh auth status`, then `gh repo view jnshi/math-lineage --json viewerPermission -q .viewerPermission`.
   - **`ADMIN`, `MAINTAIN` or `WRITE`:** push branches to the remote that points at `jnshi/math-lineage`.
   - **Anything else:** fork first with `gh repo fork jnshi/math-lineage --remote`. This adds your fork as `origin` and keeps the original as `upstream`. Push to the fork.
2. **Branch from the current upstream default branch.**
   - `git fetch <remote-for-jnshi/math-lineage>`, then `git switch -c review/<short-preprint-name> <that-remote>/main`.
   - The deliverables are untracked files, so they carry over.
   - If the base moved since the review started, check that it didn't change the reviewed preprint or its companions: `git diff --stat <old> <new> -- preprints/<preprint> preprints/<companion>…`. If it did, the locators may be stale; tell the user.
3. **Stage only the deliverables.** Stage the five files above, plus `.gitignore` if you added `prior-work/` and `reviews/` to it.
   - Run `git status --short` and confirm nothing from `prior-work/` or `reviews/` is staged.
   - `git check-ignore -q prior-work/INDEX.md` should succeed.
4. **Commit.** The message is "Add precedence review: <preprint title>". Its body gives the finding counts (e.g. "12 findings: 5 Strong, 6 Partial, 1 Structural; 19 of 25 earlier works not in the preprint's bibliography"). End it with whatever attribution trailer the environment specifies for commits.
5. **Push** with `git push -u <remote> <branch>`.
6. **Open the PR.** Run `gh pr create --repo jnshi/math-lineage --base main --head <owner>:<branch> --title "Precedence review: <preprint title>" --body-file <scratch>/pr-body.md`. The body holds:
   - the README's summary and table;
   - the list of files added;
   - one paragraph on how the review was done: section-by-section reading, verification against downloaded sources, an author-persona check of every finding;
   - the attribution line the environment specifies for PR bodies.
7. **Report the PR link to the user.** If the environment provides PR or CI tools, use them to check the PR's status. Never enable auto-merge unless asked.

### Without `gh`
If `gh` is not installed or not signed in, open the PR through the GitHub website instead. Never try to work around authentication. Steps 2–4 above (branch, stage, commit) are the same. The push and the PR then depend on whether the user can push to `jnshi/math-lineage`. Ask them if you don't know. Otherwise, try the push: a "Permission … denied" or 403 error means they can't.

- **With push access:**
  1. Push the branch to the remote that points at `jnshi/math-lineage`.
  2. Give the user `https://github.com/jnshi/math-lineage/compare/main...<branch>?quick_pull=1&title=<title>&body=<body>`, with the title and body URL-encoded. The link opens the new-PR form pre-filled, and the user only clicks **Create pull request**. If the URL gets very long, leave out `body`, and give them the body to paste from `<scratch>/pr-body.md`.
- **Without push access, which is the usual case for anyone but the repository's owner:**
  1. Ask the user to fork the repository on GitHub, at `https://github.com/jnshi/math-lineage/fork`. Forking is an action on their account, so they do it themselves.
  2. Add their fork as a remote and push the branch there: `git remote add fork https://github.com/<their-user>/math-lineage.git`, then `git push -u fork <branch>`. Use their fork's actual name if they renamed it. Their existing git credentials must allow the push; if they don't, stop and say so.
  3. Give them the cross-fork link `https://github.com/jnshi/math-lineage/compare/main...<their-user>:<branch>?quick_pull=1&title=<title>&body=<body>`, URL-encoded the same way.

Users who know from the start that they have no push access can fork first and clone their fork instead (setup, step 0.1). In that case, add `jnshi/math-lineage` as `upstream` with `git remote add upstream https://github.com/jnshi/math-lineage.git`, and branch from `upstream/main` in step 2.
