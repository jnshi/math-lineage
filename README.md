&emsp;*Quick links: [To read](#to-read) · [To contribute](#to-contribute) · [About the skill](#about-the-skill) · [Reviewed preprints](#reviewed-preprints) · [List of missing attributions](#list-of-missing-attributions)*

On October 6, 2026, OpenAI released a [repository](https://github.com/openai/math) of 722 machine-generated manuscripts presenting solutions to major open problems across many fields of mathematics. A week earlier, the [Advisory Group on Mathematics and Artificial Intelligence](https://agmai.org) (AGMAI), a group of mathematicians that advises AI companies, had [recommended](https://agmai.org/general-sep29/) that a lab releasing such results first search the literature for related ideas and "cite the papers in which the ideas were first introduced". On the day of the release, AGMAI left it to the mathematical community to assess how far its recommendations had been followed ([statement](https://agmai.org/#openai-release)).

When a manuscript uses ideas and techniques from earlier papers without citing them, it removes the landmarks that normally help readers navigate a new paper, obscures what is truly new in it, and withholds credit from the people who introduced those ideas. Proper citation is therefore not considered optional in published works.

The goal of this repository is to search for and document some of this missing attribution, and so to help the community with its assessment and aid in understanding the new solutions. The approach uses LLM agents to handle this task at scale. Each report lists earlier works used by a preprint without citation, with locators in both papers so that readers can check each finding.

*Sketch, generated from each published report's `precedence-stats.json` and updated with every new report; it may also give the counts by field, using the field headings in [`overview.pdf`](overview.pdf):*

So far, ⟨n⟩ of the 719 preprints have been reviewed. The reports list ⟨N⟩ findings (⟨counts by relationship⟩; ⟨counts by centrality⟩), of which ⟨g⟩ are attribution gaps and ⟨k⟩ show overstated novelty.

## To read

In each reviewed manuscript's folder under [`preprints/`](preprints/), the report `precedence-findings.pdf` sits next to OpenAI's original manuscript, usually `paper.pdf` or `main.pdf`. The folder's `README.md` also summarizes the report in a table. The reviewed manuscripts are listed under [Reviewed preprints](#reviewed-preprints). Each report makes no claim of completeness, does not judge whether the manuscript is correct, and has not been vetted by a human.

This repository is a fork of [openai/math](https://github.com/openai/math). The manuscripts and their supporting material (`preprints/`, `lean/`, `reasoning_traces/`, [`CONTENTS.md`](CONTENTS.md), [`overview.pdf`](overview.pdf), [`history.md`](history.md)) are as released there; see [its README](https://github.com/openai/math#readme) for how they were produced.

## To contribute

To review a preprint that doesn't have a review yet (see [Reviewed preprints](#reviewed-preprints)):
1. Make a slim clone of this repository, without `lean/` and the PDFs: about 270 MB instead of 3 GB. On Windows, run these commands in Git Bash.
   ```bash
   git clone -c core.longpaths=true --filter=blob:none --sparse https://github.com/jnshi/math-lineage
   cd math-lineage
   git sparse-checkout set --no-cone --stdin <<'EOF'
   /*
   !/lean/
   !*.pdf
   EOF
   ```
2. Start an agent that reads [`AGENTS.md`](AGENTS.md) in the `math-lineage` folder, and ask it for a precedence review of the preprint. Use Claude Opus 5.5, GPT 5.6 Sol or a stronger model; weaker models have not been evaluated yet. If you want to read a file that the slim clone left out, such as the preprint's PDF, ask the agent to check it out. The agent asks a few questions first, shows you the report before anything is published, and asks before opening a pull request against this repository.

A 27-page preprint took about 350M tokens (97% cache reads) and 4 hours. Expect a 50-page preprint to take 50–100% of the weekly usage limit of a basic paid subscription.

To request a review of a preprint, open an issue that names it. To report an error in a report, open an issue that names the preprint and the finding's ID.

Findings, corrections and vetting from experts are planned too, alongside the machine-sourced findings, but their format is not settled yet. Suggestions are welcome on the [discussions page](https://github.com/jnshi/math-lineage/discussions). For now, they can go in an issue.

## About the skill

The [precedence-review skill](.agents/skills/precedence-review/SKILL.md) reads a preprint section by section and searches for earlier papers that already contain the techniques, constructions and results it uses. Each candidate is checked against the earlier paper itself. A separate agent then reviews each finding from the preprint author's point of view, and decides whether citing the earlier work would help an expert reader or is owed as credit.

Pull requests that improve the skill are welcome; please include a before-and-after of two preprint reviews in the PR, with the [SK model spectral gap](preprints/A-spectral-gap-throughout-the-high-temperature-Sherrington-Kirkpatrick-phase-September-24-2026/) as one of them.

**License.** The precedence-review skill is licensed under a mix of the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0) and the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). See the LICENSE files in the [skill folder](.agents/skills/precedence-review/) for details.

## Reviewed preprints

*Sketch, updated with every new report: one row per reviewed preprint, in the numbered order of [`overview.pdf`](overview.pdf) (by result number, then in the order the result lists its manuscripts), under the overview's field headings. Fields with no reviewed preprint are left out.*

<table>
<thead><tr><th>Result</th><th>Preprint</th><th>Report date</th><th>Findings</th><th>Attribution gaps</th></tr></thead>
<tbody>
<tr><th colspan="5">⟨Field heading from overview.pdf⟩</th></tr>
<tr><td>⟨result number⟩</td><td><a href="preprints/⟨folder⟩/">⟨title⟩</a></td><td>⟨date⟩</td><td>⟨N⟩</td><td>⟨g⟩</td></tr>
</tbody>
</table>

## List of missing attributions

*Sketch, generated from each published report's `precedence-findings.json`: a bibliography of the earlier works that the reports find missing, one entry per work, in alphabetical order of first author. It includes every earlier work in a finding printed in a report, unless the preprint credits the work for that content; findings with overstated novelty are left out. Works are merged across reports by arXiv id or DOI, and otherwise by exact title and author list.*

- ⟨Authors⟩. ⟨Title⟩. ⟨Venue⟩, ⟨year⟩. [arXiv:⟨id⟩](https://arxiv.org/abs/⟨id⟩)
- ⟨Authors⟩. ⟨Title⟩. ⟨Venue⟩, ⟨year⟩. [doi:⟨doi⟩](https://doi.org/⟨doi⟩)
