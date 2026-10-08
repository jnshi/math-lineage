---
name: precedence-review
description: Run a full precedence review of a mathematics preprint. It finds the techniques, theory and partial results from earlier papers that the preprint reuses without credit. It verifies each one against the actual sources, and produces an expert-facing LaTeX write-up, machine-readable findings files, and a pull request that publishes them. Use this skill whenever someone wants a math paper or preprint checked for uncited precedence, missing attribution, unattributed reuse of techniques, prior work it should have cited, or "who did this first". That holds even if they don't say "precedence review", and especially for machine-generated preprints such as those in the openai/math release. Also use it to resume, extend, write up, check or publish such a review.
---

# Precedence review of a mathematics preprint

A precedence review reads a preprint section by section. It finds each place where the preprint reuses a technique, construction or result from an identifiable earlier paper without crediting it, and checks every claim against the earlier paper itself. The result is:
- a concise LaTeX report that an expert who has not read the preprint can verify at a glance;
- JSON files that a tool can aggregate across many preprints;
- a pull request that publishes both.

You are the **coordinator**. Subagents do the reading, searching, drafting and checking. You sequence the passes, keep the shared state, verify load-bearing claims yourself, and keep the user informed.

The work is long. In the first run, a 190-page preprint with 20 sections took most of a day. Each section subagent ran for 10–30 minutes and used 170k–430k tokens. Before starting, tell the user roughly what it will cost, and confirm which preprint to review.

`<skill>` below means this skill's base directory. `<repo>` is the working copy of the reviews repository `jnshi/math-lineage`, and `<scratch>` is your session scratch directory.

## Scope

What counts as a finding is what made this procedure useful, so get it exactly right and put it in every subagent brief. `references/scope-and-grading.md` has the full rules and worked examples.

- **(A) Unattributed reuse** is the main target. A technique, construction, identity, estimate or body of theory developed in an identifiable earlier paper is reused without credit for that content. "Without credit" includes no citation at all, and a citation that covers something else or something narrower.
- **(B) Same-problem precedence:** earlier, uncited partial progress on the same problem. **Only the introduction pass searches for it.** Later section agents focus on (A).
- **(C) Structural:** a published result would replace a large part of the argument. Subagents get a passive slot for it and report it only if they come across one. **There is no dedicated structural pass.**
- **Never report:**
  - related work whose omission is a judgment call;
  - textbook or folklore tools;
  - "cite the original rather than the later source" quibbles.

  The guiding sentence: *"Not related work citations that could be omitted as judgment calls; only direct precedence of partial progress on the same problem, and, more importantly, unattributed reuse of techniques or theory developed in earlier papers."*
- **Grades for (A)/(B):**
  - **Strong:** the earlier technique is reused essentially intact without credit, especially when it has a name. New ingredients do not lower the grade.
  - **Partial:** only a fragment is reused, or the credit is present but indirect.
  - Grade by how completely the *earlier technique* is reused, never against the preprint's whole argument.
- **Grades for (C):** Major or Moderate, by impact.
- **Specific-content rule.** Indirect credit counts only when the preprint cites a source, or a companion preprint, *for that specific content*, and the cited location credits the original. Citing the same paper nearby for something else is not credit. When the preprint re-proves content itself, a companion's parallel credit does not transfer.

## Layout

```
<repo>/preprints/<preprint>/      target; read-only until the publish step (build/sections/*.tex, build/references.bib, paper.pdf)
<repo>/prior-work/                shared paper library, reused across reviews (gitignored)
    INDEX.md  papers/  text/  src/  tools/fetch_arxiv.sh
<repo>/reviews/<slug>/            working files for this review (gitignored)
    NN-<section-slug>.md  FINDINGS.md  TIMING.md  COMPANION-CREDIT-MAP.md  CONSOLIDATION.md
    author-checks/<ID>.md   writeup/{precedence-findings.tex, parts/, findings/, build/}
<scratch>/                        briefs, compiled-text extractions, one subfolder per subagent
```

