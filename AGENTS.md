# AGENTS.md

Entry file for agents working in this repo (Claude Code loads it through the `CLAUDE.md` symlink). Keep it thin; status and history live in `MEMORY.md` (read it at session start; it does not auto-load). Never run `/init` here. Unsure which entry file to edit? `bash ~/brain/scripts/entry-file.sh`.

## What this repo is

Joseph's PUBLIC (MIT) collection of shareable Claude Code skills: `envault-run/` (secret-management skill + the wrapper script) and `html-gif/` (HTML/CSS to GIF pipeline). README.md is the human-facing overview.

## Rules

1. **This repo is PUBLIC.** Never commit secrets, tokens, real credentials, machine-specific paths presented as required, or Hydr8/client-specific data. Examples stay generic. Hydr8-specific skill knowledge belongs in project repos or `~/.claude/skills/`, not here.
2. **envault-run three-copy sync.** The canonical wrapper source is `envault-run/scripts/envault-run` in THIS repo. Live copies that must be updated in the SAME change: `/opt/homebrew/bin/envault-run` (installed binary) and `~/.claude/skills/envault-run/` (live skill copy). A fix that lands in only one copy recreates the drift that hid the July 2026 jq bug.
3. Skill-craft: frontmatter `description` is the highest-leverage line; encode workflows actually repeated, not guesses.

## Pointers

- Status + change history: `MEMORY.md`
- Brain effort note: `~/brain/Efforts/Claude Skills.md`
- Global skills consolidation (Phase E, planned): these skills are candidates for `~/.agents/skills/` with symlinks; see the fleet migration plan in the brain.
