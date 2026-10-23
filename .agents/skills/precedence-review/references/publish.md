# Publishing: deliverables and the pull request

Every finished review ends with six files next to the preprint, in a pull request against [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage). The format is fixed, so that a tool can compile these files across all reviewed preprints. Reuse the schema exactly, and bump `format_version` if you ever have to change it.

```
preprints/<preprint>/
  precedence-findings.pdf     the final write-up, "Missing citations in “<preprint title>”"
  precedence-findings.tex     its source, flattened into one standalone file
  precedence-findings.json    machine-readable findings  (format math-lineage/precedence-findings, v2)
  precedence-stats.json       counts derived from the JSON (format math-lineage/precedence-stats, v2)
  precedence-telemetry.json   the run's tokens and active time (format math-lineage/precedence-telemetry, v1)
  README.md                   replaced by a short summary of the findings that links to the PDF
```

Format version 1 (categories and grades) is superseded, and the validator rejects it.

## 1. Before publishing
1. **Set the title-page date** in `writeup/precedence-findings.tex` to the date of the final revision.
2. **Draft the Provenance paragraph** at the end of `parts/about.tex`: remove the comment marks from the template's block and fill it in.
   - **The model:** the one you are running as, plus any model a subagent was given explicitly.
   - **The skill's commit:** `git log -1 --format=%h -- .agents/skills/precedence-review`, from the version that ran the review. Check that the commit is on the remote (`git merge-base --is-ancestor <commit> origin/main`), since the PDF and README link to it.
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
8. **Write the telemetry** (§5).

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
  - `in_report` is false exactly when the persona's `form_of_inclusion` is `none`: an in-scope finding, or a component of a merged finding, that the persona judged not worth a pointer, or placed under an exclusion on its judgment alone, with no passage named. Such records stay here so the record of the missing citation survives. Findings withdrawn on a fact, findings whose claims were rejected, and anything out of scope on a stated fact (including what the persona places under an exclusion on a textbook passage it names, or a date) are not in the JSON.
  - `relationship`: `same result`, `same technique`, `adapted`, `proof shortcut`, `same route`, `fragment` or `weaker result` (in sort order).
  - `centrality`: `main result`, `central`, `supporting` or `peripheral` (best-effort judgment). A weaker result is never `main result`.
  - `form_of_inclusion`: `citation`, `sentence`, `paragraph` or `none`, from the author-persona check. With overstated novelty, it describes the change to the abstract or framing, and is never `citation`.
  - `attribution_gap`: derived, and recomputed by the validator. It holds when the relationship is same technique, adapted or same result; the centrality is main result, central or supporting; and the principal source is `not_cited` or `cited_for_other_content`.
  - `overstated_novelty`: the preprint credits the earlier work for this content, directly or through a cited location that credits it, but its abstract, statements of significant contributions or framing of a main result present it as new, explicitly or as a reader would reasonably take it. When true, `novelty_claim` says where (e.g. `"Abstract; framing of Theorem 1.1 (p. 2)"`), and every source is `credited`, `credited_elsewhere` or `credited_in_part`.
  - `technique` is the finding's title as printed (a gloss without citations). Keep it in sync when titles change.
  - `preprint_locations` uses compiled numbering and printed pages, for example `"§3 (p. 7)"` or `"Lemma 8.2 (pp. 31–32)"`.
  - `credit_in_preprint` is one sentence: what the preprint cites for this content, and where.
  - `sources` lists the **principal** earlier work first: the one that holds the finding's relationship, judged against its whole content (works holding the same relationship type are tied, however closely each matches; among them, the one the others credit or build on, otherwise the earliest). The others are satellites; if the idea's originator is among them, it comes next. Each source has:
    - `locators`: where in that work, with printed pages, or null;
    - `role`: what that work contributes to the finding, in a few words;
    - `credit_status`, one of:
      - `not_cited`: the work is not in the preprint's bibliography, and no location the preprint cites credits it for this content;
      - `cited_for_other_content`: it is in the bibliography, but not cited for this content;
      - `credited_elsewhere`: it is credited for this content at other locations, directly or through a cited location that credits it (such as a companion lemma), but not where the content is used, in a way that an expert reader who doesn't know the earlier work might not connect with it;
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
In `jnshi/math-lineage`, every preprint folder already has a `README.md`: the release's (title, author, date and a BibTeX entry), or an earlier review's. Replace it entirely with one written from `<skill>/assets/README-template.md`, keeping nothing from the old file. It contains:
- a link to the preprint and a prominent link to the write-up PDF;
- one sentence with the counts: missing citations, overstated novelty, attribution gaps, and earlier works absent from the bibliography;
- one table row per finding (ID | Relationship | Centrality | Technique or result | Earlier work | Cited?).
  - The "Earlier work" cell names each work as "Authors Year", linked to its arXiv or DOI page. The links also tell apart two works with the same authors and year.
  - The last cell gives the credit status in a few words and the flags in bold;
