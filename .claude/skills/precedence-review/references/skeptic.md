# Author-persona check and applying its verdicts

## Why this framing
The check plays the preprint's author. An adversarial skeptic tends to argue findings away, and a defensive author tends to reject everything. At first the persona was an honorable author who would be glad to be reminded of a source they had read and forgotten. That framing asked only whether a credit was owed. In both runs it accepted or partly accepted every finding in the report, and it said nothing about how much space a finding deserved.

The user then reframed the persona around the review's real purpose. The author's values haven't changed; they just show up as two practical concerns. First and foremost, the author wants the manuscript to be understandable to experts. Second, they want to give due respect to work they built on. Every pointer also costs the reader attention, and no author wants a ten-page related-work section ahead of their own contribution. So the persona decides not just *whether* the earlier work deserves a pointer, but *in what form*. **The burden of proof is on inclusion.** The persona includes a pointer only if it can affirm specific reasons, and never has to justify leaving one out. In the second run, five independent runs of this brief gave the same form of inclusion for each of the two borderline findings.

Three more lessons from that run:
- **Keep the check blind.** A check told that a candidate had been withdrawn, and given the drafter's counterargument, agreed with the withdrawal. The user asked for the check to be redone without that priming. A check never sees review notes, earlier checks, retired fragments or the withdrawal history.
- **Don't give the persona a checklist.** A list of "valid reasons" anchors the persona and implies the list is complete. The run's most consequential objections were not on any list: the wrong earlier work credited, an object mismatch, statements that weren't nested, a wrongly described mechanism, and a stated reason contradicting the report's own definitions. All of them came from the open instruction to check every claim.
- **One run per finding.** Repeated runs with a pre-registered majority vote cost about 240k tokens per run, and are worth it only when the user asks for them.

The check runs on the finished write-up fragments, because those carry the exact correspondences it needs to test.

## Before launching
1. Build the full write-up and copy the PDF to `writeup/precedence-findings.pdf`. Dump its text to `writeup/build/full.txt`.
2. Leave both files, and the fragments, untouched while the agents run. Make any interim fixes only in the build copy.
3. Create `reviews/<slug>/author-checks/`.

Launch one agent per finding, all in parallel, in the background. These agents only read; the one file each writes is its verdict. When they are all in, give the user one table (Finding | Form of inclusion | Claims | Grade and proportion | Errata) and say what you'll change. Don't post a line per arrival.

## Brief
Save this to `<scratch>/author-check-brief.md`. Each agent's prompt is a short header followed by "Your full instructions are in `<scratch>/author-check-brief.md`. Read it completely first and follow it exactly." The header reads: "Today is {TODAY}. Your finding is **{ID}**, in file `findings/{SLUG}.tex`." Take the ID from `print_summaries.py` after the last build. Extend the header by finding type:
- **For a same-result or weaker-result finding:** "It concerns earlier results on the same problem."
- **For an overstated-novelty finding:** "Your preprint does cite this earlier work; the claim is that your abstract or framing presents the content as new. Judge that claim as a reader of your abstract would take it."
- **For a proposed-route finding:** "It concerns a proof route that an earlier paper proposed; judge whether a pointer for proposing that route earns its place."
- **For a subsuming-result finding:** "It claims that published results make part of your argument unnecessary. Check carefully whether the claimed implication really holds, including every hypothesis and normalization."
- **For a candidate that isn't in the report** (withdrawn by its drafter, or a late lead): state the claim inline, as the section pass first stated it, in the finding format (title, sources, your preprint's locations, correspondence, citation status, relationship and centrality). Correct factual details only. Don't mention that it was withdrawn or why, and don't point to any fragment.

````text
## Your role
You are the author of the preprint "{TITLE}" ({DATE}). You are responding to a report that says your preprint is missing attributions. You are well-meaning, honorable, gracious and humble, and above all you value the collaborative effort of building the grand edifice of mathematics.

Right now, that value shows up as two practical concerns about your manuscript. First and foremost, you want it to be as understandable as possible to experts. An expert reader should be able to see where each idea comes from, recognize familiar machinery as familiar, and know where to find its origins and fuller treatments. Second, you want to give due respect to the work you may have built on.

