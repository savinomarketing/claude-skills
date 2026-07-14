#!/usr/bin/env python3
"""
SVG -> animated GIF template builder.

Turns a static vector brandmark (e.g. a Recraft-generated .svg) into an
animation-ready HTML template that capture.py can render into a GIF. This is
the "Recraft -> GIF" bridge: generate a mark in Recraft, then one command
animates it, no hand-editing of HTML.

Two jobs:
  1. clean_svg()      -- strip the white background rect Recraft prepends,
                         and make the <svg> scale to its container.
  2. build_template() -- wrap the cleaned SVG in a CSS keyframe animation
                         (one of the ANIM presets) and return an HTML string.

Presets (see ANIMATIONS):
  fill     water rises from the bottom, then a glow-pulse settle (great for droplets)
  pop      bouncy scale-in from nothing with a fade
  draw     left-to-right wipe reveal
  stagger  each path fades + rises in sequence (uses per-path animation-delay)
  spin     3D flip-in on the Y axis
  float    fade-in, then a gentle continuous bob (looping)

Thin-band motion presets (fill, draw, stagger) should be rendered with
--dedup 1.0; capture.py defaults to that automatically for them.
"""

import re
from pathlib import Path

# Presets whose motion lives in a small/thin band each frame. The default frame
# dedup (0.9995) treats those near-identical and silently drops them, so
# capture.py bumps dedup to 1.0 for these unless the user overrides --dedup.
THIN_BAND_ANIMS = {"fill", "draw", "stagger"}

DEFAULT_BG = "#071e33"  # deep HYDR8/Elev8 navy; override with --bg


def clean_svg(svg_text: str) -> tuple[str, int]:
    """Strip Recraft's white background rect and make the SVG fill its box.

    Returns (cleaned_svg, path_count). path_count is the number of <path>
    elements remaining after the background is removed (used by the stagger
    preset to space out per-path delays).
    """
    # Recraft opens every vector with a full-canvas white rect. Drop it so the
    # GIF background (brand navy or whatever --bg sets) shows through.
    svg_text = re.sub(
        r'<path[^>]*d="M\s*0\s*0\s*L\s*\d+\s*0[^>]*'
        r'fill="rgb\(255,\s*255,\s*255\)"[^>]*>\s*</path>\s*',
        "",
        svg_text,
        count=1,
    )
    # Scale to container instead of the intrinsic 1024px, and letterbox-fit
    # rather than Recraft's non-uniform "none".
    svg_text = svg_text.replace('preserveAspectRatio="none"', 'preserveAspectRatio="xMidYMid meet"')
    svg_text = re.sub(r'\bwidth="\d+(\.\d+)?"', 'width="100%"', svg_text, count=1)
    svg_text = re.sub(r'\bheight="\d+(\.\d+)?"', 'height="100%"', svg_text, count=1)

    path_count = len(re.findall(r"<path\b", svg_text))
    return svg_text, path_count


def _stagger_delays(svg_text: str, path_count: int, total_s: float) -> str:
    """Inject an incremental animation-delay onto each <path> for the stagger
    preset. Each path is a `.mark path` targeted by the CSS below; the delay is
    what actually sequences them."""
    if path_count <= 1:
        return svg_text
    step = total_s / path_count
    idx = {"n": 0}

    def add_delay(m: re.Match) -> str:
        delay = round(idx["n"] * step, 3)
        idx["n"] += 1
        tag = m.group(0)
        # append to an existing style="" or add one
        if "style=" in tag:
            return re.sub(r'style="([^"]*)"', rf'style="\1;animation-delay:{delay}s"', tag, count=1)
        return tag[:-1] + f' style="animation-delay:{delay}s">'

    return re.sub(r"<path\b[^>]*>", add_delay, svg_text)


