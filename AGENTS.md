# Notes for agents working in this repository

This repository mirrors the openai/math release of mathematics manuscripts (`preprints/`, `reasoning_traces/`, `CONTENTS.md`, `overview.pdf`). It also holds precedence reviews of some of those preprints, published next to them in `preprints/<preprint>/`, and the skill that produces them.

- **Precedence reviews.** To run, resume, check or publish a review, read `.agents/skills/precedence-review/SKILL.md` completely and follow it.
- **The clone may be partial** (blobless and sparse). Don't run git commands that read every file's contents, such as `git ls-tree -l`, `git grep <rev>` or `git log -p`: they download the whole history. The skill's `references/environment.md` has the details.
- **Local working areas.** `reviews/` (review working files) and `prior-work/` (the library of earlier papers shared by reviews) are gitignored and stay on this machine.
- **Ask before you commit, push or open a pull request.**
