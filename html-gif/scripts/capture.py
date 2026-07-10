#!/usr/bin/env python3
"""
HTML GIF Capture Engine

Renders HTML/CSS animations via Playwright, captures frames, assembles into optimized GIFs.

Usage:
    python capture.py <html_file> <output.gif> [--width 480] [--height 480] [--fps 15] [--duration 2.5] [--colors 128]

Examples:
    python capture.py template.html logo-reveal.gif
    python capture.py template.html stat.gif --width 600 --height 340 --fps 20 --duration 3
"""

import argparse
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def capture_frames(
    html_path: str,
    width: int = 480,
    height: int = 480,
    fps: int = 15,
    duration: float = 2.5,
    device_scale: int = 2,
) -> list[np.ndarray]:
    """
    Open an HTML file in Playwright, step through CSS animations frame by frame,
    and capture screenshots.

    The HTML template should use CSS animations. This script pauses all animations
    via the Web Animations API and seeks to each frame time.

    Args:
        html_path: Path to the HTML animation file
        width: Viewport width in CSS pixels
        height: Viewport height in CSS pixels
        fps: Frames per second to capture
        duration: Total animation duration in seconds
        device_scale: Device pixel ratio (2 = retina, captures at 2x then downscales)

    Returns:
        List of frames as numpy arrays (RGB)
    """
    from playwright.sync_api import sync_playwright

    html_path = str(Path(html_path).resolve())
    total_frames = int(fps * duration)
    frame_interval_ms = 1000.0 / fps
    frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale,
        )

        # Load the HTML file
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")

        # Small delay for fonts/images to settle
        page.wait_for_timeout(300)

        # Pause all CSS animations at time 0
        page.evaluate("""() => {
            const animations = document.getAnimations();
            animations.forEach(a => {
                a.pause();
                a.currentTime = 0;
            });
        }""")

        for i in range(total_frames + 1):
            time_ms = i * frame_interval_ms

            # Seek all animations to this time
            page.evaluate(f"""() => {{
                const animations = document.getAnimations();
                animations.forEach(a => {{
                    a.currentTime = {time_ms};
                }});
            }}""")

            # Brief wait for rendering
            page.wait_for_timeout(16)

            # Capture screenshot as bytes
            screenshot_bytes = page.screenshot(type="png")

            # Convert to PIL Image, then to numpy array
            img = Image.open(__import__("io").BytesIO(screenshot_bytes))

            # Downscale from retina to target size
            if device_scale > 1:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            img = img.convert("RGB")
            frames.append(np.array(img))

        browser.close()

    return frames


