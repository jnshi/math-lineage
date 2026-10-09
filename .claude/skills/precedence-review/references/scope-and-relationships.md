# Scope, relationships and credit

Read this before writing any brief, and paste the relevant parts into each one. Most of these rules were corrections to an earlier attempt, so each one fixes a real failure.

## The purpose, and the scope sentence for briefs
The review is for expert readers first. It shows them where the preprint's load-bearing ideas come from when the preprint doesn't cite the source there. Accountability for missing citations comes second, but the missing citation is the point of every entry, and the write-up says so plainly.

Put this sentence in every section brief:

> "Find the load-bearing techniques, constructions and results in this section that trace to an identifiable earlier paper, where an expert reading the preprint wouldn't find the pointer: nothing is cited for them at the point of use, or what is cited covers something else or something narrower. Also record earlier progress on the same problem that the preprint doesn't cite. Whether a pointer earns its place in the report is decided later; your job is to find and verify."

Agents calibrate better against a concrete sentence than against a paraphrase.

## What a finding is
A finding is a load-bearing part of the preprint (a technique, construction, identity, estimate, proof route or result) that an identifiable earlier paper already contains, where the preprint doesn't cite that paper for it at the place it is used. A finding names the earlier source with an exact locator, and shows the correspondence concretely: their statement or equation next to the preprint's.

**The one exception is overstated novelty** (see Flags): content the preprint *does* cite, but which its abstract or framing presents as new.

## Relationships
Each finding has one relationship type. It describes the mathematics, regardless of citations. Choose the closest type that holds.

| Type | Meaning |
|---|---|
| same technique | The earlier technique, construction or theory is reused essentially intact, possibly in a new setting or with new ingredients around it. |
| adapted | The earlier technique's structure is followed, with a change at its core: a different object, or a key step replaced. |
| fragment | One identifiable piece of the earlier technique is reused. |
| same route | An earlier paper proposed the proof strategy, even heuristically, and the preprint carries it out. |
| same result | An earlier paper proves essentially the same statement. |
| weaker result | An earlier paper proves a weaker, special-case or partial-range version of a statement the preprint proves. |
| subsuming result | A published result would replace or substantially shorten a large part of the argument. |

Choosing between neighbours:
- **Same technique, not adapted, when the change is around the technique rather than in it.** New ingredients, a new setting, or a combination with other tools leave the technique intact. List them under "Differences". This replaced a first-run rubric under which a named technique reused intact (Polchinski renormalization) came out weaker merely because the preprint added new ingredients.
- **"Fragment" means a fragment of the technique.** A reused headline idea without its downstream machinery is still the technique. "It's only a small part of our proof" is a matter of centrality, not of relationship.
- **Same route** covers an earlier paper's proposed strategy, even a heuristic sketch. In the second run the user chose to report such a case (an earlier paper's §2 sketching the whole route), against the coordinator's recommendation to leave it out.
- **Weaker result** stays a candidate even when a later, cited result implies it. In the second run a drafter withdrew such a result as "strictly weaker than a cited result"; the user reinstated it, and five independent author checks all said the preprint should cite it in one sentence. Check the dates of the cited works, and which of their theorems actually implies the earlier result.
- **Subsuming result** is a passive slot: agents note one under a "Subsuming result (noted)" heading only if they come across it, with the paper span, the published result and its locator, what becomes a citation, and what checking it would need. There is no dedicated pass for it; one was explicitly rejected. **The coordinator checks every subsuming-result claim itself,** in the library sources, before recording it.

## Centrality (best-effort)
Centrality is a glanceable flag for the reader, so they don't have to trace dependencies themselves. It is proposed at consolidation, assigned by the coordinator, and labelled best-effort:
- **main result:** the earlier work covers the main result itself, or most of it, not just a step in its proof;
- **central:** the main theorem's proof runs through it;
- **supporting:** it is an input to a central step;
- **peripheral:** an extension, a side result, a remark, or one of several interchangeable inputs.

A **weaker result** takes the centrality of the statement it precedes, but is never "main result": the preprint still goes well beyond it. Each entry states the dependency chain that justifies its centrality, in the preprint's compiled numbering: "Lemma 5.6 → Prop. 5.1 → Thm. 1.1". The chain is the checkable part; the label is a judgment.

## Credit status and the specific-content rule
For each earlier work in a finding, the credit status says what the preprint cites for this content:
- **not cited:** the work is not in the bibliography;
- **cited for other content:** in the bibliography, but not cited for this content;
- **credited elsewhere:** cited for this content at other locations, but not where it is used;
- **credited in part:** cited for part of this content only;
- **credited:** cited for this content. Allowed only in a finding with overstated novelty.

**Content the preprint credits where it is used is not a finding,** unless its novelty is overstated. That includes credit through a cited location that itself credits the work, such as a companion lemma: the reader reaches the source in one hop.

