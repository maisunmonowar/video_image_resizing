"""video resizing utility

This module implements a simple command‑line interface for reducing the
resolution (and optionally changing the codec) of videos.  It is intended to
be OS‑independent and uses ``ffmpeg`` under the hood; that binary must be
available on ``PATH``.

Usage patterns:

1. **Single file**
   ``resize_video.py path/to/movie.mp4 --resolution 720p [--codec libx264]``

   The script will transcode ``movie.mp4`` to the requested resolution (height)
   keeping the aspect ratio.  You must supply at least ``--resolution`` or
   ``--codec`` (or both) when targeting an individual file.  The output file is
   created next to the source with a suffix indicating what was changed, e.g.
   ``movie_720p_libx264.mp4``.

2. **Directory tree**
   ``resize_video.py some/parent/folder``

   The tree is walked recursively.  Whenever a directory name resembles a
   vertical resolution (``720p``, ``480``, ``4k`` etc.) that value is treated as
   the height to which every video inside that directory (and its subdirectories)
   should be converted.  Folders without a recognised resolution are ignored.
   Example::

       base/
       ├── 720p/
       │   ├── clip1.mp4          # resized to 720 high
       │   └── deep/
       │       └── clip2.mp4      # also 720 high (inherits from ancestor)
       └── misc/
           └── clip3.mp4          # skipped (no resolution folder)

The ``ffmpeg`` command line is roughly::

    ffmpeg -i in.mp4 -vf scale=<w>:<h> -c:v <codec> out.mp4

The width is set to ``-2`` unless a specific ``--width`` is provided, letting
ffmpeg preserve the aspect ratio.
"""

import argparse
import os
import re
import subprocess
import sys
from typing import Iterable, Optional, Tuple

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm", ".mpeg", ".mpg"}


def is_video_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in VIDEO_EXTS


def parse_resolution(res_str: str) -> int:
    """Return a numeric height extracted from a string like ``720p`` or ``4k``.

    The returned value is the vertical resolution in pixels.  ``4k`` is
    interpreted as ``4000`` (not 2160) because the script has no knowledge of
    exact standards; it merely strips the trailing letter.  A bare number is
    also accepted.
    """

    m = re.match(r"^(\d+)([pPkK]?)$", res_str.strip())
    if not m:
        raise ValueError(f"invalid resolution '{res_str}'")
    value = int(m.group(1))
    letter = m.group(2).lower()
    if letter == "k":
        value *= 1000
    return value


def find_nearest_resolution(directory: str, stop_at: str) -> Optional[int]:
    """Walk up from ``directory`` towards ``stop_at`` looking for a folder
    name that contains a resolution.  Returns the first height found, or
    ``None`` if nothing is discovered.
    """

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


def build_ffmpeg_command(
    infile: str,
    outfile: str,
    height: Optional[int] = None,
    width: Optional[int] = None,
    codec: Optional[str] = None,
) -> list[str]:
    """Construct the ``ffmpeg`` command list for the requested parameters."""

    cmd = ["ffmpeg", "-y", "-i", infile]
    filters: list[str] = []
    if height or width:
        w = width if width else -2
        h = height if height else -2
        filters.append(f"scale={w}:{h}")
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    if codec:
        cmd.extend(["-c:v", codec])
    cmd.append(outfile)
    return cmd


def make_output_path(
    infile: str,
    height: Optional[int] = None,
    width: Optional[int] = None,
    codec: Optional[str] = None,
) -> str:
    """Generate an output filename next to ``infile`` suiting the options."""

    base, ext = os.path.splitext(infile)
    parts: list[str] = []
    if height:
        parts.append(f"{height}p")
    if width:
        parts.append(f"{width}w")
    if codec:
        # sanitize codec name for filesystem
        parts.append(codec.replace("/", "_"))
    if not parts:
        # nothing to change
        return infile
    return f"{base}_{'_'.join(parts)}{ext}"


def process_file(
    path: str,
    height: Optional[int] = None,
    width: Optional[int] = None,
    codec: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Resize a single video file according to the parameters."""

    if not is_video_file(path):
        print(f"skipping non-video file {path}")
        return
    out = make_output_path(path, height=height, width=width, codec=codec)
    if os.path.abspath(path) == os.path.abspath(out):
        print(f"input and output would be identical, skipping {path}")
        return
    cmd = build_ffmpeg_command(path, out, height=height, width=width, codec=codec)
    print("running:", " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def process_directory(
    root: str,
    default_codec: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Walk ``root`` recursively and resize files in resolution directories.

    The height is determined by the nearest ancestor directory with a valid
    resolution name.  ``default_codec`` is applied to all conversions if
    supplied.
    """

    root = os.path.abspath(root)
    for curdir, _, files in os.walk(root):
        height = find_nearest_resolution(curdir, root)
        if height is None:
            continue
        for fname in files:
            path = os.path.join(curdir, fname)
            process_file(path, height=height, codec=default_codec, dry_run=dry_run)


def _parse_cmdline() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch resize videos using ffmpeg")
    p.add_argument("path", help="video file or directory to process")
    p.add_argument(
        "-r", "--resolution", help="target vertical resolution (e.g. 720p, 4k)",
    )
    p.add_argument("-w", "--width", type=int, help="target width in pixels")
    p.add_argument("-c", "--codec", help="video codec (e.g. libx264)")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print ffmpeg commands instead of executing them",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_cmdline()
    target = args.path
    if os.path.isfile(target):
        if not (args.resolution or args.width or args.codec):
            sys.exit("error: must supply --resolution/--width or --codec when giving a file")
        h = parse_resolution(args.resolution) if args.resolution else None
        w = args.width
        process_file(target, height=h, width=w, codec=args.codec, dry_run=args.dry_run)
    elif os.path.isdir(target):
        # directory mode ignores any resolution/width provided on CLI; codec still
        # applies globally
        process_directory(target, default_codec=args.codec, dry_run=args.dry_run)
    else:
        sys.exit(f"{target} is not a file or directory")


if __name__ == "__main__":
    main()