- one-line definitions of the terms;
- links to the `.tex` and the three JSON files;
- **last**, the one-line provenance, in the wording the user approved (§1): "**Provenance:** generated by LLM agents (<model>) running the [precedence-review](https://github.com/jnshi/math-lineage/tree/<commit>/.agents/skills/precedence-review) skill (commit <commit>); makes no claim of completeness, and has not been vetted by a human. Run by <name>", plus any disclosure the operator asked for in About.

## 5. `precedence-telemetry.json`
Write it last, right before the pull request, so that it covers the whole run, and after `precedence-findings.json`, whose slugs it matches to the agents' labels. If work continues after you write it, such as changes the user asks for, write it again:

`python3 -I -X utf8 <skill>/scripts/run_telemetry.py preprints/<preprint> --skill-commit <commit> --session <id> … (--no-deviations | --deviations …)`

- `--skill-commit`: the commit the Provenance paragraph names; repeat it if it names several.
- `--session`: each session ID listed in `TIMING.md`. Without it, the script reads only the current session. If a listed session's transcript is gone (Claude Code deletes them after 30 days by default), the script stops: leave the telemetry out, along with its line in the README.
- **Deviations:** `--no-deviations` if the deviations list in `TIMING.md` is empty. Otherwise `--deviations`, with the tokens they added and saved, which the script sums by kind. Run it with `--dry-run` first: it lists the agents, numbered (0 is the coordinator), with their tokens.
  - **Extra:** `--extra <n>` for each agent that ran only because of a deviation, such as a test, a rerun or a relaunch. When the extra work is part of an agent's work, such as a resumed agent's work after the deviation or the coordinator's own, estimate its share: `--extra <n>=0.3`.
  - **Saved:** what the skipped or shortened steps, or the work taken from an earlier run, would have cost, as a multiple of a comparable agent of this run: `--saved <n>=2` for two section passes like agent `<n>`.
  - **Otherwise, improvise:** when the effect can't be tied to agents of this run, estimate it by kind, as in `--extra-tokens cache_read=40M,output=0.3M` (or `--saved-tokens`). For example, use the same pass in other reviews' published `precedence-telemetry.json`, preferably ones without deviations, scaled by the number of sections or findings. With no basis at all, pass `--extra unknown` or `--saved unknown`.
  - Note in `TIMING.md` how you reached each estimate; only the sums are published.
- Outside Claude Code, pass `--usage-unavailable "<harness and version>"` in place of `--session`. Tokens and time are then null; don't fill them in from `TIMING.md` or from estimates.

The file carries its own definitions. It gives the tokens by kind (uncached input, cache writes, cache reads, output) and the active hours, in total, by model and reasoning effort, by pass and by subagent, with the deviation flag and estimates. Active hours leave out waiting for the user, usage-limit pauses and gaps over 10 minutes, but count shorter pauses.

Show the user the file and get their yes before committing it, since it discloses the models and reasoning efforts they used, the agents' labels and your deviation estimates. Point out any unusual model names the script reports. If they don't want it published, leave it out, along with its line in the README.

## 6. Pull request against `jnshi/math-lineage`

### Settle at the start
Before the review starts (SKILL.md, "Before starting", item 5), agree with the user how the branch will reach GitHub and who opens the pull request, and record the plan in `TIMING.md`. Ask rather than assume, and use any way the user prefers, including ones not listed here. Never handle passwords or tokens yourself: when something needs a sign-in, the user does it.
1. **Push access.** If `gh` is installed and signed in, `gh repo view jnshi/math-lineage --json viewerPermission -q .viewerPermission` shows it: `ADMIN`, `MAINTAIN` or `WRITE` means they can push branches there, with no fork. Otherwise ask.
2. **The fork,** without push access.
   - If they already have one, perhaps renamed or under an organization, use it.
   - Otherwise, settle who creates it and how. You can run `gh repo fork`, but only with their OK, since it creates a repository on their account (`--org <org>` puts it under an organization). Or they create it themselves: on the website (`https://github.com/jnshi/math-lineage/fork`), in GitHub Desktop, in an editor's GitHub integration, or through a GitHub connector in this environment.
   - If there is no clone yet, make the fork now and clone the fork (setup, step 0.1), not `jnshi/math-lineage`. An existing clone gets the fork as a remote.