The layout follows `jnshi/math-lineage`, which mirrors the openai/math release: one folder per preprint under `preprints/`, each with its TeX source in `build/`.

## The passes, in order

**The order matters.** Every check of an open lead must finish before the write-up. The write-up then feeds the author-persona check, because that check tests the write-up's exact correspondences. In the first run, consolidation drifted to the end and had to be patched in after the write-up, which wasted a round. If the user inserts a new pass, check whether any pending verification now lands after the write-up, and say so if it does.

### 0. Setup (you, no subagents)
1. **Get a working copy of the reviews repository, [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage).** It mirrors the openai/math preprint release and collects the published reviews, and every review ends with a pull request against it.
   - **If the current directory is already a clone, skip cloning.** `git remote -v` shows `jnshi/math-lineage`, or a fork of it.
   - Otherwise clone it: `gh repo clone jnshi/math-lineage`, or `git clone https://github.com/jnshi/math-lineage`. If the user has no push access, fork it first; see `references/publish.md`.
   - On Windows, set `git config core.longpaths true` before checkout. Long preprint paths exceed MAX_PATH, and the checkout fails without it.
   - Reuse an existing working copy where possible. The gitignored `prior-work/` library only accumulates locally.
   - Fetch and fast-forward the default branch before starting.
2. **Locate the preprint and its companions.**
   - Companions are preprints from the same release that the preprint cites. They are **not** prior literature: use them only to understand imported inputs and to apply the specific-content rule.
   - A companion's bibliography may be a `references.tex` with `\bibitem`s rather than a `.bib` file.
3. **Map the sections from the compiled PDF's table of contents** (`pdftotext -enc UTF-8 -f 1 -l 3 paper.pdf -`), not from file names.
   - One `.tex` file can hold several sections, so give each section agent a file plus a line range.
   - Find each section's start with the Grep tool and the pattern `^\\section`.
4. **Extract compiled text** for the preprint and each companion into `<scratch>` with `pdftotext -enc UTF-8`. The text keeps `\f` page breaks, so a match's page number is 1 plus the number of `\f` before it. Every subagent needs this to give compiled locators. Companion PDFs are not always named `paper.pdf`.
5. **Set up the library.**
   - If `prior-work/` doesn't exist, create it with `INDEX.md` from `<skill>/assets/INDEX-template.md`.
   - Copy `<skill>/scripts/fetch_arxiv.sh` to `prior-work/tools/`.
   - Make sure `.gitignore` lists `prior-work/` and `reviews/`.
6. **Create `reviews/<slug>/`** with `FINDINGS.md` and `TIMING.md`, from `assets/FINDINGS-template.md` and `assets/TIMING-template.md`.

### 1. Section passes: one subagent per section, strictly one at a time
Each agent reads the digest of earlier findings. That is what keeps findings from being reported twice, and it only works if sections run in order.

`references/section-pass.md` has the brief and its variants:
- the introduction pass checks novelty claims and searches for (B);
- overview sections get a strategy-level check with less effort;
- every agent stays strictly within its section. A broadly briefed first agent roamed into the whole paper.

After each hand-back, before launching the next agent:
1. Read the report's Findings and Leads.
2. Check each grade against the rules. If you regrade, put a dated note in the report. Such notes are internal and never reach the write-up.
3. For each Strong finding, grep the whole preprint and its bibliography for the source's author names.
4. Verify yourself any claim that would change the picture, such as "this whole route is redundant", by reading the cited passage in the library.
5. Update `FINDINGS.md` and `TIMING.md`. Duration and tokens come from the task notification.
6. Carry the leads for later sections into the next brief.
7. Send the user a short status.

### 2. Companion credit map (one subagent, early)
Companions often re-prove the same lemma *with* an external credit that the preprint omits. This pass maps every companion credit to the parallel content in the preprint. Run it right after the introduction pass so that every later section gets its leads. Run halfway through the first review, it found nothing for the sections already done and three real leads for later ones. The brief is in `references/lead-passes.md`.

