# Findings digest: {review}

The coordinator maintains this file after every section. Section subagents read it instead of all the earlier reports; the full reports are `NN-*.md`. Author-persona checks never read it.

**Scope:** techniques, constructions, results and proof routes that the preprint uses in its arguments, which an identifiable earlier paper already contains, where the preprint doesn't cite that paper for them where they are used.
- That covers reused techniques, constructions and theory, proposed routes the preprint carries out, and earlier results on the same problem. The introduction pass searches for earlier results; later passes record one-liners.
- Proof shortcuts are recorded only when noticed; nobody searches for them.
- The one exception is overstated novelty: content the preprint cites, but presents as new in its abstract or framing.

**Inclusion** is decided by the author-persona check, so don't drop a verified candidate on a judgment call: record the facts. Rule a candidate out only on facts:
- the correspondence fails;
- the source postdates the preprint;
- it is credited where used;
- it is textbook material in the form used (name the passage);
- it is a parallel (state the facts);
- it is a "cite the original" quibble;
- it is a physics heuristic.

**Relationship** (in sort order): same result · same technique (reused essentially intact, even with new ingredients around it) · adapted (structure followed, core changed) · proof shortcut · same route · fragment (one piece of the technique) · weaker result.

**Centrality** (best-effort judgment of how much of the main argument depends on it): main result (the earlier work covers the main result itself, or most of it) · central · supporting · peripheral. A weaker result is never main result.

**Credit status:** not cited · cited for other content · credited elsewhere (not where it is used) · credited in part · credited (only with overstated novelty).
- A citation counts only if it is for that specific content; citing the same paper nearby for something else does not count.
- A method citation covers the method's own lemmas.
- Content credited where it is used, directly or through a cited location that credits it, is not a finding unless its novelty is overstated.
- List the principal earlier work first.

**Author-name check:** {for each finding: the source's names, and where, if anywhere, they appear in the preprint, its abstract and its bibliography}

## Findings

| ID | Technique or result (sources, principal first, with locators) | Relationship | Where in the paper (dependency chain) | Credit status | Differences |
|---|---|---|---|---|---|

## Overstated novelty

- **{ID}:** {the claim, quoted, and its location}; {the cited earlier work that covers it, and where the preprint cites it}.

## Earlier-result one-liners (for consolidation)

- §N: {earlier result, locator, date}; {what in the preprint it precedes}.

## Ruled out (don't re-check)

- **{item}:** {the fact that rules it out} (§N).

## Recurrences, corrections and merge candidates (for consolidation)

- §N: {finding} also at {locations}.
- Merge candidates (the user decides at the write-up): {IDs, reason}.
- Corrections reported by agents: {what and where}.
- Strongest judgment-call objection to a finding, with its factual premise (for the drafter to check; never passed to the persona): {ID: objection}.

## Proof shortcuts (noted)

- {paper span}. {published result and locator}. {what becomes a citation}. {status of the coordinator's check}.

## User decisions

- {date}: {decision, verbatim where it matters}. Include whether the user wants to check the persona's reasoning before findings are dropped.

## Write-up: slugs, order and changes during drafting

| Slug | ID | Relationship | Centrality (dependency chain) | Flags | Drafting outcome (pages; proposed changes; dropped components; withdrawal and its fact) |
|---|---|---|---|---|---|

## Final verdicts

Filled in after the author-persona check: form of inclusion, claims verdict, the relationship and centrality you settled, errata count, the length applied, and which findings stay in the JSON only.
