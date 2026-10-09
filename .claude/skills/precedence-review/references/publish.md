# Publishing: deliverables and the pull request

Every finished review ends with five files next to the preprint, in a pull request against [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage). The format is fixed, so that a tool can compile these files across all reviewed preprints. Reuse the schema exactly, and bump `format_version` if you ever have to change it.

```
preprints/<preprint>/
  precedence-findings.pdf     the final write-up, "Missing citations in “<preprint title>”"
  precedence-findings.tex     its source, flattened into one standalone file
  precedence-findings.json    machine-readable findings  (format math-lineage/precedence-findings, v2)
  precedence-stats.json       counts derived from the JSON (format math-lineage/precedence-stats, v2)
  README.md                   replaced by a short summary of the findings that links to the PDF
```

Format version 1 (categories and grades) is superseded, and the validator rejects it.

## 1. Before publishing
1. **Set the title-page date** in `writeup/precedence-findings.tex` to the date of the final revision.
2. **Draft the Provenance paragraph** at the end of `parts/about.tex`: remove the comment marks from the template's block and fill it in.
   - **The model:** the one you are running as, plus any model a subagent was given explicitly.
   - **The skill's commit:** `git log -1 --format=%h -- .claude/skills/precedence-review`, from the version that ran the review. Check that the commit is on the remote (`git merge-base --is-ancestor <commit> origin/main`), since the PDF and README link to it.
   - **The person who ran the job:** ask the user how their name should appear. Never fill it in from the git configuration, an email address or the account. In one clause, add any input of theirs that shaped a finding, such as leads they supplied.
   - **Any disclosure the operator asks you to add,** verbatim.

   Keep it to these facts, and add no conflict-of-interest section by default.
3. **Get the user's approval of the exact wording.** The paragraph discloses facts about the user: their name, the AI models they have access to, and their input and choices during the run. Show them the paragraph and the README's provenance line (§4) exactly as they will be published, and wait for an explicit yes. Change the wording as they ask, and leave out anything they don't want published. The approved wording is the only version that goes out, in the PDF, the README and the PR body. If anything in it changes later, ask again.
4. **Build** with `build.sh` until it prints `result: PASS`. It stamps a passing build.
5. **Write `precedence-findings.json`** (§2).
6. **Run** `bash "<skill>/scripts/publish_prep.sh" "<writeup dir>" "<preprint dir>" "<scratch>/flat"`. It stops at the first failure. In order, it:
   - checks the arguments, and that the build is stamped as passing and unchanged since;
   - flattens the source with `flatten_tex.py`. This inlines every `\input` and drops the `% BIB` comment lines, which are redundant once the bibliography is inlined. `\ploc`'s hidden file:line arguments stay; they never print;
   - runs the lint `tex_gate.py` on the flat file's body;
   - compiles the flat file in `<scratch>/flat/` with three pdflatex passes, confined to that folder (from a clean folder the table of contents settles only on the third); checks both PDFs with `pdf_check.py`; and checks that the flat PDF's `pdftotext -layout` text is identical to the build's;
   - fails if the flat source or the PDF text contains a local path or an email address;
   - prints comment lines in the flat file that look like working notes ("paywalled", "not read", instructions meant for agents). Remove any you find, then rerun;
   - validates the JSON and writes the stats (§3);
   - copies the flat `.tex` and the PDF into `preprints/<preprint>/`, and the PDF to `writeup/precedence-findings.pdf`. Nothing is copied unless every earlier step passed.

   Rerun it after every change to the write-up that should reach the deliverables.
7. **Write the README** (§4), with the approved provenance line.

## 2. `precedence-findings.json`
See `<skill>/assets/precedence-findings.example.json` for a complete example. Its structure:

