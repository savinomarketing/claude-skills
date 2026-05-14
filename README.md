# Claude Code Skills

A small collection of [Claude Code](https://claude.com/claude-code) skills I've built and use in my own work. Sharing them in case they're useful.

By Joseph Savino, [savinomarketing.com](https://savinomarketing.com).

## What's in here

### [`envault-run/`](envault-run/): Secure local secret management

Setup, configuration, and security auditing for [`envault-manager`](https://www.npmjs.com/package/envault-manager) (local SQLite-based secret storage) paired with a custom `envault-run` wrapper that injects secrets at runtime without ever writing them to disk.

Use it when:
- Setting up envault in a new project
- Auditing an existing envault setup for security gaps
- Configuring MCP servers or LaunchAgent plists to inject secrets at runtime
- Diagnosing why envault-run is not finding credentials

The `envault-run` wrapper itself is a separate tool (not in this repo). It lives at `~/.npm-global/bin/envault-run` on my machine. Source distribution TBD; for now the skill assumes you have it.

### [`html-gif/`](html-gif/): HTML/CSS animations to GIF

Create animated GIFs from HTML/CSS templates. Playwright captures frames from CSS animations, PIL assembles them into optimized GIFs. Optional one-step upload to Giphy.

Use it when you want:
- Branded GIFs for LinkedIn comments, Twitter/X, or Slack
- Logo reveals, stat callouts, animated headlines
- A way to design GIFs using real CSS instead of code-drawn primitives

Comes with a generic demo template you can customize via CSS custom properties.

## How to install a skill

Claude Code looks for skills in `~/.claude/skills/`. Copy whichever skill folder you want into that directory:

```bash
git clone https://github.com/savinomarketing/claude-skills.git
cp -r claude-skills/envault-run ~/.claude/skills/
cp -r claude-skills/html-gif ~/.claude/skills/
```

Restart Claude Code (or reload the project) for the skills to be picked up. You can verify with `/skills` inside Claude Code.

## License

[MIT](LICENSE). Use, modify, redistribute freely.
