# Scope, relationships and credit

Read this before writing any brief, and paste the relevant parts into each one. `assets/about.tex` has the same definitions as readers see them; keep the two in step.

## The purpose, and the scope sentence for briefs
The review is for expert readers first. It shows them where parts of the preprint come from when the preprint doesn't cite the source there. Accountability for missing citations comes second, but the missing citation is the point of every entry, and the write-up says so plainly.

The section brief template carries this sentence; keep it verbatim:

> "Find the load-bearing techniques, constructions and results in this section that trace to an identifiable earlier paper, where an expert reading the preprint wouldn't find the pointer: nothing is cited for them at the point of use, or what is cited covers something else or something narrower. Also record earlier progress on the same problem that the preprint doesn't cite. Whether a pointer earns its place in the report is decided later; your job is to find and verify."

"Load-bearing" means used in the preprint's arguments, not only mentioned as background.

## What a finding is
A finding is a technique, construction, identity, estimate, proof route or result that the preprint uses in its arguments, which an identifiable earlier paper already contains, where the preprint doesn't cite that paper for it at the place it is used. A finding names the earlier source with an exact locator, and shows the correspondence concretely: their statement or equation next to the preprint's.

**The one exception is overstated novelty** (see Flags): content the preprint *does* cite, but which its abstract or framing presents as new.

## Relationships
Each finding has one relationship type. It describes the mathematics, regardless of citations. If several fit, choose the first that holds in this order: same result, same technique, adapted, proof shortcut, same route, fragment, weaker result.

| Type | Meaning |
|---|---|
| same technique | The earlier technique, construction or theory is reused essentially intact, possibly in a new setting or with new ingredients around it. |
| adapted | The earlier technique's structure is followed, with a change at its core: a different object, or a key step replaced. |
| fragment | One identifiable piece of the earlier technique is reused. |
| same route | An earlier paper proposed the proof strategy, even heuristically, and the preprint carries it out. |
| same result | An earlier paper, or several earlier papers together, prove essentially the same statement. |
| weaker result | An earlier paper proves a weaker, special-case or partial-range version of a statement the preprint proves. |
| proof shortcut | A published result would replace or substantially shorten a large part of the argument. |

Choosing between neighbours:
- **Same technique, not adapted, when the change is around the technique rather than in it.** New ingredients, a new setting, or a combination with other tools leave the technique intact; list them under "Differences".
- **"Fragment" means a fragment of the technique.** A reused headline idea without its downstream machinery is still the technique. "It's only a small part of our proof" is a matter of centrality, not of relationship.
- **Same route** covers an earlier paper's proposed strategy, even a heuristic sketch.
- **Same result, not proof shortcut, when earlier work covers the statement itself,** even split across several papers that need only a short combination. A proof shortcut makes part of the argument unnecessary without covering the statement.
- **Weaker result** stays a candidate even when a later, cited result implies it. Check the dates of the cited works, and which of their theorems actually implies the earlier result.
- **Proof shortcut:** agents record one under a "Proof shortcuts (noted)" heading only if they come across it, with the paper span, the published result and its locator, what becomes a citation, and what checking it would need. No pass searches for these. **The coordinator checks every proof-shortcut claim itself,** in the library sources; every verified one goes on to drafting.

## Centrality (best-effort)
Centrality is a quick label for the reader: how much of the preprint's main argument depends on the finding. It is a judgment, not a checklist. The coordinator assigns it, starting from the proposal made at consolidation.
- **main result:** reserved for earlier work that covers the main result itself, or most of it;
- **central**, **supporting**, **peripheral:** decreasing dependence of the main argument on the finding.

A **weaker result** is never main result. Each entry states the chain of results the finding feeds, in the preprint's compiled numbering ("Lemma 5.6 → Prop. 5.1 → Thm. 1.1"), so a reader can see the basis for the label.

## Credit status and the specific-content rule
For each earlier work in a finding, the credit status says what the preprint cites for this content:
- **not cited:** the work is not in the bibliography;
- **cited for other content:** in the bibliography, but not cited for this content;
- **credited elsewhere:** cited for this content at other locations, but not where it is used;
- **credited in part:** cited for part of this content only;
- **credited:** cited for this content. Allowed only in a finding with overstated novelty.

**Content the preprint credits where it is used is not a finding,** unless its novelty is overstated. That includes credit through a cited location that itself credits the work, such as a companion lemma: the reader reaches the source in one hop.

List the **principal** earlier work first in each finding: the one the content mainly comes from. The attribution-gap flag looks at it.

**The specific-content rule.** A citation counts only when it is *for that specific content*. Worked cases:
- **Credited, not reported.** The preprint imports an inequality as a cited lemma of a companion, and the companion's section with that lemma opens by crediting the earlier method.
- **Credited elsewhere.** The same mechanism is cited at one place in the preprint and used without a citation at another. Credit at one location does not carry over to another.
- **Cited for other content.** A paper is cited in the same proof, but only for its last step, which doesn't credit the criterion the rest of the proof runs. Likewise, a paper cited in the same paragraph for its Theorem 1.6, while the content used is from its §4.
- **A method citation covers the method.** "We adapt the method of [X]" covers that method's own lemmas, but not a different device from the same paper.
- **A mention elsewhere is not credit at the point of use.** An introduction saying "these tools are also combined in [X]" doesn't credit the specific constructions where they are used later: credited elsewhere at most.
- **Companion credit doesn't transfer to re-proved content.** The preprint says its estimates "are proved below" and re-proves them, while the companion's parallel proof credits the source.

