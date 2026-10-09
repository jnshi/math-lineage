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
  - It does not edit this file. Add the paper's row only after the script exits 0.
  - `src: none` means the authors submitted only a PDF, or the source has no TeX files; that is not a failure.
  - The script works in a staging folder `prior-work/.fetch-tmp.*`. If one is left behind (e.g. after an interrupted run), delete it.
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
  - "Relevance" says, in one or two sentences, why the paper was checked and what it contains, or `checked; not relevant to ...`. A later agent who uses the paper for a new purpose appends `[<slug> §N] ...` (or `[<slug> consolidation] ...`, etc.) to this cell.
  - Rows imported from a library kept elsewhere (`scripts/merge_library.py`) carry a `<tag>:` prefix in "Cited by" and "Added by". Their "Cited by" refers to that review's preprint.
- **Titles and dates:** copy the title exactly as the paper's title page gives it, and give the date of the first public version (e.g. "July 9, 2026" for a recent preprint). The bibliography of every write-up is generated from this file.
- **Formatting:** never put a literal `|` inside a cell: write ‖·‖ for norms and `abs(x)` for absolute values. Details belong in the review reports, not here.
- **Provenance and verification notes:** put them in the Relevance cell. If a note must sit in the Citation or arXiv / DOI cell, write it as `[note: …]`, for example `[note: author copy from the author's homepage; venue not verified]`. The bibliography generator strips `[note: …]` marks and parenthetical clauses containing a URL, and nothing else. A note written as ordinary parentheses would reach the published bibliography. The generator lists every wordy parenthetical it keeps so you can catch one.
- **The Citation cell is plain text,** not TeX. Write formulas plainly, for example "C^{1,1}" or "beta < 1/2"; the generator escapes everything.

## Downloaded papers

| Key (file in `papers/`) | Citation (authors, title, venue, year) | arXiv / DOI | Cited by the preprint? | Added by | Relevance |
|---|---|---|---|---|---|

## Checked but not downloaded

Papers examined but not freely available, or whose downloads failed.

| Citation | arXiv / DOI / URL | Why not downloaded | What was checked | Added by |
|---|---|---|---|---|
