# MEMORY.md - claude-skills

Session memory, dated entries newest first. Read at session start (does not auto-load).

## 2026-07-03

- AGENTS.md-first scaffold added (fleet C4 wave, minimal treatment): AGENTS.md real + CLAUDE.md symlink + this file. Tag `pre-agents-flip` marks the pre-scaffold state.
- envault-run jq extraction bug fixed earlier today (commit 0a64ca1): `keys[]` returned profile names instead of variable keys, so NOTHING was injected post-rebuild. Fixed in all three copies (repo + /opt/homebrew/bin + live skill).
- README stale-fact fix: the wrapper IS in this repo now (`envault-run/scripts/envault-run`, added Jul 1 after the machine loss); the old `~/.npm-global/bin` path is dead.

## 2026-07-01

- Wrapper script itself committed for the first time (b069d70): the original was never committed and died with the old machine. Lesson: the repo is the source of truth, live copies are installs.
- LaunchAgent log-path rule + psql keg-only PATH gotcha added to the envault-run skill (8785e8b).

## Standing

- Three-copy sync discipline (see AGENTS.md rule 2).
- This repo is public; secrets never, examples generic.
