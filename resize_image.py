"""Image resizing utility.

Provides a command line tool for shrinking images either individually or in
batch based on directory names.  The behaviour parallels ``resize_video.py``
so that the repository contains a consistent pair of tools.

Usage:

1. **Single file**
   ``resize_image.py path/to/photo.jpg --width 800``
   ``resize_image.py picture.png --resolution 600 --quality 70``

   One of ``--width`` or ``--resolution`` (height) or ``--quality`` must be
   supplied.  The output file is created next to the source with suffixes
   describing the changes (e.g. ``photo_800w_q85.jpg``).

2. **Directory tree**
   ``resize_image.py some/folder``

   The tree is walked recursively.  A target height is inferred from the
   closest ancestor directory whose name looks like a resolution (``720p``,
   ``300`` etc.).  A global ``--quality`` flag may also be provided.

The script uses Pillow (``PIL``); ensure it is installed before running.
"""

import argparse
import os
import re
import sys
from typing import Optional, Tuple

from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


def is_image_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in IMAGE_EXTS


def parse_resolution(res_str: str) -> int:
    """Return a numeric height from strings like ``720p`` or ``4k``.

    Reuses the same logic as ``resize_video`` (height only).  ``4k`` becomes
    ``4000``.  A bare integer is accepted.
    """

    m = re.match(r"^(\d+)([pPkK]?)$", res_str.strip())
    if not m:
        raise ValueError(f"invalid resolution '{res_str}'")
    value = int(m.group(1))
    letter = m.group(2).lower()
    if letter == "k":
        value *= 1000
    return value


def parse_dimension(dim_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse strings like ``800x600`` or ``720p``.

    Returns ``(width, height)`` where either may be ``None`` if unspecified.
    """

    if "x" in dim_str:
        parts = dim_str.lower().split("x", 1)
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError(f"invalid dimension '{dim_str}'")
        return int(parts[0]), int(parts[1])
    # fall back to resolution semantics for height
    return None, parse_resolution(dim_str)


def find_nearest_resolution(directory: str, stop_at: str) -> Optional[int]:
    # identical to video version; copied for convenience
    directory = os.path.abspath(directory)
    stop_at = os.path.abspath(stop_at)
    while True:
        name = os.path.basename(directory)
        try:
            return parse_resolution(name)
        except ValueError:
            pass
        if directory == stop_at or not directory:
            break
        directory = os.path.dirname(directory)
    return None


def make_output_path(
    infile: str,
    height: Optional[int] = None,
    width: Optional[int] = None,
    quality: Optional[int] = None,
) -> str:
    """Generate output filename including options used."""

    base, ext = os.path.splitext(infile)
    parts: list[str] = []
    if height:
        parts.append(f"{height}p")
    if width:
        parts.append(f"{width}w")
    if quality:
        parts.append(f"q{quality}")
    if not parts:
        return infile
    return f"{base}_{'_'.join(parts)}{ext}"


def process_file(
    path: str,
    height: Optional[int] = None,
    width: Optional[int] = None,
    quality: Optional[int] = None,
    dry_run: bool = False,
) -> None:
    """Resize a single image file."""

    if not is_image_file(path):
        print(f"skipping non-image file {path}")
        return
    try:
        with Image.open(path) as im:
            orig_w, orig_h = im.size
            # determine new dimensions
            if width and height:
                new_w, new_h = width, height
            elif width:
                new_w = width
                new_h = int(round(orig_h * width / orig_w))
            elif height:
                new_h = height
                new_w = int(round(orig_w * height / orig_h))
            else:
                print(f"no size specified for {path}, skipping")
                return
    except Exception as e:
        print(f"error opening {path}: {e}")
        return

    out = make_output_path(path, height=height, width=width, quality=quality)
    if os.path.abspath(path) == os.path.abspath(out):
        print(f"input and output would be identical, skipping {path}")
        return

    print(f"resizing {path} -> {out} {new_w}x{new_h}")
    if dry_run:
        return

    with Image.open(path) as im:
        im = im.resize((new_w, new_h), Image.LANCZOS)
        save_kwargs: dict = {}
        if quality is not None and im.format and im.format.upper() in ("JPEG", "JPG"):
            save_kwargs["quality"] = quality
        im.save(out, **save_kwargs)


def process_directory(
    root: str,
    default_quality: Optional[int] = None,
    dry_run: bool = False,
) -> None:
    """Walk ``root`` recursively and resize files in resolution directories."""

    root = os.path.abspath(root)
    for curdir, _, files in os.walk(root):
        height = find_nearest_resolution(curdir, root)
        if height is None:
            continue
        for fname in files:
            path = os.path.join(curdir, fname)
            process_file(path, height=height, quality=default_quality, dry_run=dry_run)


def _parse_cmdline() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch resize images using Pillow")
    p.add_argument("path", help="image file or directory to process")
    p.add_argument(
        "-r", "--resolution", help="target vertical size (e.g. 720p, 300)",
    )
    p.add_argument("-w", "--width", type=int, help="target width in pixels")
    p.add_argument(
        "-q",
        "--quality",
        type=int,
        choices=range(1, 101),
        metavar="[1-100]",
        help="JPEG quality (ignored for other formats)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned operations but do not write files",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_cmdline()
    target = args.path
    if os.path.isfile(target):
        if not (args.resolution or args.width or args.quality):
            sys.exit("error: must supply --resolution/--width or --quality when giving a file")
        h = parse_resolution(args.resolution) if args.resolution else None
        w = args.width
        process_file(target, height=h, width=w, quality=args.quality, dry_run=args.dry_run)
    elif os.path.isdir(target):
        process_directory(target, default_quality=args.quality, dry_run=args.dry_run)
    else:
        sys.exit(f"{target} is not a file or directory")


if __name__ == "__main__":
    main()
