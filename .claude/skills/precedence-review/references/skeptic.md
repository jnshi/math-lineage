# Author-persona check and applying its verdicts

## Why this framing
An adversarial skeptic tends to argue findings away. A defensive author tends to reject everything. This pass uses the preprint's *honorable* author instead. That author wants to know whether each claim is true, is glad to be reminded of a source they forgot to cite, and rejects claims that are untrue or contrived. This framing produced specific, checkable verdicts, and every finding of the first run came back accepted or partly accepted, each with concrete corrections.

The check runs on the finished write-up fragments, because those carry the exact correspondences it needs to test.

## Before launching
1. Build the full write-up and copy the PDF to `writeup/precedence-findings.pdf`. Dump its text to `writeup/build/full.txt`.
2. Leave both files untouched while the agents run. Make any interim fixes only in the build copy.
3. Create `reviews/<slug>/author-checks/`.

Launch one agent per finding, all in parallel, in the background. These agents only read; the one file each writes is its verdict.

## Brief
Save this to `<scratch>/author-check-brief.md`. Each agent's prompt is a one-line header followed by the brief, with `{ID}` and `{SLUG}` filled in. The ID is the printed one, from `print_summaries.py` after the last build. The header reads: "Today is {TODAY}. Your finding is **{ID}**, in file `findings/{SLUG}.tex`." Extend it by finding type:
- **For a (B) finding:** "It is a (B)-type finding: earlier, weaker results on the same problem."
- **For a structural finding:** "It is a structural finding: it claims that published results make part of your argument unnecessary. Treat it as feedback on a missed citation that would have shortened the paper. Check carefully whether the claimed implication really holds, including every hypothesis and normalization."

````text
## Your role
You are the author of the preprint "{TITLE}" ({DATE}). You are responding to a report that says your preprint is missing attributions. You are well-meaning, honorable, gracious and humble, and above all you value the collaborative effort of building the grand edifice of mathematics. So you approach each piece of feedback with curiosity, not defensiveness. You want to know whether it is really true. It is quite possible that you read the argument somewhere and forgot, or simply forgot to write down the attribution, and it would be a delight to be reminded. But, honorable as you are, you will also reject any attribution claim that simply isn't true, or is contrived or unrealistic, for the sake of truth and beauty. Respond accordingly.

## Materials
- **The report**, compiled: `{WRITEUP_DIR}/precedence-findings.pdf`, with its text in `{WRITEUP_DIR}/build/full.txt`.
- **Your finding's LaTeX source:** `{WRITEUP_DIR}/findings/{SLUG}.tex`. Read the whole finding, and the report's Section 1 ("About this document") for its definitions and grading rules.
- **Your preprint:** `{PREPRINT_DIR}`, with TeX in `build/sections/*.tex` and `paper.pdf`.
  - Compiled text with page breaks (`\f`; the page is 1 plus the number of `\f` before a match): `{SCRATCH}/paper.txt`.
  - In the report's source, `\ploc{compiled}{file:line}` gives the TeX location as its hidden second argument, which helps you find passages quickly.
- **Your companion preprints** (same release): {LIST}. Compiled text: {COMPANION TEXT FILES}.
- **The earlier works:** `{REPO}/prior-work/` (`src/<Key>/` LaTeX where available, `papers/<Key>.pdf`, `text/<Key>.txt`). Grep `INDEX.md` to map citation keys to files. **Do not download anything.** If a check needs a work that isn't there, say so in your response.
- Judge the finding on its own merits by reading the preprint and the sources yourself. Don't rely on any other review notes in the repository.

## What to do
1. **Check every factual claim in the finding** against the actual passages:
   - the preprint's statements and locators (compiled numbers and pages);
   - the earlier work's statements and locators;
   - the claimed correspondences and formulas, as transcribed;
   - the claimed citation facts: what your preprint does and does not cite, and where.
2. **Decide honestly, as the author:**
   - **Accept.** The earlier work really contains this, you used it, and your preprint doesn't credit it for this. Say precisely what attribution you would add, and where.
   - **Accept in part.** Say which part holds and which doesn't.
   - **Reject.** The claim is untrue, contrived or unrealistic. Valid reasons are specific ones:
     - your preprint already credits it at a location the report missed (give it);
     - the content is textbook material in exactly the form you used (name the textbook passage);
     - the correspondence fails at a specific step;
     - the earlier work postdates your preprint;
     - the "reused" content is generic calculus that no one would cite.
   - "It's only a small part" or "my version is more general" is not a reason to omit credit for what was reused. The report's own rule is that new ingredients don't lower the grade.
   - Also say whether the report's grade (Strong, Partial, or for a structural finding Major/Moderate) is fair, and whether its stated *reason* for the grade is right.
3. **Report write-up errors** in this finding: typos, grammar, wrong compiled locators or page numbers, mistranscribed formulas, wrong theorem numbers, notation inconsistencies, unclear or misleading sentences, and LaTeX rendering problems in the PDF. Give each its exact location (quote the text) and the correction.

{TOOL PITFALLS BLOCK}

## Output
- Write `{REVIEW_DIR}/author-checks/{ID}.md` with these parts:
  1. **Verdict:** one line, Accept / Accept in part / Reject, plus whether the grade is fair.
  2. **Author's response:** 1–3 paragraphs in your author's voice, specific and courteous.
  3. **Claim check:** a table of claim | holds? | note.
  4. **Write-up errata:** a numbered list of quote → correction. Write "none found" if there are none.
- **Edit nothing else.** Do not modify the report's files.
- Final message, under 120 words: the verdict, the grade assessment, the number of errata, and the single most important reason.
````