def assemble_gif(
    frames: list[np.ndarray],
    output_path: str,
    fps: int = 15,
    num_colors: int = 128,
    loop: int = 0,
    dedup_similarity: float = 0.9995,
) -> dict:
    """
    Assemble captured frames into an optimized GIF.

    Args:
        frames: List of RGB numpy arrays
        output_path: Where to save the GIF
        fps: Playback frames per second
        num_colors: Color palette size (fewer = smaller file)
        loop: Loop count (0 = infinite)

    Returns:
        Dictionary with file info
    """
    import imageio.v3 as imageio

    if not frames:
        raise ValueError("No frames to assemble")

    output_path = Path(output_path)
    frame_duration = 1000 / fps

    # Color quantization with global palette for better compression
    pil_frames = [Image.fromarray(f) for f in frames]

    # Build global palette from sampled frames
    sample_count = min(5, len(pil_frames))
    sample_indices = [int(i * len(pil_frames) / sample_count) for i in range(sample_count)]
    sample_pixels = np.vstack(
        [np.array(pil_frames[i]).reshape(-1, 3) for i in sample_indices]
    )
    total = len(sample_pixels)
    w = min(512, int(np.sqrt(total)))
    h = (total + w - 1) // w
    needed = w * h
    if needed > total:
        sample_pixels = np.vstack([sample_pixels, np.zeros((needed - total, 3), dtype=np.uint8)])
    palette_img = Image.fromarray(sample_pixels[:needed].reshape(h, w, 3).astype(np.uint8))
    global_palette = palette_img.quantize(colors=num_colors, method=2)

    # Apply palette to all frames
    optimized = []
    for pf in pil_frames:
        q = pf.quantize(palette=global_palette, dither=1)
        optimized.append(np.array(q.convert("RGB")))

    # Deduplicate consecutive near-identical frames. Subtle motion in a small
    # region (a wink, a ticking digit) can fall under the default threshold and
    # get eaten; pass a higher --dedup (up to 1.0 = keep everything that
    # changed at all) when the animation has small-area detail.
    deduped = [optimized[0]]
    for i in range(1, len(optimized)):
        diff = np.abs(optimized[i].astype(float) - deduped[-1].astype(float))
        similarity = 1.0 - (np.mean(diff) / 255.0)
        if similarity < dedup_similarity:
            deduped.append(optimized[i])

    # Save
    imageio.imwrite(output_path, deduped, duration=frame_duration, loop=loop)

    size_kb = output_path.stat().st_size / 1024
    size_mb = size_kb / 1024
    h_px, w_px = deduped[0].shape[:2]

    info = {
        "path": str(output_path),
        "size_kb": round(size_kb, 1),
        "size_mb": round(size_mb, 2),
        "dimensions": f"{w_px}x{h_px}",
        "frames": len(deduped),
        "fps": fps,
        "duration_s": round(len(deduped) / fps, 1),
        "colors": num_colors,
    }

    print(f"\nGIF created: {output_path}")
    print(f"  Size: {info['size_kb']} KB ({info['size_mb']} MB)")
    print(f"  Dimensions: {info['dimensions']}")
    print(f"  Frames: {info['frames']} @ {fps} fps ({info['duration_s']}s)")
    print(f"  Colors: {num_colors}")

    if size_mb > 5:
        print(f"\n  Warning: {size_mb:.1f} MB exceeds 5 MB social media recommendation")
        print("  Try: fewer colors, lower fps, shorter duration, or smaller dimensions")

    return info


def preview(file_path: str):
    """Open the GIF in Safari (macOS Preview shows frames as filmstrip, not animated)."""
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Safari", str(file_path)])


def main():
    parser = argparse.ArgumentParser(description="HTML/CSS animation to GIF capture engine")
    parser.add_argument("html_file", help="Path to HTML animation template")
    parser.add_argument("output", help="Output GIF path")
    parser.add_argument("--width", type=int, default=480, help="Width in pixels (default: 480)")
    parser.add_argument("--height", type=int, default=480, help="Height in pixels (default: 480)")
    parser.add_argument("--fps", type=int, default=15, help="Frames per second (default: 15)")
    parser.add_argument("--duration", type=float, default=2.5, help="Duration in seconds (default: 2.5)")
    parser.add_argument("--colors", type=int, default=128, help="Color palette size (default: 128)")
    parser.add_argument("--dedup", type=float, default=0.9995, help="Frame dedup similarity threshold; frames more similar than this to the last kept frame are dropped. Use 1.0 to keep every changed frame, e.g. for small-area motion like a wink (default: 0.9995)")
    parser.add_argument("--scale", type=int, default=2, help="Device scale factor (default: 2, retina)")
    parser.add_argument("--no-preview", action="store_true", help="Skip auto-opening the GIF after creation")
    parser.add_argument("--upload", action="store_true", help="Upload to Giphy after creation (requires GIPHY_API_KEY)")
    parser.add_argument("--tags", default="", help="Giphy tags, comma-separated")
    parser.add_argument("--title", default="", help="Giphy display title")
    args = parser.parse_args()

    print(f"Capturing: {args.html_file}")
    print(f"  {args.width}x{args.height} @ {args.fps}fps, {args.duration}s")

    frames = capture_frames(
        html_path=args.html_file,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=args.duration,
        device_scale=args.scale,
    )

    info = assemble_gif(
        frames=frames,
        output_path=args.output,
        fps=args.fps,
        num_colors=args.colors,
        dedup_similarity=args.dedup,
    )

    if not args.no_preview:
        preview(info["path"])

    if args.upload:
        from upload import upload_to_giphy
        upload_to_giphy(
            gif_path=info["path"],
            tags=args.tags,
            title=args.title,
        )


if __name__ == "__main__":
    main()