**The specific-content rule.** A citation counts only when it is *for that specific content*. Worked cases:
- **Credited, not reported.** The preprint imports an inequality as "Lemma 8.1 of companion AG", and the section containing AG's Lemma 8.1 opens by crediting Wang's method.
- **Credited elsewhere.** The same mechanism is used elsewhere in the preprint with no citation at that location. Credit at one location does not carry over to another.
- **Cited for other content.** A paper is cited in the same proof, but only for its Lemma 4, the last step. That does not credit the capacity–measure criterion that the rest of the proof runs. Likewise, Du–Huang cited in the same paragraph for its Theorem 1.6, while the content used is from their §4.
- **A method citation covers the method.** "We adapt the signed two-spin method of [W]" covers that method's own lemmas, but not a different device from the same paper.
- **A parallel use is not credit at the point of use.** "X, Y and Z are also combined in the method of [EAMS]", in the introduction, doesn't credit the specific constructions where they are used later: credited elsewhere at most.
- **Companion credit doesn't transfer to re-proved content.** The preprint says its estimates "are proved below" and re-proves them, while the companion's parallel proof credits the source.

## Flags
- **Attribution gap.** Set when the relationship is same technique, adapted, same route or same result; the centrality is main result, central or supporting; and the preprint cites none of the finding's earlier works for this content anywhere (each is not cited, or cited for other content). It follows from the other fields, and the validator recomputes it.
- **Overstated novelty.** Set when the preprint cites the earlier work for this content, but its abstract, a statement of its contributions, or the framing of a main result presents the content as new. That covers implicit overstatement too: what matters is how a reader would reasonably take it, not whether the word "new" appears. A typical case: two cited papers together give the main theorem, the introduction says so in passing, and the abstract presents the theorem as the preprint's own. Record where the claim is made (`novelty_claim`). Without a citation, the case is an ordinary finding instead (and often an attribution gap).

## Who decides inclusion
Section agents find and verify. Drafters write at the assigned relationship and centrality. **The author-persona check decides** whether a finding earns a place in the report, and in what form, weighing what the pointer gives an expert reader against what it costs them in attention (`skeptic.md`). A finding it judges not worth a pointer stays in the JSON only. Before that point, don't drop a verified candidate on a judgment call, such as:
- "superseded by later cited work";
- "only a standard device";
- "only a fragment";
- "related work rather than reuse".

Record the facts that bear on it instead: the dates, what the source itself says about the device, and which cited work covers what. Stop early only for a defect that makes the claim false: the correspondence fails at a specific step, the source postdates the preprint, or the preprint credits the content where it is used after all (and doesn't overstate it).

## Not reported
- **Generic textbook or folklore tools in their textbook form.** The exception is when the *specific way they are combined* traces to an identifiable paper.
  - In each section brief, name the generic tools typical of that section's area, so agents don't spend time on them. **Name only single tools, never machinery at the level of a combination.** An agent told that a combination's ingredients are textbook tends to rule the combination generic too, even when it traces to a specific paper.
  - Examples of single tools, from probability and spin-glass papers:
    - semicircle law, edge rigidity, Stieltjes-transform bounds;
    - the bare Kac–Rice formula, and conditioning a GOE on linear constraints;
    - Weyl interlacing, BBP rank-one formulas, Schur complements, Sherman–Morrison;
    - Haar measure basics, coarea, Wick/Isserlis, Gaussian integration by parts;
    - Itô calculus, Doob, Markov/Chebyshev, Grönwall;
    - tensorization and the chain rule for entropy, Pinsker, Prékopa–Leindler;
    - spectral gap → mixing, LSI → hypercontractivity → mixing.
- **"Cite the original rather than the later source" quibbles,** when a cited source genuinely covers the content. That includes a cited source that itself credits the original.
- **Physics heuristics or numerics, as findings.** A rigorous reuse of a *specific* expansion first derived in physics can still be a finding.
- **Anything public on or after the preprint's date.** "Earlier" means publicly available before it, and a same-day posting doesn't count.
- **Parallels:** an earlier paper doing the analogous thing in another setting, with nothing to suggest the preprint drew on it. A verified parallel can go in one sentence inside an entry when it helps place it.

## Companion preprints
Preprints from the same release that the paper cites are **not earlier work** here. Use them for two things only:
- to understand inputs the preprint imports;
- for the specific-content rule. A companion that re-proves the same lemma often names the external source; in the first run, this was the richest source of leads.

A companion re-running another companion's argument is not reportable. Many preprints have no companions; then the credit map and every companion clause are dropped.

## Verifying a finding
- **Never report from a title or abstract.** Download the paper into the library, read the specific passage, and compare statements and proofs side by side. Give exact locators: theorem or equation number plus the *printed* page in the stated version.
- **Never invent** citations, theorem numbers, quotes or formulas. If unsure, say so to the coordinator. In the write-up, leave the claim out.
- **Check hidden credit before calling anything uncited.** Grep the whole preprint, including the abstract, all sections, the bibliography, captions and footnotes, for:
  - the source's author names, with accent and spelling variants;
  - its bib key;
  - the technique's name.
- **Read the abstract and the contribution statements against the findings.** If one presents as new what a cited earlier work covers, that is overstated novelty.
- **Record what the source says about itself.** If the source calls the device standard, or credits a third paper for it, note that with its locator. It is content an expert reader wants, and it matters to the persona check.

## Order and IDs
- **During the section passes:** `§N-1`, `§N-2`, … in the reports and in FINDINGS.md.
- **In the write-up,** findings are ordered by magnitude and numbered F1, F2, … by LaTeX:
  1. centrality: main result, central, supporting, peripheral;
  2. then the relationship, closest first: same result, subsuming result, same technique, adapted, same route, fragment, weaker result;
  3. then reading order.
- The finding headings carry no section number, so an ID never sits next to a different LaTeX number ("3.2 F2").
- Reordering renumbers. If the user is already reading a draft, tell them when IDs change.