3. **The account and the push.** Settle which GitHub account owns the branch, and how git authenticates to it: over HTTPS through their credential manager or `gh` (`gh auth setup-git`), or over SSH, perhaps through a host alias for a second account. If the plan uses `gh` and it isn't installed or signed in, ask the user to install it and run `gh auth login` themselves.
4. **The commit identity.** The author's name and email are published with the commit, so suggest a GitHub noreply address (`…@users.noreply.github.com`) if they don't have one set.
5. **Who opens the pull request:** you, with `gh pr create`; the user, from a pre-filled link ("Without `gh`", below) or on the website; or another tool they use.
6. **Test what can be tested now:** `gh auth status` if the plan uses `gh`, and `git ls-remote <url>` for the repository the branch will go to, once it exists. Some environments block pushes or SSH, and it is better to find out now than after the review.

### At publishing
**Ask the user before you create the branch, commit or push.** They may want to hold publication while checks are open.

1. **Check the plan from the start** (`TIMING.md`) against the setup: the remote, the commit identity, and that `gh` is still signed in if the plan uses it. Test the push with `git push --dry-run <remote> HEAD:refs/heads/<branch>`. Do this before committing: a commit made under the wrong identity has to be amended (`git commit --amend --reset-author`).
2. **Make the fork, if the plan has one and it doesn't exist yet,** in the way agreed. With `gh`: `gh repo fork jnshi/math-lineage --remote`, which adds the fork as `origin` and keeps the original as `upstream`. Push to the fork.
3. **Branch from the current upstream default branch.**
   - `git fetch <remote-for-jnshi/math-lineage>`, then `git switch -c review/<review> <that-remote>/main`.
   - The deliverables are untracked files, so they carry over.
   - If the base moved since the review started, check that it didn't change the reviewed preprint or its companions: `git diff --stat <old> <new> -- preprints/<preprint> preprints/<companion>…`. If it did, the locators may be stale; tell the user.
4. **Stage only the deliverables.** Stage the six files above (five if the user left out the telemetry), plus `.gitignore` if you added `prior-work/` and `reviews/` to it.
   - In a sparse clone, use `git add --sparse -- <files>`: the PDF falls outside a `!*.pdf` pattern, and plain `git add` refuses it.
   - Run `git diff --cached --name-status` and confirm they are all there and nothing from `prior-work/` or `reviews/` is.
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
If the plan doesn't use `gh`, or it stopped working, open the PR through the GitHub website instead. Never try to work around authentication. Steps 1 and 3–5 above (setup, branch, stage, commit) are the same. The push and the PR then depend on whether the user can push to `jnshi/math-lineage`, which the plan says. A "Permission … denied" or 403 error on the push means they can't.

- **With push access:**
  1. Push the branch to the remote that points at `jnshi/math-lineage`.
  2. Give the user `https://github.com/jnshi/math-lineage/compare/main...<branch>?quick_pull=1&title=<title>&body=<body>`, with the title and body URL-encoded. The link opens the new-PR form pre-filled, and the user only clicks **Create pull request**. With the findings table, the URL gets too long (about 6,000 characters), so give the title-only link and point the user to `reviews/<review>/pr-body.md` to paste.
- **Without push access, which is the usual case for anyone but the repository's owner:**
  1. If the fork doesn't exist yet, ask the user to create it as planned, for example at `https://github.com/jnshi/math-lineage/fork`.
  2. Add their fork as a remote and push the branch there: `git remote add fork https://github.com/<their-user>/math-lineage.git`, then `git push -u fork <branch>`. Use their fork's actual name if they renamed it. Their existing git credentials must allow the push; if they don't, stop and say so.
  3. Give them the cross-fork link `https://github.com/jnshi/math-lineage/compare/main...<their-user>:<branch>?quick_pull=1&title=<title>&body=<body>`, URL-encoded the same way.

If you cloned the fork at the start, add `jnshi/math-lineage` as `upstream` with `git remote add upstream https://github.com/jnshi/math-lineage.git`, and branch from `upstream/main` in step 3.