**As verdicts arrive,** give the user one line each: the verdict, the grade, the key reason, and "N of M in". When all are in, give a table (Finding | Verdict | Grade | Errata) and say what you'll change.

**What the first run's checks found:** grade reasons that broke the report's own rules (for example "it's inside a lemma whose main statement is new"); components that didn't hold; wrong transcriptions that omitted a hypothesis; formula definitions slightly off; leftover numbered captions; undefined grade labels; wrong bibliography titles. Expect this level of detail.

## Applying the verdicts
1. **Back up** all fragments to `writeup/findings/pre-check/`.
2. **Make the shared fixes yourself** before launching agents:
   - grade definitions missing from `about.tex`;
   - bibliography title corrections, in `prior-work/INDEX.md`, which is where the bibliography is generated from.
3. **Launch one agent per finding, in parallel.** Each prompt is short:
   - point to `<scratch>/apply-check-brief.md` (below);
   - give the ID, the slug and a private scratch subfolder;
   - include a **"Verdict to apply" block that you distil** from `author-checks/<slug>.md`: accept or accept in part, which grade stands, which components to drop, a reworded grade reason if needed, the key errata, and the errata count;
   - include the Tool-pitfalls block;
   - ask for a proposed replacement of this finding's summary-table cells if the claim changed.
4. **When they return:**
   - Apply the cross-file items they report yourself: bibliography working notes, mismatches with other fragments such as a sibling finding describing a dropped claim, and summary-table cells.
   - Rebuild and run the QA gates (`writeup.md`).
   - Grep the PDF text for the specific wording that was just removed.
   - Record the final verdicts at the top of `FINDINGS.md`.
   - Send the PDF.

### Brief for applying a verdict
````text
You are revising ONE finding (a LaTeX fragment) in a report for **human experts who will only read the PDF**. An independent check has just reviewed the finding, written from the point of view of the preprint's author. It produced (i) a verdict and (ii) a list of write-up errata. Your job is to make the fragment correct and consistent with what that check established. Today is {TODAY}.

## Files
- **Fragment to revise (edit in place; edit nothing else):** `{WRITEUP_DIR}/findings/<SLUG>.tex`. A backup is in `findings/pre-check/`. Keep its `\finding{…}{<SLUG>}` line, and never type a finding ID; refer to other findings with `\ref{f:<slug>}`.
- **The check:** `{REVIEW_DIR}/author-checks/<SLUG>.md`. Read it fully: the verdict, the author's response, the claim-check table and the errata list.
- **Shared notation and rules:** `{WRITEUP_DIR}/parts/overview.tex`, `parts/about.tex`, `parts/preamble.tex`.
- **For re-checking:** preprint TeX `{PREPRINT_DIR}/build/sections/`; compiled preprint text with `\f` page breaks `{SCRATCH}/paper.txt` plus the companion texts; sources in `{REPO}/prior-work/src/<Key>/` and `text/<Key>.txt`.

## What to do
1. **Apply every erratum that is correct.** Spot-check any erratum that changes mathematics or a locator against the source before applying it. If you judge an erratum wrong, skip it and say why in your final message. If an erratum concerns a file other than your fragment (bibliography, INDEX.md, about.tex, another finding), don't edit that file; report the exact change needed.
2. **Apply the verdict.** If the check accepted only part of the finding, or said the stated reason for the grade is wrong, revise the finding's claims, title, Summary, Correspondence and How-to-check so they assert only what holds. Drop rejected components from the claim; don't keep them as "also" items. Reword the grade reason in the Summary accordingly. Keep the grade the check found fair.
3. **Don't import the check's prose.** Don't add the author's response, a dialogue, "the author agrees", or any mention of the check, the review process or grade history. The fragment should simply be correct.
4. **Keep the house rules:**
   - **Headings,** exactly in this order: Summary, Setup, Role in the argument, The earlier technique (or The earlier result / The earlier results), Correspondence, What is new in the preprint, How to check. Structural findings keep their own adapted headings.
   - **No** caveats, no citation-status paragraph, no process notes and no tutorial expansions. (If an erratum suggests adding a caveat or footnote, skip it.)
   - **Locators:** only `\ploc{compiled}{file:line}` (compiled locators print; never print file names or labels), and `\sloc`/`\cite` for sources.
   - **Lists:** plain `itemize`/`enumerate` with no options.
   - **Tables:** `xltabular` inside `center` with `\small`, booktabs rules, and `\addlinespace` between rows. Don't number or caption tables ("Table 9"); refer to "the table below".
   - **Length:** don't make the finding longer than it is.
   - **Edit only with the Edit/Write tools.**
5. **Test-compile:** `bash "{SKILL}/scripts/fragment_test.sh" "{WRITEUP_DIR}/parts/preamble.tex" "{WRITEUP_DIR}/findings/<SLUG>.tex" "{SCRATCH}/fix-<SLUG>"`. It must end with `result: PASS`. Also remove any listed warning that isn't legitimate.

{TOOL PITFALLS BLOCK}

## Final message (under 120 words)
- The number of errata applied and skipped, with one-line reasons for any skipped (and any change needed outside your fragment).
- What changed in the finding's claim or grade reason.
- Confirmation that the fragment compiles.
- If the claim changed: proposed replacement cells for this finding's row in the summary table (Technique / In the preprint / Credited?).
````

**Bibliography working notes.** If a check flags notes in a bibliography entry, such as "author copy from …", "saved as …" or "text extraction garbled", don't strip them from `INDEX.md`. Agents use those notes. Rewrite such notes in INDEX.md, or in the fragment's `% BIB` line, as `[note: …]`. `make_bib.py` strips only `[note: …]` marks and URL clauses, and it lists every other wordy parenthetical it keeps, so check that list on every build.
