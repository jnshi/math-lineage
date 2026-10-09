---
name: precedence-review
description: Run a full precedence review of a mathematics preprint. It finds the missing citations, meaning earlier papers behind the preprint's load-bearing techniques, constructions and results that the preprint doesn't cite where they are used, plus cited work whose novelty the abstract overstates. It verifies each correspondence against the actual sources, and produces an expert-facing LaTeX write-up ("Missing citations in …"), machine-readable findings files, and a pull request that publishes them. The current version is built around preprints from the openai/math release, and it sends its reports to the collaborative repository jnshi/math-lineage on GitHub. Use it when someone asks for a precedence review or a missing-citations review of a whole preprint, especially one from openai/math, or works in a jnshi/math-lineage checkout. Also use it to resume, extend, write up, check or publish such a review. A full review takes hours and millions of tokens, which can be a large share of a weekly usage limit. So for a narrower question, such as whether a paper should cite X, who first proved a lemma, or whether one technique is uncited, confirm with the user that they want the full review before starting it; often a direct answer is what they want.
---

# Precedence review of a mathematics preprint

A precedence review reads a preprint section by section. It finds the load-bearing techniques, constructions and results that trace to an identifiable earlier paper, where a reader of the preprint can't follow the trail because the preprint cites nothing for them, or cites something else. It checks every claim against the earlier paper itself. The result is:
- a concise LaTeX report that an expert who has not read the preprint can verify at a glance;
- JSON files that a tool can aggregate across many preprints;
- a pull request that publishes both.

**What the review is for.** Each finding is a missing citation: earlier work behind part of the preprint that a reader can't reach from the preprint itself. Recording it serves two purposes, in this order.
1. **Understanding.** It gives an expert the pointer the preprint doesn't: where an idea comes from, what familiar machinery is in play, and where to find its origins. This purpose decides which findings go into the write-up, how much space each gets, and that the relationship is described precisely.
2. **Accountability.** It records that the citation is missing. The write-up says so plainly in every entry, the summary table and the JSON keep the credit status, and the flags mark the most serious cases.

**Don't do what this process does poorly.** It is good at equation-level correspondences, exact locators, checking what a citation actually covers, and reading the sources it retrieved. It is weak at anything that needs complete knowledge of the literature, or taste. So the write-up doesn't summarize what is new in the preprint (the preprint does that, and better), doesn't pick a "best reference", doesn't present itself as a complete map, and doesn't impose its own architecture on the paper. It attaches verified pointers to the preprint's own structure.

You are the **coordinator**. Subagents do the reading, searching, drafting and checking. You sequence the passes, keep the shared state, verify load-bearing claims yourself, and keep the user informed.

**Cost.** The work is long. A 66-page preprint with 8 sections and 8 findings used about 7.5M subagent tokens over about 5 hours for the standard passes: section passes 230k–380k tokens each, consolidation about 440k, drafting 210k–370k per finding, author checks 190k–330k per finding, and applying verdicts 80k–200k per finding. A 190-page preprint with 20 sections took most of a day.

**Confirm before starting.** Unless the user has explicitly asked for a full review, or is already set up for one (working in a jnshi/math-lineage checkout on a preprint from the release), confirm that this is what they want. Say roughly what it will cost in hours and tokens, and offer the narrower alternative: answering their specific question about one claim, lemma or citation directly. In every case, confirm which preprint to review and tell the user the estimate before launching the first agent. **Estimate again before any extra round** (re-checks, repeated runs, redrafts): each costs about as much per finding as the first.

`<skill>` below means this skill's base directory. `<repo>` is the working copy of the reviews repository `jnshi/math-lineage`, and `<scratch>` is your session scratch directory.

## Scope

What counts as a finding is what made this procedure useful, so get it right and put it in every subagent brief. `references/scope-and-relationships.md` has the full rules and worked examples.

