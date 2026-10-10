# Sourced by build.sh, fragment_test.sh and publish_prep.sh: how the write-up
# is compiled. The write-up's TeX is written by agents that read untrusted
# sources, so TeX itself is confined, whatever commands the TeX contains:
#   - it cannot read files outside its working folder and that folder's
#     subfolders (apart from TeX's own installation, found by search);
#   - it cannot write outside them, or run programs (-no-shell-escape);
#   - it writes PDFs without object streams, so pdf_check.py can read every
#     object.
# TeX Live reads openin_any/openout_any from the environment ("p": paranoid);
# MiKTeX reads MIKTEX_CORE_ALLOWUNSAFEINPUTFILES/OUTPUTFILES. Each ignores the
# other's variables, so both are set.
#
#   sandbox_pdflatex [pdflatex options] <file.tex>
#       pdflatex, confined, from the current folder; the job name is the file's.
#       Its input is empty, so TeX code that reads the terminal ends the run.
#       A run longer than SANDBOX_SECONDS (TeX can loop forever) is stopped
#       with exit status 124, where timeout or gtimeout is installed.
#   sandbox_check
#       returns 1 (with a message) unless this TeX installation actually refuses
#       to read a file outside its folder. Run it before compiling: on a TeX that
#       ignores both settings, compiling would not be confined.

SANDBOX_SECONDS=300

sandbox_pdflatex() {
  local n=$#
  local file=${!n}
  local opts=("${@:1:$((n - 1))}")
  local job limit=() rc
  job=$(basename "$file" .tex)
  if command -v timeout > /dev/null 2>&1; then
    limit=(timeout "$SANDBOX_SECONDS")
  elif command -v gtimeout > /dev/null 2>&1; then
    limit=(gtimeout "$SANDBOX_SECONDS")
  fi
  ${limit[@]+"${limit[@]}"} env openin_any=p openout_any=p shell_escape=f \
    MIKTEX_CORE_ALLOWUNSAFEINPUTFILES=f MIKTEX_CORE_ALLOWUNSAFEOUTPUTFILES=f \
    pdflatex -no-shell-escape ${opts[@]+"${opts[@]}"} -jobname="$job" \
      "\\pdfobjcompresslevel=0 \\input{$file}" < /dev/null
  rc=$?
  if [ "$rc" = 124 ]; then
    echo "pdflatex stopped after ${SANDBOX_SECONDS}s: the TeX is probably looping" >&2
  fi
  return $rc
}

sandbox_check() {
  local t abs rc=0
  t=$(mktemp -d 2>/dev/null) || { echo "sandbox check: cannot create a temporary folder" >&2; return 1; }
  mkdir "$t/outside" "$t/run" || { rm -rf "$t"; return 1; }
  printf '%s\n' '\typeout{SANDBOX-CANARY-WAS-READ}' > "$t/outside/canary.tex"
  # The absolute path as TeX sees it (Windows form under Git Bash).
  abs=$(cd "$t/outside" && { pwd -W 2>/dev/null || pwd; })
  printf '%s\n' '\documentclass{article}' \
    '\InputIfFileExists{../outside/canary.tex}{}{}' \
    "\\InputIfFileExists{$abs/canary.tex}{}{}" \
    '\begin{document}x\end{document}' > "$t/run/c.tex"
  ( cd "$t/run" && sandbox_pdflatex -interaction=nonstopmode c.tex > /dev/null 2>&1 )
  if [ ! -f "$t/run/c.log" ] || ! grep -q 'Output written' "$t/run/c.log"; then
    echo "sandbox check: pdflatex could not compile a test file" >&2
    rc=1
  elif grep -q 'SANDBOX-CANARY-WAS-READ' "$t/run/c.log"; then
    echo "sandbox check: this TeX installation read a file outside its folder despite openin_any=p and MIKTEX_CORE_ALLOWUNSAFEINPUTFILES=f; refusing to compile. Tell the user." >&2
    rc=1
  fi
  rm -rf "$t"
  return $rc
}
