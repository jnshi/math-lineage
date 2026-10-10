---
name: precedence-review
description: Run a full precedence review of a mathematics preprint. It finds the preprint's missing citations, meaning earlier papers that already contain parts of it but that it doesn't cite where those parts appear, plus cited content that its abstract or framing presents as new. It verifies each against the sources, and publishes an expert-facing LaTeX write-up ("Missing citations in …"), JSON findings and a pull request. It is built around preprints from the openai/math release and the collaborative repository jnshi/math-lineage on GitHub. Use it when someone asks for a precedence review or a missing-citations review of a whole preprint, or to resume, extend, check or publish one. A full review takes hours and millions of tokens. For a narrower question, such as whether a paper should cite X or who first proved a lemma, confirm that the user wants the full review before starting it.
---

<!-- Pointer for Claude Code, which reads project skills from .claude/skills/. Keep the name and description identical to .agents/skills/precedence-review/SKILL.md. -->

This skill's files are in `.agents/skills/precedence-review/` at the root of this repository, where other agents look for skills. Read `.agents/skills/precedence-review/SKILL.md` completely and follow it. Wherever it says `<skill>`, it means that folder, not this one.
