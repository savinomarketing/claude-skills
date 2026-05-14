# envault-run Security Audit Checklist

**Read when:** Running a security audit of an envault setup, or setting up envault for
the first time and want to confirm everything is locked down.

## 1. File System Permissions

```bash
# DB file: must be 600 (owner read/write only)
ls -la ~/.envault/envault.db
# Expected: -rw-------

# DB directory: must be 700 (owner only)
ls -la ~/.envault/
# Expected: drwx------

# envault-run wrapper: 755 is fine (no secrets in the script itself)
ls -la $(which envault-run)
```

envault-manager auto-sets `chmod 600` on `envault.db` at startup. Verify it didn't
drift. If wrong: `chmod 600 ~/.envault/envault.db && chmod 700 ~/.envault/`

## 2. No Plaintext .env Files

```bash
# Find non-empty .env files across all projects
find ~ -maxdepth 5 \( -name ".env" -o -name ".env.*" \) \
  ! -name ".env.example" ! -path "*/node_modules/*" 2>/dev/null | xargs ls -la 2>/dev/null
```

For each non-zero file:
- Is it gitignored? (`git check-ignore -v <file>`)
- Does it contain real secrets or is it a placeholder?
- If real secrets: migrate to envault, then delete

**Migration workflow (one project at a time):**

```bash
cd /path/to/project

# 1. Import .env into envault SQLite DB
envault sync --from project

# 2. Verify all keys landed correctly
envault var list --json 2>/dev/null | jq '[.[].[] | .key]'

# 3. Test that envault-run injects them
envault-run -- node -e "console.log('OK')"

# 4. Delete the plaintext file
rm .env

# 5. Confirm it's gone
ls -la .env 2>/dev/null || echo "Deleted."
```

Do NOT run `envault sync` without `--from project`. That direction writes `.env` to
disk, which is the opposite of what you want.

## 3. LaunchAgent PATH Validation (macOS only)

```bash
# Check PATH in all LaunchAgent plists
grep -r "PATH" ~/Library/LaunchAgents/ 2>/dev/null
```

Required in PATH for envault to work in scheduled jobs:
- `$(echo $HOME/.bun/bin)`: envault-manager uses `bun:sqlite`
- `$(npm config get prefix)/bin`: envault and envault-run live here
- `/usr/local/bin`: node (or wherever `which node` resolves)

Get the exact values to paste into plists (they don't expand `~` or `$HOME`):

```bash
echo "bun bin:  $HOME/.bun/bin"
echo "npm bin:  $(npm config get prefix)/bin"
echo "envault:  $(which envault-run)"
echo "node:     $(which node)"
```

Test that envault-run works with a minimal PATH:

```bash
PATH="$HOME/.bun/bin:$(npm config get prefix)/bin:/usr/local/bin:/usr/bin:/bin" \
  HOME=$HOME envault-run -- node -e "console.log('HOME:', process.env.HOME)"
```

## 4. MCP Server Configuration

```bash
# Review .mcp.json for any servers NOT using envault-run
cat .mcp.json | jq '.mcpServers | to_entries[] | {name: .key, command: .value.command}'
```

Any server that needs credentials must have:
- `"command"`: the absolute path from `which envault-run`
- `"args"`: `["--", "<actual-server-binary>"]`

## 5. Claude Code Deny Rules

Check `.claude/settings.json` for Bash deny rules:

```json
{
  "permissions": {
    "deny": [
      "Bash(envault var get*)",
      "Bash(envault sync*)",
      "Bash(*envault var get*)",
      "Bash(cat .env*)",
      "Bash(grep * .env*)"
    ]
  }
}
```

These prevent Claude from accidentally echoing secrets to the terminal.

## 6. .gitignore Coverage

```bash
# For each project with a .env file, verify it's gitignored:
git -C /path/to/project check-ignore -v .env
# Expected: .gitignore:N:.env   /path/to/project/.env
```

All `.env`, `.env.*`, and credential files should be listed in `.gitignore`.

## 7. Disk Encryption (macOS)

```bash
# Verify FileVault is enabled (protects SQLite DB if Mac is stolen)
fdesetup status
# Expected: FileVault is On.
```

FileVault is the last line of defense. Even with 600 permissions, a stolen unlocked
Mac gives direct file access. FileVault encrypts the whole disk at rest.

## 8. envault-run Script Integrity

After installing or modifying envault-run, record its sha256 as a baseline:

```bash
shasum -a 256 $(which envault-run)
```

Store that hash somewhere you trust (password manager, secure note). On future audits,
verify it hasn't changed:

```bash
shasum -a 256 $(which envault-run)
# Compare output to your stored baseline. Any diff means the script was modified
```

If the hash has changed unexpectedly, inspect the script before running it:

```bash
cat $(which envault-run)
```

## 9. Shell History Protection

Secrets typed in the terminal can end up in `~/.zsh_history` or `~/.bash_history`.

**Check zsh is configured to ignore sensitive commands:**

```bash
grep "HIST_IGNORE_SPACE" ~/.zshrc
# Expected: setopt HIST_IGNORE_SPACE
```

If missing, add to `~/.zshrc`:

```bash
setopt HIST_IGNORE_SPACE   # commands prefixed with a space are not saved
setopt HIST_IGNORE_DUPS    # don't save consecutive duplicate commands
```

Then reload: `source ~/.zshrc`

**Usage:** Prefix any command with a space to prevent it from being saved:

```bash
 envault var set MY_SECRET   # leading space = not saved to history
```

**Check for existing secrets in history** (search without revealing values):

```bash
grep -c "envault var set" ~/.zsh_history 2>/dev/null
# If > 0, consider clearing history: history -p && > ~/.zsh_history
```

## Quick Audit Script

Paste this into terminal for a fast pass:

```bash
echo "=== DB permissions ===" && ls -la ~/.envault/envault.db
echo "=== Dir permissions ===" && ls -la ~/.envault/ | head -3
echo "=== envault-run path ===" && which envault-run
echo "=== .env files ===" && find ~ -maxdepth 5 -name ".env" ! -name ".env.example" ! -path "*/node_modules/*" 2>/dev/null | xargs ls -la 2>/dev/null
echo "=== FileVault ===" && fdesetup status 2>/dev/null || echo "(not macOS or fdesetup unavailable)"
echo "=== LaunchAgent PATH ===" && grep -rh "PATH" ~/Library/LaunchAgents/ 2>/dev/null || echo "(no LaunchAgents found)"
```

## Pass/Fail Summary

| Check | Pass condition |
|-------|----------------|
| `~/.envault/envault.db` | `-rw-------` (600) |
| `~/.envault/` directory | `drwx------` (700) |
| Plaintext `.env` files | Zero non-empty files, or all gitignored |
| LaunchAgent PATH | Includes bun bin + npm global bin |
| MCP servers | All credential-needing servers use envault-run |
| Claude deny rules | `envault var get` + `envault sync` blocked |
| FileVault (macOS) | On |
| envault-run integrity | sha256 matches stored baseline |
| Shell history | `HIST_IGNORE_SPACE` set in `.zshrc` |
