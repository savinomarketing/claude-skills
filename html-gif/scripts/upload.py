#!/usr/bin/env python3
"""
Giphy Upload

Uploads GIFs to Giphy via the Upload API. The destination channel is determined by
the API key (each key is tied to one user/channel account). Set up a channel at
giphy.com first if you want uploads to land somewhere specific.

Requires GIPHY_API_KEY environment variable.

Usage:
    GIPHY_API_KEY=your_key python upload.py <gif_file> [--tags "logo,brand"] [--title "Logo Reveal"]

Examples:
    GIPHY_API_KEY=your_key python upload.py path/to/logo-reveal.gif --tags "logo,brand"
    GIPHY_API_KEY=your_key python upload.py path/to/stat.gif --title "50% Savings" --tags "stats"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


GIPHY_UPLOAD_URL = "https://upload.giphy.com/v2/upload"


def upload_to_giphy(
    gif_path: str,
    tags: str = "",
    title: str = "",
    source_post_url: str = "",
) -> dict:
    """
    Upload a GIF to Giphy via the Upload API.

    Args:
        gif_path: Path to the GIF file
        tags: Comma-separated tags
        title: Display title on Giphy
        source_post_url: Optional URL the GIF is associated with

    Returns:
        Dictionary with upload result including Giphy URL
    """
    api_key = os.environ.get("GIPHY_API_KEY")
    if not api_key:
        print("Error: GIPHY_API_KEY not found in environment.")
        print("Run with: GIPHY_API_KEY=your_key python upload.py <gif>")
        sys.exit(1)

    gif_path = Path(gif_path)
    if not gif_path.exists():
        print(f"Error: File not found: {gif_path}")
        sys.exit(1)

    size_mb = gif_path.stat().st_size / (1024 * 1024)
    if size_mb > 100:
        print(f"Error: File too large ({size_mb:.1f} MB). Giphy limit is 100 MB.")
        sys.exit(1)

    # Build multipart form data
    boundary = "----GiphyUploadBoundary"
    body = bytearray()

    # api_key field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="api_key"\r\n\r\n')
    body.extend(f"{api_key}\r\n".encode())

    # file field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{gif_path.name}"\r\n'.encode())
    body.extend(b"Content-Type: image/gif\r\n\r\n")
    body.extend(gif_path.read_bytes())
    body.extend(b"\r\n")

    # Optional fields
    if tags:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="tags"\r\n\r\n')
        body.extend(f"{tags}\r\n".encode())

    if title:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="title"\r\n\r\n')
        body.extend(f"{title}\r\n".encode())

    if source_post_url:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="source_post_url"\r\n\r\n')
        body.extend(f"{source_post_url}\r\n".encode())

    body.extend(f"--{boundary}--\r\n".encode())

    # Upload
    print(f"Uploading {gif_path.name} ({size_mb:.1f} MB) to Giphy...")

    req = Request(
        GIPHY_UPLOAD_URL,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Upload failed: {e.code} {e.reason}")
        if error_body:
            print(f"  {error_body}")
        sys.exit(1)

    gif_id = result.get("data", {}).get("id", "")
    giphy_url = f"https://giphy.com/gifs/{gif_id}" if gif_id else "unknown"
    media_url = f"https://media.giphy.com/media/{gif_id}/giphy.gif" if gif_id else "unknown"

    print(f"\nUploaded to Giphy!")
    print(f"  Giphy page: {giphy_url}")
    print(f"  Direct URL: {media_url}")
    if tags:
        print(f"  Tags: {tags}")
    if title:
        print(f"  Title: {title}")

    return {
        "id": gif_id,
        "giphy_url": giphy_url,
        "media_url": media_url,
        "tags": tags,
        "title": title,
    }


def main():
    parser = argparse.ArgumentParser(description="Upload GIF to Giphy")
    parser.add_argument("gif_file", help="Path to GIF file")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--title", default="", help="Display title on Giphy")
    parser.add_argument("--source-url", default="", help="Source URL the GIF is associated with")
    args = parser.parse_args()

    upload_to_giphy(
        gif_path=args.gif_file,
        tags=args.tags,
        title=args.title,
        source_post_url=args.source_url,
    )


if __name__ == "__main__":
    main()