### 3. Consolidation (before the write-up)
Check every open lead: credit-map items in sections already reviewed, unresolved leads, and suggested merges. Also list the noted (C) items. The brief is in `references/lead-passes.md`.

### 4. Write-up (one drafting subagent per finding, in parallel)
See `references/writeup.md`.
1. **Scaffold the write-up yourself:** the preamble, the About and Overview parts, and the build tools.
2. **Launch the drafting agents.** Each re-verifies its finding against the sources. A drafter may conclude a lower grade, or title the finding "[Withdrawn]", and report it.
3. **Send the user a PDF as soon as the first fragment lands,** so they can catch problems early.
4. **Assemble.**
   - Merges are the user's call; recommend one when two findings overlap.
   - Move withdrawn or merged fragments to `findings/retired/`.
   - Renumber with `scripts/renumber_findings.py`.
   - Write the summary table.
   - Build, run the QA gates and send the PDF.

### 5. Author-persona check (one read-only agent per finding, in parallel)
Each agent plays the preprint's honorable author. It is curious and glad to be reminded of a forgotten source, but it rejects claims that are untrue or contrived. It also reports every typo and write-up error. Each agent writes `author-checks/<ID>.md`. The brief is in `references/skeptic.md`.

### 6. Apply verdicts (one agent per finding, in parallel)
1. Back up the fragments.
2. Distil each check into a short "verdict to apply" block in that agent's prompt.
3. Each agent edits only its own fragment. You make all cross-file changes yourself: bibliography, About, summary table.
4. Rebuild, run the QA gates and send the PDF.

The brief is in `references/skeptic.md`.

### 7. Publish and open a pull request
1. Put the deliverables into `preprints/<preprint>/`:
   - the PDF;
   - a flattened `.tex` that compiles on its own;
   - `precedence-findings.json`;
   - `precedence-stats.json`;
   - a README summarizing the findings.
2. **Finish by opening a pull request against `jnshi/math-lineage`.**
   - Use a new branch holding only those files, plus `.gitignore` if it changed.
   - Push the branch and run `gh pr create`.
   - Give the user the link.

The schema, scripts, README template and PR steps are in `references/publish.md`.

### Left out on purpose
- **Reference chaining.** It mined the bibliographies of all the cited papers and ranked candidates by how many cited papers cite them. In the first run it cost 29 minutes and 466k tokens and found nothing new. Only 8 of the 16 sources behind the eventual findings were in its pool, at ranks 4, 10 and then 62–696.
- **A dedicated structural pass.** The passive slot was judged enough.
- **Google Scholar "cited by".** There is no API, and it serves CAPTCHAs, which must not be bypassed.
- **The unauthenticated Semantic Scholar API.** It returns 429 almost immediately.

## Rules for the expert write-up

These rules came from review of the first write-up. Put them in every drafting, editing and fix brief, and check the PDF text against them.

- **Audience.** The readers are experts in the field who have not read the preprint and will only see the PDF. Every claim must be checkable at a glance: exact statements, compiled locators, and correspondences side by side, each in its own paper's notation.
- **Concise.** At most about 3 pages per finding.
  - No "citation status" paragraph: one sentence in the Summary is enough.
  - **No caveats.** The only test is: "does this mean the preprint is justified in omitting the citation?" If a reason passes, change the grade or withdraw the finding instead of writing a caveat.
  - No asides.
  - No calibration section of things examined and found fine.
  - No section/page map.
- **No tutorial expansion of the earlier technique.** State it precisely, in the source's notation, with locators. Agents don't write good explanations for learners. Readers learn the shared structure from the precise correspondences.
- **No process notes.** That means:
  - no grade history ("regraded", "originally Partial");
  - no agents, reports, library, review passes or searches;
  - no "not consulted" and no unreproducible checks.

  State citation facts as facts about the preprint. Omit anything you could not verify rather than printing "[not verified]".
