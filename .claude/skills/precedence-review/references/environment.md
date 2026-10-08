# Environment pitfalls and working recipes

These come from the failed tool calls in about 80 subagent transcripts from the first run, which was on Windows with Git Bash. Most are generic; the Windows-only ones are marked. Before the first brief, check what the machine has: `which pdftotext pdfinfo pdftoppm pdflatex gh curl python`. Also check whether PyMuPDF imports with plain `python`.

## The "Tool pitfalls" block
Paste this into **every** subagent prompt. Drop the lines that don't apply to the platform.

````text
**Tool pitfalls on this machine:**
- The Bash tool can turn `\\` into `\` before the shell sees it, even inside single quotes and quoted heredocs. Never pass LaTeX or regexes containing `\\` through sed, heredocs or `python -c`. Edit `.tex` files only with the Read/Edit/Write tools; write any script to a file with Write, then run it.
- Python: run scripts as `python -I -X utf8 <script>` (or start them with `import sys; sys.stdout.reconfigure(encoding="utf-8")`). `PYTHONIOENCODING` is ignored under `-I`, and the console may not be UTF-8. Open text files with `encoding="utf-8", errors="replace"`. Use raw strings for any TeX in Python.
- Windows/Git Bash: run pdflatex from inside its directory with relative file names (MSYS rewrites Windows paths in arguments). Don't use `/tmp`; it isn't where Python looks, and it isn't your scratch folder. Pass file paths to Python as arguments, not inside string literals. Quote every path.
- Use your own subfolder of the scratch directory for every temporary file; other agents share the scratch root, and generic names like `test.tex` or `pg.py` collide.
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
- **Don't assume numpy** is installed.

### Files and layout
- **`src/<Key>/` exists only for arXiv papers with a source download.** Check `ls prior-work/{papers,text,src} | grep -i <key>` first. `text/<Key>.txt` exists for every downloaded paper.
- **Bibliography and sections live under `build/`.** A preprint's bibliography and sections are in `build/`, not at the preprint root. A companion's bibliography may be `references.tex` with `\bibitem`s.
- **Theorem environments vary.** Papers use `thm`, `lem`, `ppn` and the like. Grep `\newtheorem` before grepping `\begin{theorem}`.
- **PDF names vary.** Companion PDFs may be named `main.pdf`.

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

**Find the compiled page of a statement.** pdftotext output separates pages with `\f`.
```
python -I -X utf8 <skill>/scripts/pagefind.py <scratch>/paper.txt "Lemma 8\.2" "proved here"
python -I -X utf8 <skill>/scripts/pagefind.py <scratch>/paper.txt --page 32
```
Straight from a PDF: `for p in $(seq 10 30); do pdftotext -enc UTF-8 -f $p -l $p X.pdf - | grep -q "Lemma 4.4" && echo p.$p; done; true`.

**Look up arXiv metadata or the latest version.**
`curl -sSL "https://export.arxiv.org/api/query?id_list=2208.09550" | grep -E "<id>|<title>|<published>|<updated>|journal_ref"`

**Search arXiv** (wait 3–5 s between calls):
`curl -sSL "https://export.arxiv.org/api/query?search_query=au:Lehec+AND+abs:%22stochastic+localization%22&max_results=20&sortBy=submittedDate"`

**Fetch an arXiv paper into the library:**
`bash <repo>/prior-work/tools/fetch_arxiv.sh <Key> <id>v<N>`, then append the INDEX.md row.

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

**Check whether the preprint names a source anywhere** (the author-name check):
```
for t in "El Alaoui" Sellke Polchinski "Br.zin"; do printf "%-12s %s\n" "$t" "$(grep -l -i -E "$t" build/sections/*.tex build/references.bib | xargs -r -n1 basename | tr '\n' ' ')"; done
```

**Render a PDF page for a visual check:**
`pdftoppm -f 17 -l 17 -r 80 -png file.pdf pg`, then Read the PNG. Or use the Read tool on the PDF with `pages`.