So you approach each piece of feedback with curiosity, not defensiveness. Would pointing to this earlier work help an expert understand your argument? Does it deserve acknowledgement as something you built on? And is the claim really true? Every pointer you add also costs your reader something: attention, and time spent away from what your paper itself contributes. No author wants readers to wade through pages of related work before reaching the argument. So ask not only whether a pointer would help an expert, but whether it earns its place, and in what form. You will also reject any attribution claim that isn't true, or is contrived or unrealistic. A false or strained attribution would mislead an expert reader about where an idea comes from and what it depends on. It would also give credit where none is due, which is no respect to anyone.

## Materials
- **The report**, compiled: `{WRITEUP_DIR}/precedence-findings.pdf`, with its text in `{WRITEUP_DIR}/build/full.txt`.
- **Your finding's LaTeX source:** `{WRITEUP_DIR}/findings/{SLUG}.tex` (or the finding given in your prompt). Read the whole finding, and the report's Section 1 ("About this document") for its definitions and grading rules.
- **Your preprint:** `{PREPRINT_DIR}`, with TeX in `build/sections/*.tex`, bibliography `{BIBLIOGRAPHY FILE}`, and the compiled `{PDF NAME}`.
  - Compiled text with page breaks (`\f`; the page is 1 plus the number of `\f` before a match): `{SCRATCH}/paper.txt`. {SAY WHETHER THE PDF PAGE INDEX EQUALS THE PRINTED PAGE NUMBER.}
  - In the report's source, `\ploc{compiled}{file:line}` gives the TeX location as its hidden second argument, which helps you find passages quickly.
- **Your companion preprints** (same release): {LIST, OR "none"}. Compiled text: {COMPANION TEXT FILES}.
- **The earlier works:** `{REPO}/prior-work/` (`src/<Key>/` LaTeX where available, `papers/<Key>.pdf`, `text/<Key>.txt`). Grep `INDEX.md` to map citation keys to files. **Do not download anything.** If a check needs a work that isn't there, say so in your response; if you rely on a textbook passage that isn't there, mark it as unverified. For source papers, cite printed page numbers; some PDFs have an offset between the PDF index and the printed number.
- Judge the finding on its own merits by reading the preprint and the sources yourself. **Don't open any other review notes in the repository:** not `FINDINGS.md`, the `NN-*.md` reports, `CONSOLIDATION.md`, anything under `{REVIEW_DIR}/author-checks/` other than the one file you write, or anything under `{WRITEUP_DIR}/findings/retired/` or the `findings/pre-*/` backups.

## What to do
1. **Check every factual claim in the finding** against the actual passages:
   - the preprint's statements and locators (compiled numbers and pages);
   - the earlier work's statements and locators;
   - the claimed correspondences and formulas, as transcribed;
   - the claimed citation facts: what your preprint does and does not cite, and where.
2. **Decide the form of inclusion**, as the author: what, if anything, you would add to your manuscript for this earlier work. Choose one:
   - **none**;
   - **a citation at the point of use** (a bare reference, no new prose);
   - **a clause or a sentence**;
   - **a short paragraph**.

   Choose anything other than "none" only if you can affirm, for specific reasons, that it helps an expert reader enough to be worth their attention, or that it is owed as acknowledgement of something you built on, and that the claims it rests on are true. If you cannot affirm that, the answer is "none". You do not need to show that omitting it is justified; it is enough to explain why inclusion is not affirmed. Say exactly where any addition would go.
3. **Judge the finding's claims:** Accept, Accept in part (say which parts hold and which don't), or Reject, each for specific reasons you can point to in the texts. "It's only a small part" or "my version is more general" doesn't make a reuse claim false. If the finding says your abstract or framing overstates novelty, judge whether a reader would reasonably take it that way.
4. **Judge the classification and proportion.** Say whether the report's relationship type and centrality are right under the report's own definitions (About), and whether its stated reasons are. Also say whether the space the report gives this finding (its length and weight) is proportionate to the form of inclusion you chose. If it isn't, say what length would be (e.g. one row in the summary table and a few lines, rather than three pages).
5. **Report write-up errors** in this finding: typos, grammar, wrong compiled locators or page numbers, mistranscribed formulas, wrong theorem numbers, notation inconsistencies, unclear or misleading sentences, and LaTeX rendering problems in the PDF. Give each its exact location (quote the text) and the correction.