- **A finding** is a load-bearing part of the preprint (a technique, construction, estimate, proof route or result) that an identifiable earlier paper already contains, where the preprint doesn't cite that paper for it at the place it is used. Either nothing is cited, or what is cited covers something else or something narrower. **The one exception is overstated novelty** (below).
- **Relationship** (replaces the old grades and categories): what the mathematics has in common, regardless of citations.
  - **Same technique:** reused essentially intact, possibly in a new setting or with new ingredients around it.
  - **Adapted:** its structure followed, with a change at the core.
  - **Fragment:** one identifiable piece of the technique.
  - **Same route:** an earlier paper proposed the strategy, even heuristically, and the preprint carries it out.
  - **Same result** or **weaker result:** earlier progress on the same problem. The introduction pass searches for these; later passes record any they come across in one line, for consolidation.
  - **Subsuming result:** a published result would replace a large part of the argument. This is a passive slot; there is no dedicated pass.
- **Centrality (best-effort):**
  - **main result:** the earlier work covers the main result itself, or most of it;
  - **central:** the main theorem's proof runs through it;
  - **supporting:** it is an input to a central step;
  - **peripheral:** anything else.

  A weaker result takes the centrality of the statement it precedes, but never "main result". Each entry states its dependency chain (for example "Lemma 5.6 → Prop. 5.1 → Thm. 1.1"), so the reader can check the label without tracing it themselves.
- **Credit status,** per earlier work: not cited; cited for other content; credited elsewhere (not where it is used); credited in part. Content credited where it is used, directly or through a cited location that credits it, is not a finding, unless its novelty is overstated (below).
- **Specific-content rule.** A citation counts only when it is *for that specific content*. Citing the same paper nearby for something else is not credit. A citation of a named method covers that method's own lemmas, but not a different device from the same paper. When the preprint re-proves content itself, a companion's parallel credit does not transfer.
- **Flags:**
  - **attribution gap:** a close relationship (same technique, adapted, same route, same result), at least supporting, with the earlier work not cited for this content anywhere;
  - **overstated novelty:** the preprint cites the earlier work for this content, but its abstract, contribution statements or framing of a main result present it as new, explicitly or as a reader would reasonably take it. This is the one case in which credited content is reported.
- **Inclusion is decided late, by the author-persona check.** It asks whether pointing to the earlier work would help an expert reader enough to earn its place, and in what form. A finding it judges not worth a pointer stays in the JSON only. Section agents and drafters don't drop a verified candidate on a judgment call, such as "superseded by later cited work", "only a standard device", or "related rather than reused". They record it with the facts and leave the decision to the persona. In the second run, the two findings that agents had dropped on such grounds came back after the user looked at them, and that cost two extra rounds.
- **Not reported:**
  - textbook or folklore tools in their textbook form (a specific combination that traces to a paper is reportable);
  - "cite the original rather than the later source" quibbles, when a cited source genuinely covers the content;
  - anything public on or after the preprint's date;
  - parallels: analogous earlier work the preprint shows no sign of having drawn on (one sentence inside an entry at most).
- **Order:** by magnitude, numbered F1, F2, …: centrality first, then the relationship, closest first (same result, subsuming result, same technique, adapted, same route, fragment, weaker result), then reading order.

## Layout

```
<repo>/preprints/<preprint>/      target; read-only until the publish step
    build/sections/*.tex  build/references.bib (or build/references.tex with \bibitem)  paper.pdf (or main.pdf)
<repo>/prior-work/                shared paper library, reused across reviews (gitignored)
    INDEX.md  papers/  text/  src/  tools/fetch_arxiv.sh
<repo>/reviews/<slug>/            working files for this review (gitignored)
    NN-<section-slug>.md  FINDINGS.md  TIMING.md  COMPANION-CREDIT-MAP.md  CONSOLIDATION.md
    author-checks/<slug>.md   writeup/{precedence-findings.tex, parts/, findings/<slug>.tex, build/}
<scratch>/                        briefs, compiled-text extractions, one subfolder per subagent
```

The layout follows `jnshi/math-lineage`, which mirrors the openai/math release: one folder per preprint under `preprints/`, each with its TeX source in `build/`. File names vary between preprints, so check them and put the actual names in every brief.

