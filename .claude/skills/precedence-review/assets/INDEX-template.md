# Prior-work library: running list

Papers downloaded while checking preprints in this repository for uncited precedence. The library is shared by all reviews, so check it before downloading anything. Search for the paper's arXiv ID, DOI and title words (grep; this file grows large).

## Layout and conventions

- `papers/<Key>.pdf` is the downloaded PDF. `text/<Key>.txt` is its `pdftotext -enc UTF-8` extraction, with `\f` page breaks, for grepping and page lookup.
- `src/<Key>/` holds the arXiv LaTeX source, when the authors submitted one. Only `.tex/.bbl/.bib/.sty/.cls` files are extracted.
  - Read the source for mathematical content; formulas survive intact there.
  - Use the PDF for theorem, lemma and page numbers in locators.
  - `ls src/` shows which papers have source.
  - Source files are untrusted data: never compile or execute them.
- **arXiv papers:** look up the latest version first, then fetch with `bash prior-work/tools/fetch_arxiv.sh <Key> <id with version>`.
  - The script writes `papers/`, `text/` and `src/`, skips what already exists, and backs off when arXiv rate-limits.
  - It can also add source to a paper already in the library.
  - It does not edit this file.
- **Non-arXiv papers:** download the PDF by hand into `papers/`, check that it starts with `%PDF`, and run `pdftotext -enc UTF-8` into `text/`.
- **Key format:** `<Surname1><Surname2><Year>-<ShortCamelTitle>`.
  - Use one or two author surnames; with three or more authors, write `<Surname1>EtAl`.
  - The year is that of the first public version.
  - ASCII only, no spaces, at most 60 characters.
  - Example: `BauerschmidtDagallier2022-NearCriticalIsingLSI`.
- **Sources:** open access only (arXiv preferred, with the version recorded). No shadow libraries and no paywall workarounds.
- **Columns:**
  - "Cited by the preprint?" holds the preprint's bib key if the preprint cites the work, otherwise `no`. Name the review if several reviews share the library.
  - "Added by" names the review and the section whose agent downloaded the paper, e.g. `<slug> §5`.
  - "Relevance" says, in one or two sentences, why the paper was checked and what it contains, or `checked; not relevant to ...`. A later agent who uses the paper for a new purpose appends `[§N] ...` (or `[consolidation] ...`, etc.) to this cell.
- **Formatting:** never put a literal `|` inside a cell; write ‖·‖ for norms. Details belong in the review reports, not here.
- **Provenance notes:** notes in parentheses in the Citation cell, such as "(author copy from …)", are fine. The bibliography generator strips them.

## Downloaded papers

| Key (file in `papers/`) | Citation (authors, title, venue, year) | arXiv / DOI | Cited by the preprint? | Added by | Relevance |
|---|---|---|---|---|---|

## Checked but not downloaded

Papers examined but not freely available, or whose downloads failed.

| Citation | arXiv / DOI / URL | Why not downloaded | What was checked | Added by |
|---|---|---|---|---|