# Each preset returns (css_for_mark, extra_css). css_for_mark styles the
# `.mark` wrapper (or `.mark path` for stagger). Keep durations in sync with
# the --duration you pass to capture.py.
def _css_fill(dur: float) -> str:
    fill_s = round(dur * 0.72, 2)
    settle_delay = fill_s
    return f"""
  .mark {{
    clip-path: inset(100% 0 0 0);
    animation: fill {fill_s}s cubic-bezier(.22,.61,.36,1) forwards,
               settle 0.5s ease-out {settle_delay}s forwards;
  }}
  @keyframes fill {{ 0% {{ clip-path: inset(100% 0 0 0); }} 100% {{ clip-path: inset(0% 0 0 0); }} }}
  @keyframes settle {{
    0%   {{ transform: scale(1.0);  filter: drop-shadow(0 0 26px rgba(48,132,192,0)); }}
    45%  {{ transform: scale(1.05); filter: drop-shadow(0 0 26px rgba(48,132,192,.55)); }}
    100% {{ transform: scale(1.0);  filter: drop-shadow(0 0 14px rgba(48,132,192,.35)); }}
  }}"""


def _css_pop(dur: float) -> str:
    return f"""
  .mark {{ opacity: 0; animation: pop {round(dur*0.55,2)}s cubic-bezier(.34,1.56,.64,1) forwards; }}
  @keyframes pop {{
    0%   {{ opacity: 0; transform: scale(0.2); }}
    60%  {{ opacity: 1; transform: scale(1.08); }}
    100% {{ opacity: 1; transform: scale(1.0); }}
  }}"""


def _css_draw(dur: float) -> str:
    return f"""
  .mark {{ clip-path: inset(0 100% 0 0); animation: wipe {round(dur*0.8,2)}s cubic-bezier(.22,.61,.36,1) forwards; }}
  @keyframes wipe {{ 0% {{ clip-path: inset(0 100% 0 0); }} 100% {{ clip-path: inset(0 0% 0 0); }} }}"""


def _css_stagger(dur: float) -> str:
    return f"""
  .mark path {{ opacity: 0; transform: translateY(24px); animation: rise {round(dur*0.35,2)}s ease-out forwards; }}
  @keyframes rise {{ to {{ opacity: 1; transform: translateY(0); }} }}"""


def _css_spin(dur: float) -> str:
    return f"""
  .stage {{ perspective: 900px; }}
  .mark {{ opacity: 0; transform-style: preserve-3d; animation: flip {round(dur*0.6,2)}s cubic-bezier(.22,.61,.36,1) forwards; }}
  @keyframes flip {{
    0%   {{ opacity: 0; transform: rotateY(90deg) scale(0.8); }}
    100% {{ opacity: 1; transform: rotateY(0deg) scale(1.0); }}
  }}"""


def _css_float(dur: float) -> str:
    return f"""
  .mark {{ opacity: 0; animation: appear {round(dur*0.4,2)}s ease-out forwards, bob 2.4s ease-in-out {round(dur*0.4,2)}s infinite; }}
  @keyframes appear {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}"""


ANIMATIONS = {
    "fill": _css_fill,
    "pop": _css_pop,
    "draw": _css_draw,
    "stagger": _css_stagger,
    "spin": _css_spin,
    "float": _css_float,
}


def build_template(
    svg_path: str,
    anim: str = "fill",
    width: int = 800,
    height: int = 800,
    bg: str = DEFAULT_BG,
    pad: float = 0.78,
    duration: float = 2.9,
) -> str:
    """Build a full HTML document animating the given SVG with the named preset.

    Args:
        svg_path: path to the (Recraft) .svg file
        anim: preset name from ANIMATIONS
        width/height: canvas size in CSS px (match capture.py --width/--height)
        bg: page background color (the mark's transparent areas show this)
        pad: fraction of the canvas the mark occupies (0.78 = 11% margin each side)
        duration: total animation seconds (match capture.py --duration)
    """
    if anim not in ANIMATIONS:
        raise ValueError(f"Unknown --anim '{anim}'. Choose from: {', '.join(ANIMATIONS)}")

    svg_text = Path(svg_path).read_text()
    svg_text, path_count = clean_svg(svg_text)

    if anim == "stagger":
        svg_text = _stagger_delays(svg_text, path_count, duration * 0.55)

    mark_css = ANIMATIONS[anim](duration)
    stage_px = int(min(width, height) * pad)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  html, body {{ margin: 0; }}
  body {{ width: {width}px; height: {height}px; background: {bg};
         display: flex; align-items: center; justify-content: center; }}
  .stage {{ width: {stage_px}px; height: {stage_px}px; display: flex;
            align-items: center; justify-content: center; }}
  .mark {{ width: 100%; height: 100%; }}
{mark_css}
</style></head><body>
  <div class="stage"><div class="mark">{svg_text}</div></div>
</body></html>"""