{TOOL PITFALLS BLOCK, WITH THE SCRATCH SUBFOLDER `{SCRATCH}/check-{SLUG}/`}

## Output
- Write `{REVIEW_DIR}/author-checks/{SLUG}.md` with these parts:
  1. **Verdict:** three short lines: the form of inclusion (and where); Accept / Accept in part / Reject on the claims; whether the relationship and centrality are right and the space proportionate.
  2. **Author's response:** 1–3 paragraphs in your author's voice, specific and courteous.
  3. **Claim check:** a table of claim | holds? | note.
  4. **Write-up errata:** a numbered list of quote → correction. Write "none found" if there are none.
- **Edit nothing else.** Do not modify the report's files.
- Final message, under 120 words: the form of inclusion, the claims verdict, the classification and proportion assessment, the number of errata, and the single most important reason.
````

**What the checks found in the first two runs:**
- classification reasons that broke the report's own rules (for example "proves every step by its own arguments", a new-ingredients discount);
- components that didn't hold;
- a result attributed to the wrong paper;
- an object mismatch (the source controls a different matrix);
- wrong transcriptions that omitted a hypothesis or a subscript;
- mechanisms described wrongly;
- headerless table continuations;
- labels the report never defined;
- wrong bibliography titles.

Expect this level of detail.

**Repeated runs, only if the user asks.** Freeze the brief first: copy it to `author-checks/` with its sha256. Write the decision rules into `author-checks/PREREGISTRATION.md` before any result exists: the number of runs, majority thresholds, and what a failed run does (relaunch it identically; discard partial files unread). Give each run its own output file. Check progress by file names only, never by reading results early.

## Applying the verdicts
1. **Back up** all fragments to `writeup/findings/pre-check/`.
2. **Make the shared fixes yourself** before launching agents:
   - definitions missing from `about.tex`;
   - bibliography title corrections, in `prior-work/INDEX.md`, which is where the bibliography is generated from.
3. **A finding whose form of inclusion is "none"** leaves the document: delete its `\input` line, move the fragment to `findings/retired/`, remove references to it, and note the reason in `FINDINGS.md`. It stays in the JSON with `in_report: false`, so the record of the missing citation survives. A finding whose claims are rejected outright leaves both.
4. **Settle the order.** Apply any change of relationship or centrality the check found right, and move `\input` lines to keep the magnitude order. Tell the user if IDs changed.
5. **Launch one agent per remaining finding, in parallel.** Each prompt is short:
   - point to `<scratch>/apply-check-brief.md` (below);
   - give the ID, the slug and a private scratch subfolder;
   - include a **"Verdict to apply" block that you distil** from `author-checks/<slug>.md`: the form of inclusion and the resulting length, the relationship and centrality that stand, which components to drop, a reworded reason if needed, the key errata, and the errata count;
   - include the Tool-pitfalls block.
6. **When they return:**
   - Apply the cross-file items they report yourself: bibliography fixes, mismatches with other fragments such as a sibling finding describing a dropped claim, and summary-table cells.
   - Rebuild and run the QA gates (`writeup.md`).
   - Grep the PDF text for the specific wording that was just removed.
   - Record the final verdicts in `FINDINGS.md` under "Final verdicts".
   - Send the PDF.

### Brief for applying a verdict
````text
You are revising ONE finding (a LaTeX fragment) in a report for **human experts who will only read the PDF**. An independent check has just reviewed the finding, written from the point of view of the preprint's author. It produced (i) a verdict, including the form in which the author would point to the earlier work, and (ii) a list of write-up errata. Your job is to make the fragment correct, consistent with what that check established, and as long as it is worth to the reader. Today is {TODAY}.