## The passes, in order

**The order matters.** Every check of an open lead must finish before the write-up. The write-up then feeds the author-persona check, because that check tests the write-up's exact correspondences. In the first run, consolidation drifted to the end and had to be patched in after the write-up, which wasted a round. If the user inserts a new pass, check whether any pending verification now lands after the write-up, and say so if it does.

### 0. Setup (you, no subagents)
1. **Get a working copy of the reviews repository, [`jnshi/math-lineage`](https://github.com/jnshi/math-lineage).** It mirrors the openai/math preprint release and collects the published reviews, and every review ends with a pull request against it.
   - **If the current directory is already a clone, skip cloning.** `git remote -v` shows `jnshi/math-lineage`, or a fork of it. Fetch and fast-forward the default branch.
   - **Otherwise make a slim clone** (blobless and sparse, with no `lean/` and no PDFs except the target's), in the background, since it takes minutes. The full checkout is about 3 GB and the slim one about 270 MB. `references/environment.md` has the commands, with the Windows pitfalls they avoid. If the user has no push access, fork first; see `references/publish.md`.
   - Reuse an existing working copy where possible. The gitignored `prior-work/` library only accumulates locally.
2. **Locate the preprint and its companions.**
   - Note the actual file names: the PDF may be `paper.pdf` or `main.pdf`, and the bibliography `build/references.bib` or `build/references.tex` with `\bibitem`s.
   - Companions are preprints from the same release that the preprint cites. They are **not** prior literature: use them only to understand imported inputs and to apply the specific-content rule.
   - **If there are no companions,** skip the credit map, drop the companion clauses from the briefs, and use About's no-companion sentence.
3. **Map the sections from the compiled PDF's table of contents** (`pdftotext -enc UTF-8 -f 1 -l 3 <pdf> -`), not from file names.
   - One `.tex` file can hold several sections, so give each section agent a file plus a line range.
   - Find each section's start with the Grep tool and the pattern `^\\section`.
4. **Extract compiled text** for the preprint and each companion into `<scratch>` with `pdftotext -enc UTF-8`. The text keeps `\f` page breaks, so a match's page number is 1 plus the number of `\f` before it. Every subagent needs this to give compiled locators. Note whether the PDF page index equals the printed page number.
5. **Look for published reviews of sibling preprints:** `git ls-tree -r --name-only HEAD preprints | grep 'precedence-findings.json$'`. A review of a preprint on the same topic is a cheap source of leads, since its sources often recur. Pass its findings to the relevant section agents as leads, always with "judge this preprint on its own text and citations".
6. **Set up the library.**
   - **Ask the user whether they keep a library from earlier reviews elsewhere.** If so, seed from it before the first agent downloads anything: `python3 -I -X utf8 <skill>/scripts/merge_library.py <their prior-work> <repo>/prior-work <tag>`. It copies papers without overwriting, and merges the INDEX rows tagged with their origin, because their "Cited by the preprint?" column refers to another preprint. Read only what the user points you to in that location.
   - If `prior-work/` doesn't exist, create it with `INDEX.md` from `<skill>/assets/INDEX-template.md`.
   - Copy `<skill>/scripts/fetch_arxiv.sh` to `prior-work/tools/`.
   - Make sure `.gitignore` lists `prior-work/` and `reviews/`.
7. **Create `reviews/<slug>/`** with `FINDINGS.md` and `TIMING.md`, from `assets/FINDINGS-template.md` and `assets/TIMING-template.md`.

### 1. Section passes: one subagent per section, strictly one at a time
Each agent reads the digest of earlier findings. That is what keeps findings from being reported twice, and it only works if sections run in order.

`references/section-pass.md` has the brief, its variants and the loop you run after each hand-back. Things that made the difference in the second run:
- **Name candidate sources for new-looking devices:** a precise description of the device plus a short list of authors or papers to compare.
- **Ask for an explicit ruling on every nearby citation** that could count as credit for the content.
- **Keep textbook lists in briefs to generic tools.** Never list machinery at the level of a combination: an agent told that a combination's ingredients are textbook tends to rule the combination generic too, even when it traces to a specific paper.
- **Have the introduction pass read the abstract and the contribution statements** against what earlier work already covers, cited or not. That is where overstated novelty shows.

After each hand-back, verify each new finding's decisive correspondence yourself in the library sources. It took about 2–3 minutes per hand-back, and it caught two mischaracterizations. Run the author-name check for every new finding.

### 2. Companion credit map (one subagent, early; only if there are companions)
Companions often re-prove the same lemma *with* an external credit that the preprint omits. This pass maps every companion credit to the parallel content in the preprint. Run it right after the introduction pass so that every later section gets its leads. The brief is in `references/lead-passes.md`.

### 3. Consolidation (before the write-up)
Check every open lead. That includes credit-map items in sections already reviewed, unresolved leads, suggested merges, and the earlier-result one-liners recorded by section passes. It also covers:
- **sources that entered the library after section N, checked against sections ≤ N.** In the second run, a paper downloaded during §7 bore on §3 and was never checked against it;
- **a compiled-locator table per finding,** which drafters start from;
- **a proposed relationship and centrality for each finding,** with its dependency chain, and the resulting magnitude order;
- the noted subsuming results.

The brief is in `references/lead-passes.md`.

### 4. Write-up (one drafting subagent per finding, in parallel)
See `references/writeup.md`.
1. **Scaffold the write-up yourself:** the preamble, the About and Overview parts, and the build tools. This can overlap with the last section pass.
2. **Launch the drafting agents.** If a user decision is pending, such as a merge, launch the drafters it doesn't affect while you wait.
   - Each drafter re-verifies its finding against the sources.
   - **A drafter withdraws a finding only for a defect that prevents a coherent draft:** the correspondence fails at a specific step, the source postdates the preprint, the preprint credits it at the point of use after all, or a factual error leaves nothing to write. Everything else is a judgment for the author-persona check.
   - A drafter may *propose* a different relationship or centrality, with reasons, in its final message, but writes the finding as assigned.
3. **Assemble.**
   - Merges are the user's call; recommend one when two findings overlap.
   - Move withdrawn or merged fragments to `findings/retired/`, and remove every `\ref{f:<slug>}` to them.
   - LaTeX numbers the findings (F1, F2, …) from the order of the `\input` lines, which follows magnitude. Withdrawing or reordering a finding is just deleting or moving its line. Nobody types an ID.
   - Write the summary table.
   - Build, run the QA gates and send the PDF.

**Leads that arrive during the write-up,** for example from the user: send them to the section agent that owns that section. SendMessage resumes it with its context. Tell it that its earlier "generic" or "textbook" rulings were made without these papers, and should be re-decided where the papers bear on them. Draft any resulting finding as an extra slug, and update the slug list in the other briefs.

### 5. Author-persona check (one blind agent per finding, in parallel)
Each agent plays the preprint's author, whose values show up as two practical concerns. First and foremost, they want the manuscript to be as understandable as possible to experts. Second, they want to give due respect to work they built on. Every pointer also costs their reader attention.

For each finding the persona decides:
- **the form of inclusion:** none, a citation at the point of use, a clause or sentence, or a short paragraph. Anything but "none" needs specific reasons that affirm it; nobody has to justify omission;
- **whether the finding's claims hold,** including any claim of overstated novelty;
- **whether the relationship and centrality are right, and the finding's space proportionate** to that form;
- **the write-up errata.**

The checks are **blind**. A check sees no review notes, no earlier check and no retired fragment, and is never told that a candidate was withdrawn. A candidate that a drafter withdrew gets a check too if the user asks, or if the reason is open to dispute, with the original claim stated inline.

Run **one check per finding**. Repeated runs with a majority vote happen only if the user asks. The brief, and the reasons behind each of its choices, are in `references/skeptic.md`.

### 6. Apply verdicts (one agent per finding, in parallel)
1. Back up the fragments.
2. Distil each check into a short "verdict to apply" block in that agent's prompt.
3. **The persona's form of inclusion sets each finding's length:**
   - "none": the finding leaves the document but stays in the JSON (`in_report: false`), so the record of the missing citation survives. Note the reason in `FINDINGS.md`;
   - a citation, clause or sentence: a short entry of at most one page;
   - a short paragraph: a full entry of at most about three pages.
4. Apply the errata that fix errors: facts, mathematics, locators, misleading sentences and visible rendering problems. Skip pure style preferences.
5. Each agent edits only its own fragment. You make all cross-file changes yourself: bibliography, About, summary table.
6. Rebuild, run the QA gates and send the PDF.

The brief is in `references/skeptic.md`.

### 7. Publish and open a pull request
1. **Ask the user before you create a branch, commit or push.** They may hold publication while checks are still open.
2. **Confirm the publishing setup before the first commit:** which remote, which commit identity, and that the push works (`git ls-remote <remote>`). A commit made under the wrong identity has to be amended.
3. Put the deliverables into `preprints/<preprint>/`:
   - the PDF;
   - a flattened `.tex` that compiles on its own;
   - `precedence-findings.json`;
   - `precedence-stats.json`;
   - a README summarizing the findings, ending with the provenance line.

   `scripts/publish_prep.sh` does the flattening, the identical-text check, the copying and the JSON validation in one step.
4. **Open a pull request against `jnshi/math-lineage`.**
   - Use a new branch holding only those files, plus `.gitignore` if it changed. In a sparse clone, stage them with `git add --sparse`.
   - Push the branch and run `gh pr create`.
   - Without push access, go through a fork. Without `gh`, use a pre-filled link to GitHub's website. Both paths are in `references/publish.md`.
   - Give the user the link.

The schema, scripts, README template and PR steps are in `references/publish.md`.

### Left out on purpose
- **Reference chaining.** It mined the bibliographies of all the cited papers and ranked candidates by how many cited papers cite them. In the first run it cost 29 minutes and 466k tokens and found nothing new. Only 8 of the 16 sources behind the eventual findings were in its pool, at ranks 4, 10 and then 62–696.
- **A dedicated pass for subsuming results.** The passive slot was judged enough.
- **An accountability ledger** separate from the summary table. The table's Credited? column and the flags already are one.
- **A "what is new" summary, a "best reference" choice, a complete map of the literature, and an architecture pass of our own.** The preprint states its own contributions and structure; the review would do these poorly.
- **Flags from drafters to the persona, and repeated persona runs by default.** Flags prime the persona, and the extra machinery wasn't worth it.
- **Google Scholar "cited by".** There is no API, and it serves CAPTCHAs, which must not be bypassed.
- **The unauthenticated Semantic Scholar API.** It returns 429 almost immediately.

## Rules for the expert write-up

These rules came from review of the first two write-ups. Put them in every drafting, editing and fix brief, and check the PDF text against them.

- **Audience.** The readers are experts in the field who have not read the preprint and will only see the PDF. Every claim must be checkable at a glance: exact statements, compiled locators, and correspondences side by side, each in its own paper's notation.
- **Length follows the form of inclusion.** No author wants readers to wade through pages of related work before reaching the argument, and the same goes for this report. Draft full entries, since the persona check needs the full correspondences. After the check, a finding the author would cite with a sentence gets a one-page entry, not three pages.
- **Say plainly that the citation is missing.** That is the point of every entry. The Summary's first two sentences say what the earlier work is, and that the preprint doesn't cite it for this content (or cites it only for something else, or only elsewhere). Describe the mathematics with verbs matched to the relationship ("follows", "adapts", "uses one step of", "carries out the route proposed in", "was first proved in"), but never let that wording soften or bury the missing citation.
- **No hedging.** A claim that doesn't hold is dropped, not qualified. Facts that help an expert place the relationship are content, stated with locators. For example: the source itself calls the device standard, or credits a third paper.
  - No separate "citation status" paragraph: the Summary states it.
  - No asides, and no calibration section of things examined and found fine.
  - No section/page map.
- **No tutorial expansion of the earlier technique.** State it precisely, in the source's notation, with locators. Agents don't write good explanations for learners. Readers learn the shared structure from the precise correspondences.
- **No process notes,** apart from the Provenance paragraph. That means:
  - no history of the finding ("reclassified", "originally a fragment");
  - no agents, reports, library, review passes, votes or searches;
  - no "not consulted" and no unreproducible checks.

  State citation facts as facts about the preprint. Omit anything you could not verify rather than printing "[not verified]".
- **Locators.**
  - Cite the preprint and companions by compiled numbering only: section, equation, theorem, page. `\ploc{compiled}{file:line}` prints only its first argument. Don't wrap it in extra parentheses: write `\ploc{(5.27), p.~39}`, not `\ploc{((5.27), p.~39)}`.
  - TeX file names, line numbers and labels never appear in the PDF.
  - Source pages are printed page numbers. Check each source for an offset from the PDF index.
  - Refer to the preprint's references by author name, never by its reference numbers.
- **Names of works.** Refer to works by their authors' names or initials, as for any citation. When two cited works share an author list, give the full names and keep an initialism for at most one of them.
- **Titles** name the technique or result, never the earlier works; that list can get long. The works go in the summary table's Credited? column.
- **Headings are a menu, not a requirement:** Summary, Setup, Role in the argument, The earlier technique (or result), Correspondence, Differences, How to check. Leave out any that don't apply, and reorder where that reads better. A short entry usually needs only Summary, Correspondence and How to check. "Differences" lists only local, checkable differences from the earlier work, not the preprint's contributions in general.
- **Lists and tables.**
  - Lists without options.
  - Tables in `xltabular` with booktabs rules, a repeated header (`\endfirsthead`/`\endhead`) and `\addlinespace` after every row.
  - No numbered table captions.
- **Title, order and summary.**
  - The document is titled "Missing citations in “⟨preprint title⟩”".
  - Findings go by magnitude (see Scope), numbered F1, F2, … in one Findings section. Their headings carry no LaTeX section number, so an ID never sits next to another number.
  - A summary table at the top has the columns ID | Relationship | Centrality | Technique or result | In the preprint | Credited?.
  - Credited? names the earlier works in the same "Authors Year" form as the README's "Earlier work" column, with `\cite`, then what the preprint cites ("Fan--Mei--Montanari 2018 \cite{…}: not cited"), then the flags `\attrgap` and `\overstated` where they apply.
- **Provenance.** About ends with a short Provenance paragraph, and the README ends with a one-line version. It says that the document was generated by LLM agents (name the model) running the `precedence-review` skill (repository and commit), "makes no claim of completeness, and has not been vetted by a human", and who ran the job. Operator inputs that shaped a finding get one clause ("who also supplied the leads behind finding F4"). The operator may add their own disclosure. Nothing else about the process goes there.

## Working with the user

- **Status.**
  - After each section hand-back, send a few lines: what was found, its relationship, and what is still running.
  - For a batch of parallel agents, send one summary when the batch is in, not a line per arrival. The user said they don't need verdicts as they come in.
  - Keep a running total of findings and subagent tokens.
- **Decisions.** Ask as numbered options with your recommendation. While a decision is pending, keep running the work it doesn't affect.
- **Brevity about process.** Keep explanations of process short, in chat and in the document. The user notices overexplaining.
- **Lean fixes.** When something goes wrong, prefer the simplest change. The user rejected an elaborate flag-routing design as "overengineered".
- **Copy-paste summaries.** When asked for a summary to copy and paste, use a nested list rather than a table.
- **Multi-part approvals.** A "yes" to a multi-part proposal does not approve every part, especially a part the user then qualifies. If unsure, ask about that part.
- **State your reading of an ambiguous request** when you act on it, so a misreading costs one message.
- **The user's own papers.** If a source is co-authored by the user, apply the same criteria, and keep authorship out of the briefs and the document. There is no presumption of impartiality, any more than in a survey that cites its author. Mention it to the user once.
- **Memory.** Record the user's rules, corrections and design decisions in memory if the environment has it. Don't record speculative design ideas unless asked.
- **Privacy.** Never put the user's email or other identifying information in API requests, User-Agent strings or `mailto` parameters.
- **Files under review.** Don't change a file that running subagents are reading or editing, such as the PDF under check or a fragment being revised. Edit the build copy, and publish after they finish.
- **Relaunching agents.** Before relaunching one that seems to have failed, check that it really ended (its notification), and give each launch its own output file. In the second run, a run presumed dead finished after its relaunch, and the two would have written the same file.
- **Long-running checks.** Keep verification commands light, with explicit timeouts. A `du -sh` over a large clone stalls.
- **Git.** Commit and push only in the publish step's pull request, after asking, or when the user asks. Never commit `prior-work/` or `reviews/`.

## Environment pitfalls

These caused most of the retries in the first two runs, mostly on Windows with Git Bash. Paste the "Tool pitfalls" block from `references/environment.md` into every subagent prompt, adapted to the platform. The worst ones:
- **Backslashes.** The Bash tool can turn `\\` into `\`, even inside single quotes and quoted heredocs. That silently corrupts LaTeX, so edit `.tex` files only with Edit or Write, and write scripts to files before running them.
- **Python output encoding.** Python output can crash on a non-UTF-8 console, and `PYTHONIOENCODING` is ignored under `python -I`. Run `python3 -I -X utf8`, or call `sys.stdout.reconfigure(encoding="utf-8")`. Use `python` only where `python3` doesn't exist.
- **arXiv over plain http** returns an empty 301 with no error. Use `curl -sSL https://export.arxiv.org/...`, spaced 3–5 s apart. Look up the version before fetching.
- **MSYS paths.** MSYS rewrites Windows paths and arguments starting with `/`. Run pdflatex from inside its build directory with relative names, pass sparse-checkout patterns through `--stdin`, and use scratch subfolders rather than `/tmp`.
- **Partial clones.** In a blobless clone, `git ls-tree -l`, `git grep <rev>` and `git log -p` download every blob, which stalled the second run for minutes. Agents don't need git at all.

## Bundled files

| File | Purpose |
|---|---|
| `scripts/fetch_arxiv.sh` | Fetch an arXiv paper (PDF, text, safely extracted LaTeX source) into `prior-work/`. Copy it to `prior-work/tools/`. Needs `python3` (3.9 or later) to unpack sources. It exits 1 if anything failed, and nothing partial is left behind. |
| `scripts/merge_library.py` | Seed `prior-work/` from a library kept elsewhere: copy papers without overwriting, and merge INDEX rows tagged with their origin. |
| `scripts/pagefind.py` | Find the compiled page of a phrase in a pdftotext file, or print a page. |
| `scripts/fragment_test.sh` | Test-compile one write-up fragment in a scratch folder and check its PDF text. It exits 0 only on `result: PASS`. |
| `scripts/make_bib.py` | Generate `parts/bibliography.tex` from the cited keys, in reading order. |
| `scripts/build.sh` | Build the whole write-up: bibliography, 3 pdflatex passes, QA gates. It exits 0 only on `result: PASS`. |
| `scripts/print_summaries.py` | Print each finding's ID (from the last build), slug, title and Summary, in document order. |
| `scripts/forbidden-patterns.txt`, `scripts/warning-patterns.txt` | Patterns that fail the build, or are only printed for review, when found in the PDF text. Shared by `build.sh` and `fragment_test.sh`. |
| `scripts/flatten_tex.py` | Inline every `\input` into one standalone `.tex` for publishing. |
| `scripts/publish_prep.sh` | Flatten, compile the flat file, check that its text matches the build, copy the deliverables into the preprint folder, and validate the JSON. |
| `scripts/precedence_stats.py` | Validate `precedence-findings.json` and write `precedence-stats.json`. |
| `assets/` | Templates: INDEX, FINDINGS, TIMING, write-up preamble/main/about/summary, example JSON, README. |
