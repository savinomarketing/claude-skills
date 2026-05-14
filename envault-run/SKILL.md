---
name: envault-run
description: >
  Setup, configuration, and security auditing for envault-manager (local SQLite-based
  secret management) and the envault-run runtime injection wrapper. Use when:
  (1) Setting up envault in a new project, (2) Auditing an existing envault setup for
  security gaps, (3) Configuring MCP servers to use envault-run, (4) Configuring
  LaunchAgent plists to inject secrets at runtime, (5) Diagnosing why envault-run isn't
  finding credentials, or (6) Any question about envault var set/get/list workflow.
---

# envault-run Skill

## What this is

**envault-manager** (`npm install -g envault-manager`) is a local-first secret manager
that stores variables in a SQLite database at `~/.envault/envault.db`.
It is NOT the AWS-backed `pratishshr/envault`, NOT the self-hosted `envault.dev` team
tool, and NOT the `envault.net` zero-knowledge tool. No cloud dependency.

**envault-run** is a custom bash wrapper that adds `envault run -- <command>` behavior
that v0.1.0 lacks natively. It reads all variables from the SQLite DB and injects them
into the process environment at runtime without writing anything to disk.

Find the path on any machine: `which envault-run`

## Core Concepts

- Secrets live in `~/.envault/envault.db` (one DB for all projects)
- Each project is identified by its git root path
- Variables scoped by project + environment (default: `"default"`)
- `envault-run` replaces `envault sync` (sync writes a `.env` file to disk, which is insecure)

## Setting Up a New Project

```bash
# 1. From the project's git root:
envault var set API_KEY          # interactive prompt, value never echoed

# 2. Verify (safe: shows masked values only):
envault var list --json 2>/dev/null | jq '[.[].[] | .key]'

# 3. Test injection:
envault-run -- node -e "console.log('KEY present:', !!process.env.API_KEY)"
```

CWD must be a git repository when running envault commands.

## `envault var` subcommand reference (verified May 4, 2026)

The full `envault var` surface, useful for non-`set` operations that come up rarely enough to be guess-prone (the removal verb is `unset`, not `rm`/`delete`/`remove`):

```
envault var list  [-p PROJECT] [--env ENV] [--json]
envault var get   <KEY> [--env ENV]                          # AVOID: exposes value to stdout
envault var set   <KEY> [--env ENV] [--value VALUE] [--multiline]
envault var unset <KEY> [--env ENV]                          # remove a single key
envault var clear [-p PROJECT] [--env ENV] [--yes]           # remove ALL keys in scope (destructive!)
envault var copy  <fromProject> [KEY] [--from-env ENV] [--env ENV]
```

Common flag conventions:
- `--env ENV`: variable scope (default `"default"`); use this if a project uses non-default envs (rare)
- `-p PROJECT`: operate on a different project from the cwd's git root (without changing dir)
- `--json`: list output as JSON (use with `jq` for safe key inspection)

`envault var clear` is destructive at the scope level. Always pair with explicit `--yes` only after confirming scope. Prefer `unset <KEY>` for individual cleanup.

## MCP Server Pattern

In `.mcp.json`, wrap every server that needs credentials:

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "/absolute/path/to/envault-run",
      "args": ["--", "/absolute/path/to/mcp-server-binary"],
      "env": {}
    }
  }
}
```

Get the correct path first (JSON doesn't expand `~` or `$HOME`):

```bash
which envault-run    # copy this into "command"
which node           # or whichever runtime the server uses
```

Claude Code launches MCP servers as subprocesses with no shell context. Without
`envault-run` as the command, the server gets no envault variables.

## LaunchAgent Pattern

LaunchAgent plists don't expand `~` or `$HOME`, so all paths must be absolute. Get your
values first:

```bash
which envault-run              # e.g. /Users/you/.npm-global/bin/envault-run
which node                     # e.g. /usr/local/bin/node
echo $HOME                     # e.g. /Users/you
npm config get prefix          # e.g. /Users/you/.npm-global
echo $HOME/.bun/bin            # e.g. /Users/you/.bun/bin
```

Then fill in the plist:

```xml
<key>ProgramArguments</key>
<array>
    <string>/absolute/path/to/envault-run</string>
    <string>--</string>
    <string>/absolute/path/to/node</string>
    <string>/absolute/path/to/script.js</string>
</array>
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/your-home/.bun/bin:/your-home/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>/your-home</string>
</dict>
```

PATH must include `~/.bun/bin` (envault uses Bun's SQLite) and the npm global bin dir
(envault + envault-run live there). HOME must be set so envault can find `~/.envault/`.

## Key Safety Rules

- **NEVER** `envault var get KEY` directly: it outputs the secret in plaintext to stdout
- **NEVER** `envault sync`: writes `.env` to disk
- **NEVER** ask the user to hand over secret values. Just tell them the variable name(s) to add (e.g., "add PUSHOVER_USER_KEY to envault") and they'll store them themselves
- **SAFE** to list key names: `envault var list --json 2>/dev/null | jq '[.[].[] | .key]'`
- **SAFE** to run: `envault-run -- <command>` (injects at runtime, nothing written)

Deny rules in `.claude/settings.json` should block `envault var get` and `envault sync`.

## Auditing an Existing Setup

See `references/audit-checklist.md` for the full checklist with copy-paste commands.

Quick audit (4 most critical checks):
1. `ls -la ~/.envault/envault.db`: must be `-rw-------` (600)
2. `ls -la ~/.envault/`: directory must be `drwx------` (700)
3. `find ~ -maxdepth 5 -name ".env" ! -path "*/node_modules/*" | xargs ls -la`, then flag non-empty files
4. Verify LaunchAgent PATH includes both `.bun/bin` and `.npm-global/bin`

## Diagnosing envault-run Failures

**`[envault-run] Warning: Could not retrieve envault variables`:**
- In a git repo? `git rev-parse --show-toplevel`
- Project registered? `envault project list`
- Bun in PATH? `which bun`
- Variables exist? `envault var list`

**MCP server can't find credentials:**
- Confirm `envault-run` is `command` (not the server binary)
- Confirm server binary is in `args` after `"--"`
- Restart Claude Code after `.mcp.json` changes

## envault-run Internals

The wrapper:
1. `envault var list --json` → gets key names (masked values)
2. `value=$(envault var get <key>)` → full value in subshell, never hits stdout
3. `export KEY=value` for each
4. `exec "$@"`: replaces self with the target command

The `var get` calls use bash command substitution. Values never appear in process args
or stdout.