## Flags
- **Attribution gap.** Set when the relationship is same technique, adapted or same result; the centrality is main result, central or supporting; and the principal earlier work is not cited for this content anywhere (not cited, or cited for other content). It follows from the other fields, and the validator recomputes it.
- **Overstated novelty.** Set when the preprint cites the earlier work for this content, but its abstract, a statement of its contributions, or the framing of a main result presents the content as new. That covers implicit overstatement too: what matters is how a reader would reasonably take it, not whether the word "new" appears. For example, two cited papers together give the main theorem, the introduction says so in passing, and the abstract presents the theorem as the preprint's own. Record where the claim is made (`novelty_claim`). Without a citation, the case is an ordinary finding instead.

## Who decides inclusion
Section agents find and verify. Drafters write the finding as assigned. **The author-persona check decides** whether a finding earns a place in the report, and in what form, weighing what the pointer gives an expert reader against what it costs them in attention (`skeptic.md`). A finding it judges not worth a pointer stays in the JSON only.

Before that point, don't drop a verified candidate on a judgment call, such as:
- "superseded by later cited work";
- "only a standard device";
- "only a fragment".

Record the facts that bear on it instead: the dates, what the source itself says about the device, and which cited work covers what.

Stop early only on facts:
- the correspondence fails at a specific step;
- the source postdates the preprint;
- the preprint credits the content where it is used after all, and doesn't overstate it;
- the content is textbook material in exactly the form used: name the textbook passage;
- the earlier work is a parallel: state the facts (setting, object, and why nothing suggests the preprint drew on it).

The exclusions below are fixed; the persona doesn't revisit them.

## Not reported
- **Generic textbook or folklore tools in their textbook form.** The exception is when the *specific way they are combined* traces to an identifiable paper.
  - In each section brief, name the generic tools typical of that section's area, so agents don't spend time on them. **Name only single tools, never a combination of tools.** An agent told that a combination's ingredients are textbook tends to rule the combination generic too, even when it traces to a specific paper.
  - Examples of single tools, from probability and spin-glass papers:
    - semicircle law, edge rigidity, Stieltjes-transform bounds;
    - the bare Kac–Rice formula, and conditioning a GOE on linear constraints;
    - Weyl interlacing, BBP rank-one formulas, Schur complements, Sherman–Morrison;
    - Haar measure basics, coarea, Wick/Isserlis, Gaussian integration by parts;
    - Itô calculus, Doob, Markov/Chebyshev, Grönwall;
    - tensorization and the chain rule for entropy, Pinsker, Prékopa–Leindler;
    - the standard implications spectral gap ⇒ mixing and LSI ⇒ hypercontractivity.
- **"Cite the original rather than the later source" quibbles,** when a cited source genuinely covers the content. That includes a cited source that itself credits the original.
- **Physics heuristics or numerics, as findings.** A rigorous reuse of a *specific* expansion first derived in physics can still be a finding.
- **Anything public on or after the preprint's date.** "Earlier" means publicly available before it, and a same-day posting doesn't count.
- **Parallels:** an earlier paper doing the analogous thing in another setting, with nothing to suggest the preprint drew on it. A verified parallel can go in one sentence inside an entry when it helps place it.

## Companion preprints
Preprints from the same release that the paper cites are **not earlier work** here. Use them for two things only:
- to understand inputs the preprint imports;
- for the specific-content rule. A companion that re-proves the same lemma often names the external source, which makes it a good source of leads.

A companion re-running another companion's argument is not reportable. Many preprints have no companions; then the credit map and every companion clause are dropped.

## Verifying a finding
- **Never report from a title or abstract.** Download the paper into the library, read the specific passage, and compare statements and proofs side by side. Give exact locators: theorem or equation number plus the *printed* page in the stated version.
- **Never invent** citations, theorem numbers, quotes or formulas. If unsure, say so to the coordinator. In the write-up, leave the claim out.
- **Check hidden credit before calling anything uncited.** Grep the whole preprint, including the abstract, all sections, the bibliography, captions and footnotes, for:
  - the source's author names, with accent and spelling variants;
  - its bib key;
  - the technique's name.
- **Read the abstract and the contribution statements against the findings.** If one presents as new what a cited earlier work covers, that is overstated novelty.
- **Record what the source says about itself.** If the source calls the device standard, or credits a third paper for it, note that with its locator. It is content an expert reader wants.

## Order and IDs
- **During the section passes:** `§N-1`, `§N-2`, … in the reports and in FINDINGS.md.
- **In the write-up,** findings are ordered by magnitude and numbered F1, F2, … by LaTeX:
  1. centrality: main result, central, supporting, peripheral;
  2. then the relationship, in this order: same result, same technique, adapted, proof shortcut, same route, fragment, weaker result;
  3. then reading order.

  The validator checks this order.
- Reordering renumbers. If the user is already reading a draft, tell them when IDs change.
