# Platform Specs & Animation Patterns

## Table of Contents
- Platform Constraints
- Recommended Presets
- Animation Pattern Library
- Template Customization Guide
- Troubleshooting

## Platform Constraints

### LinkedIn (comment GIFs)
- Auto-play in feed (no click needed)
- Loop infinitely
- Max upload: 200 MB (practical limit: under 5 MB for fast loading)
- No official dimension limit, but 480px wide is the sweet spot
- Aspect ratios: square (1:1), landscape (16:9), portrait (4:5) all work
- GIFs render at ~2x on retina displays, so capture at 2x device scale

### Twitter / X
- Max file size: 15 MB
- Max dimensions: 1280x1080
- Max duration: ~30 seconds (but keep social GIFs under 6 seconds for engagement)

### Slack
- Emoji upload: max 128 KB, 128x128 recommended
- Message GIFs: 480x480 typical, no hard limit
- Loop infinitely

### General best practices
- Keep under 3 seconds for comment GIFs (attention span)
- 15 fps balances smoothness and file size
- 64-128 colors is usually enough for branded graphics
- Dark or flat backgrounds compress better than gradients
- Simple motions (fade, slide, scale) read better at small sizes than complex particle effects

## Recommended Presets

| Use Case | Width | Height | FPS | Duration | Colors |
|----------|-------|--------|-----|----------|--------|
| Comment GIF (square) | 480 | 480 | 15 | 2-3s | 128 |
| Comment GIF (wide) | 600 | 340 | 15 | 2-3s | 128 |
| LinkedIn banner anim | 1584 | 396 | 10 | 3-5s | 64 |
| Stat callout | 480 | 270 | 20 | 2s | 64 |
| Slack emoji | 128 | 128 | 15 | 1-2s | 64 |

## Animation Pattern Library

### Staggered Reveal
Elements appear one by one with delay offsets. Works for: logos with parts, lists, stats.
```css
.item:nth-child(1) { animation: fade-in 0.4s ease-out 0.1s forwards; }
.item:nth-child(2) { animation: fade-in 0.4s ease-out 0.25s forwards; }
/* Increment delay by 0.12-0.15s per item */
```

### Counter / Ticker
Numbers count up from 0 to target. Use a CSS counter trick or text content updates.
Best for: stat callouts, percentage improvements, dollar savings.
- Use `animation-fill-mode: forwards` to hold final value
- Ease-out the counting speed (fast start, slow finish)

### Shimmer Sweep
A diagonal light sweep across the final state. Premium feel.
```css
background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%);
animation: sweep 0.6s ease-in-out forwards;
/* translateX from -200px to +200px */
```

### Pulse Glow
Subtle radial glow that breathes. Good for: logo after reveal, CTA emphasis.
```css
background: radial-gradient(ellipse, rgba(255,255,255,0.15) 0%, transparent 70%);
animation: pulse 0.8s ease-in-out forwards;
```

### Slide + Fade
Element slides in from edge while fading in. Clean, professional.
```css
@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

### Wipe Transition
For before/after. A bar sweeps across revealing the "after" state.
Use `clip-path: inset()` animated from `inset(0 100% 0 0)` to `inset(0 0 0 0)`.

## Template Customization Guide

The demo template (`assets/templates/demo.html`) uses CSS custom properties at the top:

```css
:root {
  --bg: #0f172a;             /* Background */
  --accent: #38bdf8;         /* Accent color (dot + shimmer) */
  --text: #f1f5f9;           /* Primary text */
  --muted: rgba(241,245,249,0.65); /* Subtitle */
  --font-heading: ...;
}
```

To customize:
1. Copy `demo.html` to a new filename
2. Swap the CSS custom property values for your brand colors
3. Replace the text content (or swap in an SVG logo)
4. Run `capture.py` with desired dimensions

If you have a custom font, load it via `@font-face` with a local file path, or use Google Fonts with a `<link>` tag at the top of the HTML. The capture script waits for `networkidle` which covers font loading.

## Troubleshooting

GIF too large (over 5 MB):
- Reduce colors: `--colors 64`
- Lower FPS: `--fps 10`
- Shorten duration: `--duration 2`
- Use darker or flatter backgrounds (compress better)

Animation not capturing:
- Ensure CSS animations use `animation` shorthand or longhand properties
- Web Animations API requires standard CSS animations (not JS-driven transforms)
- Check that `animation-fill-mode: forwards` is set for animations that should hold their end state

Blank or static frames:
- The HTML might use JS-driven animations instead of CSS. Convert to CSS `@keyframes`
- Check that `document.getAnimations()` returns animations (test in browser DevTools)

Fonts not loading:
- Use local font files with `@font-face` in the HTML template
- Or use Google Fonts with a `<link>` tag (requires network access during capture)
- The capture script waits for `networkidle` which covers font loading