- `format`: `"math-lineage/precedence-findings"`.
- `format_version`: `2`.
- `preprint`: `{id, title, date, path, companions: [{id, cited_as}]}`. `id` is `"OAI:<preprint folder name>"`.
- `review`: `{date, report_pdf, report_tex, locator_convention}`.
- `definitions`: the text of every relationship, centrality, form of inclusion, credit status and flag. Copy these verbatim from the example so every file carries the same definitions.
- `sources`: a map from key to `{authors[], title, year, venue, arxiv, doi, in_preprint_bibliography, preprint_bib_key?}`. Each earlier work appears once. Use the library keys from INDEX.md, or the `NL-` keys of works outside the library, not short names of your own.
  - **year** is the year of the first public version.
  - **arxiv and doi** may each be null. Give at least one when it exists, because tools match the same work across preprints by these.
- `findings[]`: `{id, slug, in_report, relationship, centrality, form_of_inclusion, attribution_gap, overstated_novelty, novelty_claim?, technique, summary, preprint_locations[], credit_in_preprint, sources: [{key, locators, role, credit_status}]}`.
  - `id` is the printed ID (`F1`, `F2`, …, without gaps, in magnitude order) for a finding in the report, and `null` for one kept in the JSON only.
  - `slug` is the fragment's slug, which also identifies a JSON-only finding.
  - `in_report` is false exactly when the persona's `form_of_inclusion` is `none`. Such findings stay here so the record of the missing citation survives. Findings withdrawn on a fact, or whose claims were rejected, are not in the JSON.
  - `relationship`: `same result`, `same technique`, `adapted`, `proof shortcut`, `same route`, `fragment` or `weaker result` (in sort order).
  - `centrality`: `main result`, `central`, `supporting` or `peripheral` (best-effort judgment). A weaker result is never `main result`.
  - `form_of_inclusion`: `citation`, `sentence`, `paragraph` or `none`, from the author-persona check. With overstated novelty, it describes the change to the abstract or framing, and is never `citation`.
  - `attribution_gap`: derived, and recomputed by the validator. It holds when the relationship is same technique, adapted or same result; the centrality is main result, central or supporting; and the principal source is `not_cited` or `cited_for_other_content`.
  - `overstated_novelty`: the preprint credits the earlier work for this content, directly or through a cited location that credits it, but its abstract, contribution statements or framing of a main result present it as new, explicitly or as a reader would reasonably take it. When true, `novelty_claim` says where (e.g. `"Abstract; framing of Theorem 1.1 (p. 2)"`), and every source is `credited`, `credited_elsewhere` or `credited_in_part`.
  - `technique` is the finding's title as printed (a gloss without citations). Keep it in sync when titles change.
  - `preprint_locations` uses compiled numbering and printed pages, for example `"§3 (p. 7)"` or `"Lemma 8.2 (pp. 31–32)"`.
  - `credit_in_preprint` is one sentence: what the preprint cites for this content, and where.
  - `sources` lists the **principal** earlier work first. Each source has:
    - `locators`: where in that work, with printed pages, or null;
    - `role`: what that work contributes to the finding, in a few words;
    - `credit_status`, one of:
      - `not_cited`: the work is not in the preprint's bibliography, and no location the preprint cites credits it for this content;
      - `cited_for_other_content`: it is in the bibliography, but not cited for this content;
      - `credited_elsewhere`: it is credited for this content at other locations, directly or through a cited location that credits it (such as a companion lemma), but not where the content is used;
      - `credited_in_part`: it is credited for part of this content only;
      - `credited`: it is credited for this content. Only with overstated novelty.

      The credited statuses may apply to a work outside the bibliography, through a cited location that credits it; `cited_for_other_content` needs the work in the bibliography.

How to fill it in:
- **What the preprint cites.** Get this from the bibliography file, and grep the sections and the abstract for `\cite…{key}` to see what each work is cited for.
- **IDs, summaries and titles.** Take them from the final build: `python3 -I -X utf8 <skill>/scripts/print_summaries.py <writeup dir>` prints each finding's ID as LaTeX assigned it, with its slug, title and Summary. Take relationships, centralities, flags and locators from the summary table, and forms of inclusion from the author checks. The JSON's `id` must be the printed ID, not the slug.
- **JSON-only findings.** Take their fields from `findings/retired/<finding>.tex` and `FINDINGS.md`, correcting anything the persona check found wrong.

## 3. `precedence-stats.json`
`publish_prep.sh` runs the validator. To run it alone: `python3 -I -X utf8 <skill>/scripts/precedence_stats.py preprints/<preprint> reviews/<review>/writeup`, after a full build.

