---
name: html-gif
description: Create animated GIFs from HTML/CSS templates using Playwright to capture frames. Use when the user asks to "create a GIF", "make an animated logo", "build a comment GIF", "animate text or stats", or needs polished branded visual content for social media.
---

# HTML GIF Creator

Create animated GIFs from HTML/CSS templates. Playwright captures frames from CSS animations, PIL assembles them into optimized GIFs. Optional one-step upload to Giphy.

Why this approach: CSS animations are easier to design and tune than code-drawn primitives. You get real typography, gradients, blend modes, SVG, and the full browser rendering pipeline. The trade-off is a Playwright dependency.

## Workflow

### 1. Choose or create a template

Start from `assets/templates/demo.html` and modify it, or create a new HTML file.

Template rules (critical):
- Use CSS `@keyframes` animations, not JavaScript-driven ones. The capture script uses the Web Animations API (`document.getAnimations()`) which cannot seek JS-driven animations.
- Set `animation-fill-mode: forwards` so end states hold after the animation completes.
- Keep total animation duration under 3 seconds for social/comment GIFs.
- Body dimensions must match the `--width` and `--height` you pass to the capture script.
- Load fonts locally with `@font-face` for reliability, or use Google Fonts with a `<link>` tag (the capture script waits for `networkidle`).

### 2. Capture and assemble

```bash
python3 scripts/capture.py <template.html> <output.gif> [options]
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--width` | 480 | Width in CSS pixels |
| `--height` | 480 | Height in CSS pixels |
| `--fps` | 15 | Frames per second |
| `--duration` | 2.5 | Animation duration in seconds |
| `--colors` | 128 | Color palette size (fewer = smaller file) |
| `--scale` | 2 | Device pixel ratio (2 = retina quality) |
| `--no-preview` | off | Skip auto-opening the GIF on Mac after creation |
| `--upload` | off | Upload to Giphy after creation (requires GIPHY_API_KEY) |
| `--tags` | (empty) | Giphy tags, comma-separated (used with --upload) |
| `--title` | (empty) | Giphy display title (used with --upload) |

Common presets:

```bash
# Square comment GIF (default)
python3 scripts/capture.py template.html out.gif

# Wide comment GIF
python3 scripts/capture.py template.html out.gif --width 600 --height 340

# Stat callout (compact, fast)
python3 scripts/capture.py template.html out.gif --width 480 --height 270 --fps 20 --duration 2 --colors 64
```

### 3. Upload to Giphy (optional)

Add `--upload` to push the GIF directly to your Giphy channel. The Giphy API key controls which channel receives the upload, so set up a channel first at giphy.com if you want the GIFs to land somewhere specific.

```bash
# Capture and upload in one command
GIPHY_API_KEY=your_key python3 scripts/capture.py template.html out.gif --upload --tags "logo,brand" --title "Logo Reveal"

# Or upload an existing GIF separately
GIPHY_API_KEY=your_key python3 scripts/upload.py path/to/your.gif --tags "logo,brand"
```

After upload, the script prints the Giphy page URL and direct media URL.

Note on Giphy indexing: new uploads on standard API keys are not indexed for public search until your channel reaches Verified, Artist, or Partner status. Share via direct URL until then.

### 4. Validate output

- Target: under 5 MB for social media (LinkedIn, Twitter)
- If too large: reduce `--colors`, `--fps`, or `--duration`
- Dark or flat backgrounds compress significantly better than gradients
- Output file path and size are printed by the script

## Template Design Rules

CSS animation requirements:
- Use the CSS `animation` property with `@keyframes`. The capture script calls `document.getAnimations()` to enumerate and seek them.
- Default `animation-play-state: running` (the script pauses them programmatically before seeking).
- Use `animation-fill-mode: forwards` to hold end states.
- Do NOT use JavaScript `requestAnimationFrame`, GSAP, or canvas-based animations. The Web Animations API cannot seek those.

Customizing the demo template:
1. Copy `assets/templates/demo.html` to a new filename
2. Update the CSS custom properties at the top (`--bg`, `--accent`, `--text`, fonts)
3. Replace the text or SVG content
4. Run `capture.py` with desired dimensions

See `references/specs-and-patterns.md` for animation pattern recipes (staggered reveal, shimmer sweep, counter ticker, slide+fade, wipe transition) and platform-specific specs (LinkedIn, Twitter, Slack).

## Dependencies

```bash
pip install playwright pillow imageio numpy
playwright install chromium
```

Playwright needs Chromium installed (one-time, ~150 MB). The capture runs headless so nothing pops up on screen.

## Programmatic Usage

The capture functions can also be imported:

```python
from scripts.capture import capture_frames, assemble_gif, preview

frames = capture_frames("template.html", width=480, height=480, fps=15, duration=2.5)
info = assemble_gif(frames, "output.gif", fps=15, num_colors=128)
preview(info["path"])  # Opens the GIF on Mac
```

The GIF auto-opens on Mac after every capture (uses the `open` command with Safari, since macOS Preview shows GIFs as a filmstrip instead of animating them). Pass `--no-preview` to suppress.
