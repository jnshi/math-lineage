# Scope and grading

Read this before writing any brief, and paste the relevant parts into each one. Most of these rules were corrections to a first attempt, so each one fixes a real failure.

## The scope, verbatim
> "I'm not looking for related work citations that could be omitted as judgment calls. Only direct precedence of partial progress on the same problem and more importantly unattributed reuse of techniques or theory developed in earlier papers."

Quote it verbatim in section briefs. Agents calibrate better against a concrete sentence than against a paraphrase.

## Categories
- **(A) Unattributed reuse: the main target.** An argument, construction, identity, estimate or body of theory used in the preprint was developed in an identifiable earlier paper, and the preprint does not attribute it there. This covers two cases: no citation at all, and a citation that covers something else, or something narrower than what is reused. A finding names the specific earlier source with an exact locator, and shows the correspondence concretely (their statement or equation next to the preprint's).
- **(B) Same-problem precedence.** Earlier, uncited partial progress on the same problem: a weaker, special-case or less general version of a statement the preprint proves, or earlier results on the paper's central question. **Only the introduction-section pass looks for (B).** Later section agents don't search for it, though they may record a (B) item they run into.
- **(C) Structural.** An existing published result would replace or substantially shorten a large part of the argument (several pages, a lemma chain, a whole route, or a main-theorem component). It also covers the case where such a result contradicts a claim of necessity or novelty.
  - **Graded by impact:** **Major** (a route, a section or a main-theorem component becomes a citation) or **Moderate** (a multi-page lemma chain becomes a citation).
  - **Passive slot only.** Agents list a (C) item under a "(C) Structural (noted)" heading only if they come across one, and omit the heading otherwise.
  - **Entry fields:**
    - the paper span;
    - the published result and its locator;
    - what becomes a corollary or citation;
    - what checking the application would need.
  - **No dedicated structural pass.** The passive slot is enough, and a dedicated pass was explicitly rejected.
  - **The coordinator checks every (C) claim itself,** in the library sources, before recording it.

## Never report
- Related work whose omission is a judgment call: background, parallel approaches, other results in the area.
- Generic textbook or folklore tools. The exception is when the *specific way they are combined* traces to an identifiable paper.
  - In each section brief, name the textbook tools typical of that section's area so agents don't report them.
  - Examples from a probability/spin-glass paper:
    - semicircle law, edge rigidity, Stieltjes-transform bounds;
    - the bare Kac–Rice formula, and conditioning a GOE on linear constraints;
    - Weyl interlacing, BBP rank-one formulas, Schur complements, Sherman–Morrison;
    - Haar measure basics, coarea, Wick/Isserlis, Gaussian integration by parts;
    - Itô calculus, Doob, Markov/Chebyshev, Grönwall, nets and union bounds;
    - tensorization and the chain rule for entropy, Pinsker, Prékopa–Leindler;
    - spectral gap → mixing, LSI → hypercontractivity → mixing.
- "Cite the original rather than the later source" quibbles, when a cited source genuinely covers the content. That includes a cited source that itself credits the original.
- Physics heuristics or numerics, as findings. A rigorous reuse of a *specific* expansion first derived in physics can still be (A).
- Anything public on or after the preprint's date. "Earlier" means publicly available before it.

## Companion preprints
Preprints from the same release that the paper cites are **not prior literature**. Use them for two things only:
- to understand inputs the preprint imports;
- for the specific-content rule below. A companion that re-proves the same lemma often names the external source; this was the richest source of leads.

A companion re-running another companion's argument is not reportable.

## Grades for (A) and (B)
This rubric replaced an earlier one that graded against the whole argument. Under that rubric, a named technique reused intact (Polchinski renormalization) came out Partial merely because the preprint added new ingredients.
- **Strong:** a technique, construction or body of theory from an identifiable earlier paper is reused essentially intact without credit for that content.
  - This holds even when the preprint combines it with new ingredients or applies it in a new setting.
  - It holds especially when the technique has a recognizable name. Put the name in the finding's title.
  - New ingredients go under "What is new" and do not lower the grade.
- **Partial:** only a fragment of the earlier technique is reused, or the credit is present but only indirectly.
- **Grade by how completely the earlier technique itself is reused,** never against the size of the preprint's argument. "It's only a small part of our proof" is not a reason to downgrade.
- **"Fragment" means a fragment of the technique.** A reused headline idea without its downstream machinery is still the technique. What the preprint adds goes under differences.

## The specific-content rule
Indirect credit counts **only** when the preprint cites a source, or a companion, *for that specific content*, and the cited location itself covers or credits the original. Worked cases from the run:
- **Partial (indirect credit).** The preprint imports an inequality as "Lemma 8.1 of companion AG", and the section containing AG's Lemma 8.1 opens by crediting Wang's method.
- **Strong.** The same large-field mechanism is used elsewhere in the preprint with no citation at that location. Indirect credit at one location does not carry over to another.
- **Not credit for the criterion.** A paper is cited in the same proof, but only for its Lemma 4, the last step. That does not credit the capacity–measure criterion that the rest of the proof runs.
- **Not credit.** Du–Huang is cited in the same paragraph for its Theorem 1.6, while the content reused is from their §4.
- **Companion credit doesn't transfer.** The preprint says its estimates "are proved below" and re-proves them, while the companion's parallel proof credits the source. Re-proved content gets nothing from the companion's credit.

## Verifying a finding
- **Never report from a title or abstract.** Download the paper into the library, read the specific passage, and compare statements and proofs side by side. Give exact locators: theorem or equation number plus page in the stated version.
- **Never invent** citations, theorem numbers, quotes or formulas. If unsure, say so to the coordinator. In the write-up, leave the claim out.
- **Check hidden credit before calling anything uncited.** Grep the whole preprint, including all sections, the bibliography, captions and footnotes, for:
  - the source's author names, with accent and spelling variants;
  - its bib key;
  - the technique's name.

## The caveat test
The single test for any reservation about a finding: **"does this mean that the preprint is justified in omitting the citation?"**
- **If yes:** the finding is weaker or fails, so change the grade or withdraw it.
- **If no:** the reservation is not worth the reader's time, so drop it.

Either way, the write-up contains no caveats. Typical reasons that do pass the test:
- the preprint credits the source after all (give the location);
- the content is textbook in exactly the form used (name the textbook passage);
- the correspondence fails at a specific step;
- the source postdates the preprint;
- the "reused" content is generic calculus no one would cite.

"My version is more general" does not pass.

## Finding IDs
- **During the section passes:** `§N-A1`, `§N-B1`.
- **In the write-up:**
  - `S1…` for Strong;
  - `P1…` for Partial, including (B), shown as "Partial (B)";
  - `C1…` for Structural, shown as "Major (C)".
- **Within each category,** order by reading order, by significance, or a mix.