The script validates the JSON before writing the stats. On a version 2 file that fails, it deletes any old stats file. It fails on:
- a version 1 file (with a request to update it; nothing is deleted);
- schema errors (field types), and empty required fields;
- duplicate JSON keys, finding IDs, slugs or `preprint_bib_key`s, or a source repeated within a finding;
- definitions that differ from the canonical ones;
- unknown relationship, centrality, form of inclusion or credit status, and a weaker result marked `main result`;
- report IDs that don't run F1, F2, … without gaps, or that break the magnitude order;
- a finding in the report with form `none`, or a JSON-only finding with an ID or another form;
- a finding printed in the PDF (in the build's `.aux`) that isn't in the JSON as a report finding, or the reverse;
- an `attribution_gap` that disagrees with its definition;
- `overstated_novelty` without a `novelty_claim`, with an uncited source, or with form `citation`; `credited` without `overstated_novelty`;
- unknown source keys, and credit statuses inconsistent with `in_preprint_bibliography`;
- a `preprint_bib_key` that the preprint's TeX never `\cite`s. A `.bib` entry that is never cited is not in the bibliography;
- any disagreement between the summary table (resolved through the build's `.aux`) and the JSON on IDs, slugs, relationships, centralities, or the `\attrgap` and `\overstated` tags.

It does not decide by itself whether an earlier work is in the bibliography: that is a fact the review established by reading the preprint. If a source marked not in the bibliography matches a bibliography entry by arXiv id, DOI or exact title, the script prints a `WARNING (check by hand)` line. Each one is only a hint, but look at every one.

Two gaps remain:
- A source can be given the wrong cited key, for example the bib key of another paper the preprint does cite. Check each `preprint_bib_key` against the bibliography entry yourself.
- The script needs the preprint's TeX (`build/`) to check citations.

The stats it writes are:
- over the findings in the report: the counts by relationship (with IDs) and by centrality, and the IDs with an attribution gap and with overstated novelty;
- over all findings, including the JSON-only ones: the counts by form of inclusion, and the slugs of the JSON-only findings;
- the number of distinct earlier works, and how many are not in the bibliography;
- the number of finding–source pairs with each credit status.

## 4. README
Overwrite the preprint folder's `README.md` from `<skill>/assets/README-template.md`. It contains:
- a link to the preprint and a prominent link to the write-up PDF;
- one sentence with the counts: missing citations, overstated novelty, attribution gaps, and earlier works absent from the bibliography;
- one table row per finding (ID | Relationship | Centrality | Technique or result | Earlier work | Cited?).
  - The "Earlier work" cell names each work as "Authors Year", linked to its arXiv or DOI page. The links also tell apart two works with the same authors and year.
  - The last cell gives the credit status in a few words and the flags in bold;
- one-line definitions of the terms;
- links to the `.tex` and the two JSON files;
- **last**, the one-line provenance, in the wording the user approved (§1): "**Provenance:** generated by LLM agents (<model>) running the [precedence-review](https://github.com/jnshi/math-lineage/tree/<commit>/.claude/skills/precedence-review) skill (commit <commit>); makes no claim of completeness, and has not been vetted by a human. Run by <name>", plus any disclosure the operator asked for in About.

## 5. Pull request against `jnshi/math-lineage`
**Ask the user before you create the branch, commit or push.** They may want to hold publication while checks are open.

1. **Confirm the publishing setup before committing.**
   - Ask which remote to push to, and which commit author to use. The author's name and email are published with the commit, so suggest a GitHub noreply address (`…@users.noreply.github.com`) if they don't have one set.
   - Test the push with `git push --dry-run <remote> HEAD:refs/heads/<branch>`.
   - Settle all this first: a commit made under the wrong identity has to be amended (`git commit --amend --reset-author`).
2. **Check access.** Run `gh auth status`, then `gh repo view jnshi/math-lineage --json viewerPermission -q .viewerPermission`.
   - **`ADMIN`, `MAINTAIN` or `WRITE`:** push branches to the remote that points at `jnshi/math-lineage`.
   - **Anything else:** ask the user before forking, since a fork is created on their account. Then run `gh repo fork jnshi/math-lineage --remote`. This adds the fork as `origin` and keeps the original as `upstream`. Push to the fork.
3. **Branch from the current upstream default branch.**
   - `git fetch <remote-for-jnshi/math-lineage>`, then `git switch -c review/<review> <that-remote>/main`.
   - The deliverables are untracked files, so they carry over.
   - If the base moved since the review started, check that it didn't change the reviewed preprint or its companions: `git diff --stat <old> <new> -- preprints/<preprint> preprints/<companion>…`. If it did, the locators may be stale; tell the user.
4. **Stage only the deliverables.** Stage the five files above, plus `.gitignore` if you added `prior-work/` and `reviews/` to it.
   - In a sparse clone, use `git add --sparse -- <files>`: the PDF falls outside a `!*.pdf` pattern, and plain `git add` refuses it.
   - Run `git diff --cached --name-status` and confirm all five files are there and nothing from `prior-work/` or `reviews/` is.
   - `git check-ignore -q prior-work/INDEX.md` should succeed.
5. **Commit.** The message is "Add precedence review: <preprint title>". Its body gives the counts (e.g. "9 findings: 4 same technique, 1 proof shortcut, 1 same route, 2 fragment, 1 weaker result; 3 attribution gaps, 1 overstated novelty; 12 of 15 earlier works not in the preprint's bibliography"). End it with whatever attribution trailer the environment specifies for commits.
6. **Push** with `git push -u <remote> <branch>`.
7. **Open the PR.** Write the body to `reviews/<review>/pr-body.md`, which is gitignored, and which the user can open. Then run `gh pr create --repo jnshi/math-lineage --base main --head <owner>:<branch> --title "Precedence review: <preprint title>" --body-file reviews/<review>/pr-body.md`. The body holds:
   - the README's summary and table, with its links made absolute (relative links break in a PR body);
   - the list of files added;
   - one sentence on how the review was done: section-by-section reading against a library of earlier papers, verification against the downloaded sources, and an author-persona check of every finding;
   - the provenance line, as the user approved it;
   - the attribution line the environment specifies for PR bodies.
8. **Report the PR link to the user.** If the environment provides PR or CI tools, use them to check the PR's status. Never enable auto-merge unless asked.

### Without `gh`
If `gh` is not installed or not signed in, open the PR through the GitHub website instead. Never try to work around authentication. Steps 1 and 3–5 above (setup, branch, stage, commit) are the same. The push and the PR then depend on whether the user can push to `jnshi/math-lineage`. Ask them if you don't know. Otherwise, try the push: a "Permission … denied" or 403 error means they can't.

- **With push access:**
  1. Push the branch to the remote that points at `jnshi/math-lineage`.
  2. Give the user `https://github.com/jnshi/math-lineage/compare/main...<branch>?quick_pull=1&title=<title>&body=<body>`, with the title and body URL-encoded. The link opens the new-PR form pre-filled, and the user only clicks **Create pull request**. With the findings table, the URL gets too long (about 6,000 characters), so give the title-only link and point the user to `reviews/<review>/pr-body.md` to paste.
- **Without push access, which is the usual case for anyone but the repository's owner:**
  1. Ask the user to fork the repository on GitHub, at `https://github.com/jnshi/math-lineage/fork`. Without `gh` you can't fork for them.
  2. Add their fork as a remote and push the branch there: `git remote add fork https://github.com/<their-user>/math-lineage.git`, then `git push -u fork <branch>`. Use their fork's actual name if they renamed it. Their existing git credentials must allow the push; if they don't, stop and say so.
  3. Give them the cross-fork link `https://github.com/jnshi/math-lineage/compare/main...<their-user>:<branch>?quick_pull=1&title=<title>&body=<body>`, URL-encoded the same way.

Users who know from the start that they have no push access can fork first and clone their fork instead (setup, step 0.1). In that case, add `jnshi/math-lineage` as `upstream` with `git remote add upstream https://github.com/jnshi/math-lineage.git`, and branch from `upstream/main` in step 3.