- **Locators.**
  - Cite the preprint and companions by compiled numbering only: section, equation, theorem, page. `\ploc{compiled}{file:line}` prints only its first argument.
  - TeX file names, line numbers and labels never appear in the PDF.
  - Refer to the preprint's references by author name, never by its reference numbers.
- **Uniform form.**
  - Seven fixed headings: Summary, Setup, Role in the argument, The earlier technique (or result), Correspondence, What is new in the preprint, How to check. Drafters may reorder them where that reads better.
  - Lists without options.
  - Tables in `xltabular` with booktabs rules and `\addlinespace` after every row.
  - No numbered table captions.
- **Order and summary.**
  - Findings go Strong, then Partial, then Structural.
  - A summary table at the top has columns ID | Grade | Technique (source) | In the preprint | Credited?. Credited? is "---" for structural findings.

## Working with the user

- **Status.** After each hand-back, send one or two lines: what was found, the grade, and what is still running. Ask for decisions as numbered options with your recommendation.
- **Copy-paste summaries.** When asked for a summary to copy and paste, use a nested list rather than a table.
- **Multi-part approvals.** A "yes" to a multi-part proposal does not approve every part, especially a part the user then qualifies. If unsure, ask about that part.
- **Memory.** Record rules and corrections in memory if the environment has it. Don't record the user's speculative design ideas unless asked.
- **Privacy.** Never put the user's email or other identifying information in API requests, User-Agent strings or `mailto` parameters.
- **Files under review.** Don't change a file that running subagents are reading, such as the PDF under check. Edit the build copy, and publish after they finish.
- **Long-running checks.** Keep verification commands light, with explicit timeouts. A `du -sh` over a large clone stalls.
- **Git.** Commit and push only in the publish step's pull request, or when the user asks. Never commit `prior-work/` or `reviews/`.

## Environment pitfalls

These caused most of the retries in the first run, mostly on Windows with Git Bash. Paste the "Tool pitfalls" block from `references/environment.md` into every subagent prompt, adapted to the platform. The worst ones:
- **Backslashes.** The Bash tool can turn `\\` into `\`, even inside single quotes and quoted heredocs. That silently corrupts LaTeX, so edit `.tex` files only with Edit or Write, and write scripts to files before running them.
- **Python output encoding.** Python output can crash on a non-UTF-8 console, and `PYTHONIOENCODING` is ignored under `python -I`. Run `python -I -X utf8`, or call `sys.stdout.reconfigure(encoding="utf-8")`.
- **arXiv over plain http** returns an empty 301 with no error. Use `curl -sSL https://export.arxiv.org/...`, spaced 3–5 s apart. Look up the version before fetching.
- **MSYS paths.** MSYS rewrites Windows paths passed as arguments. Run pdflatex from inside its build directory with relative names, and use scratch subfolders rather than `/tmp`.

## Bundled files

| File | Purpose |
|---|---|
| `scripts/fetch_arxiv.sh` | Fetch an arXiv paper (PDF, text, safely extracted LaTeX source) into `prior-work/`. Copy it to `prior-work/tools/`. |
| `scripts/pagefind.py` | Find the compiled page of a phrase in a pdftotext file, or print a page. |
| `scripts/fragment_test.sh` | Test-compile one write-up fragment in a scratch folder and grep its PDF text for forbidden strings. |
| `scripts/make_bib.py` | Generate `parts/bibliography.tex` from the cited keys, in reading order. |
| `scripts/build.sh` | Build the whole write-up: bibliography, 3 pdflatex passes, QA summary. |
| `scripts/renumber_findings.py` | Renumber finding IDs (titles, labels, refs, file names) after merges or withdrawals. |
| `scripts/print_summaries.py` | Print each fragment's title and Summary, for the summary table and JSON. |
| `scripts/flatten_tex.py` | Inline every `\input` into one standalone `.tex` for publishing. |
| `scripts/precedence_stats.py` | Validate `precedence-findings.json` and write `precedence-stats.json`. |
| `assets/` | Templates: INDEX, FINDINGS, write-up preamble/main/about/summary, example JSON, README. |