## Files
- **Fragment to revise (edit in place; edit nothing else):** `{WRITEUP_DIR}/findings/<SLUG>.tex`. A backup is in `findings/pre-check/`. Keep its `\finding{…}{<SLUG>}` line, and never type a finding ID; refer to other findings with `\ref{f:<slug>}` (valid slugs: {ALL SLUGS}).
- **The check:** `{REVIEW_DIR}/author-checks/<SLUG>.md`. Read it fully: the verdict, the author's response, the claim-check table and the errata list.
- **Shared notation and rules:** `{WRITEUP_DIR}/parts/overview.tex`, `parts/about.tex`, `parts/preamble.tex`, and the drafting rules in `{SCRATCH}/writeup-brief.md`.
- **For re-checking:** preprint TeX `{PREPRINT_DIR}/build/sections/`; compiled preprint text with `\f` page breaks `{SCRATCH}/paper.txt` plus the companion texts; sources in `{REPO}/prior-work/src/<Key>/` and `text/<Key>.txt`.

## What to do
1. **Apply the errata that fix errors:** facts, mathematics, mistranscribed formulas or statements, wrong locators, pages, theorem or equation numbers, sentences that would mislead an expert, and rendering problems visible in the PDF. Skip pure style preferences (wording polish, optional renamings). Spot-check any erratum that changes mathematics or a locator against the source before applying it. If you judge an erratum wrong, skip it and say why in your final message. If an erratum concerns a file other than your fragment (bibliography, INDEX.md, about.tex, the summary table, another finding), don't edit that file; report the exact change needed.
2. **Apply the verdict** (see "Verdict to apply" in your prompt). If the check accepted only part of the finding, or found the relationship type or its stated reason wrong, revise the finding's claims, title, Summary, Correspondence and How-to-check so they assert only what holds. Drop rejected components from the claim; don't keep them as "also" items. Use the relationship and centrality given in your verdict block.
3. **Fit the length to the form of inclusion** given in your verdict block:
   - **a citation, clause or sentence:** rewrite as a **short entry of at most one page**, including the title: `\paragraph{Summary.}` (3–5 sentences: first the earlier work and that the preprint doesn't cite it for this content, or that its abstract or framing presents it as new; then what the preprint does and where, the correspondence with its locators, and the relationship with its reason); `\paragraph{Correspondence.}` (one table of at most 4 body rows, each side in its own notation); `\paragraph{How to check.}` (an `enumerate` of 2–3 side-by-side checks). Nothing else.
   - **a short paragraph:** keep a full entry, at most about 3 pages, using the headings that apply (Summary, Setup, Role in the argument, The earlier technique or result, Correspondence, Differences, How to check).
   Make a backup copy first if you rewrite.
4. **Don't import the check's prose.** Don't add the author's response, a dialogue, "the author agrees", proposed attribution sentences, or any mention of the check, the review process, votes or the finding's history. The fragment should simply be correct, and should still say plainly that the citation is missing.
5. **Keep the house rules** in `writeup-brief.md`: no hedges, no citation-status paragraph, no process notes, no tutorial expansions; locators only via `\ploc{compiled}{file:line}` (without extra parentheses) and `\sloc`/`\cite`, with printed pages for sources; plain lists; `xltabular` tables with booktabs rules, a repeated header and `\addlinespace` between rows; no numbered captions; works named by their authors' names or initials; titles that name the technique, not the works. **Edit only with the Edit/Write tools.**
6. **Test-compile:** from inside `{WRITEUP_DIR}`, run `bash "{SKILL}/scripts/fragment_test.sh" parts/preamble.tex findings/<SLUG>.tex "{SCRATCH}/fix-<SLUG>"`. It must end with `result: PASS`, and a short entry must be one page. Also remove any listed warning that isn't legitimate.

{TOOL PITFALLS BLOCK}

## Final message (under 120 words)
- The page count, and the number of errata applied and skipped, with one-line reasons for any skipped (and any change needed outside your fragment).
- What changed in the finding's claim, relationship reason or length.
- Confirmation that the fragment compiles.
- Proposed cells for this finding's row in the summary table (Technique or result / In the preprint / Credited?), if any changed.
````

**Bibliography working notes.** If a check flags notes in a bibliography entry, such as "author copy from …", "saved as …" or "text extraction garbled", don't strip them from `INDEX.md`. Agents use those notes. Rewrite such notes in INDEX.md, or in the fragment's `% BIB` line, as `[note: …]`. `make_bib.py` strips only `[note: …]` marks and URL clauses, and it lists every other wordy parenthetical it keeps, so check that list on every build.
