# Findings digest: {review slug}

The coordinator maintains this file after every section. Section subagents read it instead of all the earlier reports; the full reports are `NN-*.md`. Author-persona checks never read it.

**Scope:** load-bearing content that an identifiable earlier paper already contains, where the preprint doesn't cite that paper for it where it is used. That covers reused techniques, constructions and theory, proposed routes the preprint carries out, and earlier results on the same problem. The introduction pass searches for earlier results; later passes record one-liners. Subsuming results are a passive slot only. The one exception is overstated novelty: content the preprint cites, but presents as new in its abstract or framing.

Inclusion is decided by the author-persona check, so don't drop a verified candidate on a judgment call: record the facts. Out of scope: textbook or folklore tools in textbook form, "cite the original" quibbles, parallels, and anything public on or after the preprint's date.

**Relationship:** same technique (reused essentially intact, even with new ingredients around it) · adapted (structure followed, core changed) · fragment (one piece of the technique) · same route · same result · weaker result · subsuming result.

**Centrality (best-effort):** main result (the earlier work covers the main result itself, or most of it) · central · supporting · peripheral. A weaker result is at most central.

**Credit status:** not cited · cited for other content · credited elsewhere (not where it is used) · credited in part. A citation counts only if it is for that specific content; citing the same paper nearby for something else does not count. A method citation covers the method's own lemmas. Content credited where it is used, directly or through a cited location that credits it, is not a finding unless its novelty is overstated.

**Author-name check:** {for each finding: the source's names, and where, if anywhere, they appear in the preprint, its abstract and its bibliography}

## Findings

| ID | Technique or result (source, locators) | Relationship | Where in the paper (dependency chain) | Credit status | Differences |
|---|---|---|---|---|---|

## Overstated novelty

- **{ID}:** {the claim, quoted, and its location}; {the cited earlier work that covers it, and where the preprint cites it}.

## Earlier-result one-liners (for consolidation)

- §N: {earlier result, locator, date}; {what in the preprint it precedes}.

## Ruled out or covered (don't re-check)

- **{item}:** {ruling and reason} (§N).

## Recurrences, corrections and merge candidates (for consolidation)

- §N: {finding} also at {locations}.
- Merge candidates (the user decides at the write-up): {IDs, reason}.
- Corrections reported by agents: {what and where}.
- Strongest objection to a judgment-based finding, with its factual premise (for the drafter to check; never passed to the persona): {ID: objection}.

## Subsuming results (noted)

- {paper span}. {published result and locator}. {what becomes a citation}. {status of the coordinator's check}.

## User decisions

- {date}: {decision, verbatim where it matters}.

## Write-up: slugs, order and changes during drafting

| Slug | ID | Relationship | Centrality (dependency chain) | Flags | Drafting outcome (pages; proposed changes; dropped components; withdrawal and its defect) |
|---|---|---|---|---|---|

## Final verdicts

Filled in after the author-persona check: form of inclusion, claims verdict, relationship and centrality as settled, errata count, the length applied, and which findings stay in the JSON only.
