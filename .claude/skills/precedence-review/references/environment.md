# Environment pitfalls and working recipes

These come from the failed tool calls in about 80 subagent transcripts from the first run and the coordinator's errors in the second, both on Windows with Git Bash. Most are generic; the Windows-only ones are marked. Before the first brief, check what the machine has: `which pdftotext pdfinfo pdftoppm pdflatex gh curl python3 python`. Also check whether PyMuPDF imports with plain `python3`.

Commands here say `python3`, since macOS and many Linux systems have no `python`. On a machine where only `python` exists (some Windows installs), substitute it everywhere, including in the briefs. The bundled shell scripts already try `python3` first, then `python`. The scripts need Python 3.9 or later.

## The "Tool pitfalls" block
Paste this into **every** subagent prompt. Drop the lines that don't apply to the platform.

````text
**Tool pitfalls on this machine:**
- The Bash tool can turn `\\` into `\` before the shell sees it, even inside single quotes and quoted heredocs. Never pass LaTeX or regexes containing `\\` through sed, heredocs or `python -c`. Edit `.tex` files only with the Read/Edit/Write tools; write any script to a file with Write, then run it.
- Python: run scripts as `python3 -I -X utf8 <script>` (or `python` where `python3` doesn't exist) (or start them with `import sys; sys.stdout.reconfigure(encoding="utf-8")`). `PYTHONIOENCODING` is ignored under `-I`, and the console may not be UTF-8. Open text files with `encoding="utf-8", errors="replace"`. Use raw strings for any TeX in Python.
- Windows/Git Bash: run pdflatex from inside its directory with relative file names (MSYS rewrites Windows paths, and arguments starting with `/`). Don't use `/tmp`; it isn't where Python looks, and it isn't your scratch folder. Pass file paths to Python as arguments, not inside string literals. Quote every path.
- Use your own subfolder of the scratch directory (`{SUBFOLDER}`) for every temporary file; other agents share the scratch root, and generic names like `test.tex` or `pg.py` collide.
- The repository is a partial (blobless, sparse) git clone. Don't run git commands that read every file's contents (`git ls-tree -l`, `git grep <rev>`, `git log -p`); they trigger huge downloads. You don't need git at all.
- Don't assume numpy, scipy or sympy are importable under `python3 -I`. Write numeric spot checks in pure Python (e.g. Simpson's rule).
- arXiv: always `curl -sSL "https://export.arxiv.org/..."`. Plain http returns an empty 301 with no error, so an empty result means a failed request, not "no hits". Wait 3–5 s between calls; on 429 or "Rate exceeded" wait 30 s or more. Look up the latest version (`api/query?id_list=<id>`) before calling fetch_arxiv.sh, which requires a version.
- A grep with no match exits 1, and `ls` on a missing path exits 2; these are not failures when output is otherwise correct. Bound outputs with `head` or `cut -c1-300`; very large outputs are saved to a file instead of shown.
````

## Pitfalls, with what fixed them

### Text and encodings
- **Backslash collapse in the Bash tool.** This was the most damaging failure: about 25 incidents across 15 agents.
  - LaTeX row ends `\\` became `\`, which produced `! Misplaced \noalign` and `! Extra alignment tab`.
  - sed replacements matched nothing, silently.
  - sed turned `\r` in `\raggedright` into a carriage return.
  - Python's `assert old in s` failed.

  The Edit tool fixed it every time. To find damage, grep for row ends that lost a backslash, `grep -n '[^\\]\\$'` (that pattern is safe because it is in a file or the Grep tool). Look for stray control characters with `grep -c $'\r'`.
- **Python string escapes.** In non-raw strings, `'\begin'` contains a backspace and `'\varphi'` a vertical tab. Use `r"..."`, or the Edit tool.
- **Console encoding.** Printing paper text crashed with `UnicodeEncodeError: 'charmap' codec` (cp1252), 40+ times. Retrying with `PYTHONIOENCODING=utf-8 python -I` failed every time, because `-I` implies `-E`. What works: `-X utf8`, or `sys.stdout.reconfigure(encoding="utf-8")`.
- **Non-UTF-8 text from pdftotext.** Some extractions are not valid UTF-8 (`UnicodeDecodeError ... 0xed`). Read with `errors="replace"`.
- **Garbled math.** pdftotext garbles math in some PDFs. Use the `.txt` for page lookup only, and take formulas from `src/<Key>/` or from the PDF page (Read tool with `pages`).
- **Ligatures.** The text contains ligatures (`ﬁ`), so "field" may not match. Search both forms.
- **Write without Read.** Write refuses to overwrite a file that hasn't been Read in this session. Read it first, even 3 lines, or use a fresh name.

### Python environment
- **`python -I` drops user site-packages,** which hid PyMuPDF and sympy. Run your own helper with plain `python` from a folder containing only that script when you need such packages.
- **Don't assume numpy or scipy** is installed. A section agent's `from scipy.integrate import quad` failed; it switched to a hand-written Simpson rule.

### Git and the clone
- **A full clone is about 3 GB**, mostly `lean/` (1.6 GB) and PDFs. It also hits the Windows path-length limit ("Filename too long") without `core.longpaths`. Use the slim clone in the recipes below.
- **Blobless clones fetch blobs lazily.** `git ls-tree -l` needs every blob's size, so it downloaded the whole repository, stalled past the tool timeout, and doubled `.git`. Use `--name-only` listings.
- **Sparse-checkout patterns on Git Bash.** `git sparse-checkout set --no-cone '/*' '!/lean/'` wrote `C:/Program Files/Git/lean/` into the pattern file, because MSYS rewrites arguments starting with `/`. It then checked out all of `lean/`. Pass the patterns through `--stdin`.
- **Sparse checkout and `git add`.** A path excluded by the patterns, such as a new PDF under `!*.pdf`, is refused by `git add` ("outside of your sparse-checkout definition"). Use `git add --sparse -- <paths>`, then check `git diff --cached --name-status`.
- **Replacing a clone.** You can't delete or rename the folder the session's working directory is in ("Device or resource busy"). Clone the new copy next to it and switch the session there first.
- **Authentication.** An HTTPS push can fail on a stale stored token ("Invalid username or token"). Don't work around it; ask the user which remote and identity to use.

### Files and layout
- **`src/<Key>/` exists only for arXiv papers with a source download.** Check `ls prior-work/{papers,text,src} | grep -i <key>` first. `text/<Key>.txt` exists for every downloaded paper.
- **Bibliography and sections live under `build/`.** A preprint's bibliography and sections are in `build/`, not at the preprint root. The bibliography may be `references.bib` or `references.tex` with `\bibitem`s, for the target as well as its companions.
- **Theorem environments vary.** Papers use `thm`, `lem`, `ppn` and the like. Grep `\newtheorem` before grepping `\begin{theorem}`.
- **PDF names vary.** The compiled PDF may be `paper.pdf` or `main.pdf`.
- **INDEX.md cells.** A literal `|` in a cell breaks the table, and `make_bib.py` then refuses to build. Agents wrote absolute values like `|γ(t1)−γ(t2)|` in a Relevance cell. Write `abs(…)` and ‖·‖ instead.

### Network
- **arXiv over http.** Plain http returns 301 and an empty body; use https with `-L`. A guessed version can 404, so resolve it through the API. Bursts get `Rate exceeded.` or a 503 HTML page. `fetch_arxiv.sh` backs off 10, 30 and 60 s on 429 and 503.
- **arXiv search queries.** Percent-encode quotes (`%22`) and parentheses. Check `<opensearch:totalResults>`: AND-heavy queries often return 0.
- **Semantic Scholar.** The unauthenticated API returns 429 right away. Get metadata from the arXiv API and trace citations with WebSearch.
- **Publisher sites.** OUP, Project Euclid and some repositories serve an HTML bot page as `200 text/html`, or a 403. Always check `-w '%{http_code} %{content_type}'` and that `head -c 5` gives `%PDF-`, and delete non-PDFs. Author homepages and Numdam worked.
- **Crossref and OpenAlex.** Both worked at 1–2 s spacing. Never send identifying information: no email, no `mailto`, no personal User-Agent.

### LaTeX
- **Path mangling (Windows/MSYS).** Passing `\input{C:/...}` on the pdflatex command line got mangled. Use `scripts/fragment_test.sh`, which copies the files into a scratch folder.
- **Passes.** Two pdflatex passes resolve references; a clean directory needs three for the table of contents.
- **Overfull boxes.** These mostly came from long titles, wide displays and long `\texttt` strings. Fixes:
  - a short optional `\subsection[...]` title;
  - `gather*` or split displays;
  - shorter locators.

  Small overfulls under about 5pt are fine; fix anything over 10pt.
- **hyperref "Token not allowed".** Caused by math in titles; use `\texorpdfstring`.
- **Expected warnings in a standalone fragment test:** undefined citations and references.
- **Benign noise:**
  - MiKTeX's "you have not checked for updates" on every run;
  - `Font shape ... undefined` warnings;
  - pdftotext `Syntax Warning`s.

### Harness behavior
- **Large outputs.** Tool outputs over about 30 KB are saved to a file; Read that file.
- **Deferred tools.** Subagents must load WebSearch/WebFetch through ToolSearch before using them.
- **The Read tool on PDFs** takes one page or one range (`pages: "3-4"`), not a list.
- **Grep tool patterns.** Look-ahead and look-behind are not supported. Filter afterwards.
- **Long Bash loops** may be auto-backgrounded.

## Recipes

**Slim clone of the reviews repository** (about 270 MB instead of about 3 GB). Run it in the background; it takes minutes.
```
git clone -c core.longpaths=true --filter=blob:none --sparse https://github.com/jnshi/math-lineage
cd math-lineage
git ls-tree -d --name-only HEAD preprints/ | grep -i "<words from the title>"
git sparse-checkout set --no-cone --stdin <<'EOF'
/*
!/lean/
!*.pdf
/overview.pdf
/preprints/<preprint>/<its PDF>
EOF
```
Add companion PDFs the same way: `echo '/preprints/<dir>/<file>.pdf' | git sparse-checkout add --stdin`. In an existing full clone, the same `sparse-checkout set` slims it in place.

**Find the compiled page of a statement.** pdftotext output separates pages with `\f`.
```
python3 -I -X utf8 <skill>/scripts/pagefind.py <scratch>/paper.txt "Lemma 8\.2" "proved here"
python3 -I -X utf8 <skill>/scripts/pagefind.py <scratch>/paper.txt --page 32
```
`p.N` is the PDF page index, which can differ from the printed page number, for example in journal reprints or after an unnumbered title page. For each page with a hit, the script also shows the page's first and last lines; read the printed number there and use that in locators. Patterns are matched against each page as a whole, so `^` and `$` don't anchor to lines. Text without form feeds is rejected; re-extract it with plain `pdftotext -enc UTF-8`.
Straight from a PDF: `for p in $(seq 10 30); do pdftotext -enc UTF-8 -f $p -l $p X.pdf - | grep -q "Lemma 4.4" && echo p.$p; done; true`.

**Look up arXiv metadata or the latest version.**
`curl -sSL "https://export.arxiv.org/api/query?id_list=2208.09550" | grep -E "<id>|<title>|<published>|<updated>|journal_ref"`

**Search arXiv** (wait 3–5 s between calls):
`curl -sSL "https://export.arxiv.org/api/query?search_query=au:Lehec+AND+abs:%22stochastic+localization%22&max_results=20&sortBy=submittedDate"`

**Fetch an arXiv paper into the library:**
Run `bash <repo>/prior-work/tools/fetch_arxiv.sh <Key> <id>v<N>`.
- If it exits 0, append the INDEX.md row.
- If it exits 1, its last line says what failed: the PDF, the text or the source. Nothing partial is kept, so a rerun retries cleanly.
- `src: none` (only a PDF was submitted, or no TeX files in the source) is not a failure.

**Fetch a non-arXiv PDF:**
```
curl -sSL -A "Mozilla/5.0" -o papers/<Key>.pdf -w "%{http_code} %{content_type}\n" "<url>"
head -c 5 papers/<Key>.pdf        # must print %PDF-
pdftotext -enc UTF-8 papers/<Key>.pdf text/<Key>.txt
```

**Read a TeX source with line numbers, for locators:**
`awk 'NR>=360 && NR<=470 {print NR": "$0}' file.tex`, or the Read tool with offset and limit.

**Check what the preprint cites a work for:**
Use the Grep tool with pattern `cite[pt]?(\[[^]]*\])?\{[^}]*<bibkey>` over `build/sections`.

**Check whether the preprint names a source anywhere** (the author-name check). Use the actual bibliography file. Printing the matching lines, not just file names, shows *how* a name appears, e.g. only inside another paper's key:
```
for t in "El Alaoui" Sellke Polchinski "Br.zin" "approximate critical"; do printf "%-22s %s\n" "$t" "$(grep -n -i -E "$t" build/sections/*.tex build/references.* | sed 's#.*/build/##' | cut -c1-70 | tr '\n' ' ' | cut -c1-300)"; done
```

**Render a PDF page for a visual check:**
`pdftoppm -f 17 -l 17 -r 80 -png file.pdf pg`, then Read the PNG. Or use the Read tool on the PDF with `pages`.
