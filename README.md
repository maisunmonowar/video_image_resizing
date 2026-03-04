# video_image_resizing

Not all videos or photos deserve to be preserved at full quality. This repository provides two command-line tools for batch resizing videos and images—either individually or recursively across directory trees based on folder names.

## Features

- **OS-independent**: Works on Windows, macOS, and Linux
- **Flexible processing**: Single file or batch directory mode
- **Smart directory mode**: Infer target resolution from folder names (e.g., `720p/`, `300/`)
- **Dry-run support**: Preview operations before executing
- **Consistent interface**: Both tools share similar CLI patterns

## Installation

### Requirements

- Python 3.13+
- `ffmpeg` (for video resizing; must be on `PATH`)
- Pillow (for image resizing; installed via pip)

### Setup

```bash
# Clone or download the repository
cd video_image_resizing

# Install dependencies
pip install pillow
```

Ensure `ffmpeg` is installed and accessible from your command line:
```bash
ffmpeg -version
```

## `resize_video.py` – Video Resizing

Batch resize videos using `ffmpeg` with support for resolution and codec changes.

### Single File Mode

Resize a single video to a specific resolution or codec:

```bash
# Resize to 720p height (aspect ratio preserved)
python resize_video.py movie.mp4 -r 720p

# Change codec only
python resize_video.py clip.mov -c libx264

# Resize and change codec
python resize_video.py video.avi -r 480p -c libx265

# Specify exact width (height auto-calculated)
python resize_video.py input.mp4 -w 1280
```

At least one of `--resolution`, `--width`, or `--codec` must be provided for single files.

### Directory Mode

Process all videos in a folder tree based on ancestor folder names:

```bash
python resize_video.py /path/to/videos

# With global codec
python resize_video.py /path/to/videos -c libx264
```

**Directory structure example:**
```
videos/
├── 720p/
│   ├── tutorial1.mp4       → resized to 720px height
│   └── clips/
│       └── intro.mp4        → inherits 720p from ancestor
├── 1080p/
│   └── presentation.mkv     → resized to 1080px height
└── archive/
    └── old_video.avi        → skipped (no resolution folder)
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--resolution RES` | `-r` | Target height (e.g., `720p`, `4k`, `480`) |
| `--width WIDTH` | `-w` | Target width in pixels |
| `--codec CODEC` | `-c` | Video codec (e.g., `libx264`, `libx265`) |
| `--dry-run` | | Print ffmpeg commands without executing |

### Supported Formats

`.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.wmv`, `.webm`, `.mpeg`, `.mpg`

---

## `resize_image.py` – Image Resizing

Batch resize images using Pillow with support for width, height, and quality settings.

### Single File Mode

Resize a single image:

```bash
# Resize to 800px width (height auto-calculated)
python resize_image.py photo.jpg -w 800

# Resize to 300px height
python resize_image.py picture.png -r 300

# Reduce quality
python resize_image.py img.jpg -q 70

# Combine width and quality
python resize_image.py picture.jpg -w 640 -q 80
```

At least one of `--resolution`, `--width`, or `--quality` must be provided for single files.

### Directory Mode

Process all images in a folder tree based on ancestor folder names:

```bash
python resize_image.py /path/to/images

# With global quality reduction
python resize_image.py /path/to/images -q 85
```

**Directory structure example:**
```
photos/
├── 300/
│   ├── thumbnail1.jpg       → resized to 300px height
│   └── set1/
│       └── pic.jpg           → inherits 300px from ancestor
├── 1200/
│   └── hires/
│       └── photo.png         → resized to 1200px height
└── misc/
    └── random.jpg            → skipped (no resolution folder)
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--resolution RES` | `-r` | Target height (e.g., `720p`, `300`, `4k`) |
| `--width WIDTH` | `-w` | Target width in pixels |
| `--quality QUAL` | `-q` | JPEG quality, 1–100 (higher = better) |
| `--dry-run` | | Print planned operations without writing |

### Supported Formats

`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`

---

## Examples

### Example 1: Batch Compress Photos for Web

```bash
# Organize photos in a 600p folder
mkdir -p photos/600
mv my_photos/*.jpg photos/600/

# Resize all to 600px height with 75% quality
python resize_image.py photos -q 75
```

### Example 2: Standardize Video Library by Resolution

```bash
# Organize into folders by target resolution
mkdir -p videos/{480p,720p,1080p}
mv stuff/*.mp4 videos/720p/

# Batch convert all to H.264
python resize_video.py videos -c libx264

# Or preview first
python resize_video.py videos -c libx264 --dry-run
```

### Example 3: Reduce File Sizes Without Re-organizing

```bash
# Single file: convert 4K to 1080p
python resize_video.py recording.mp4 -r 1080p

# Single image: thumbnail
python resize_image.py large_photo.png -w 200
```

---

## Testing

Run the included unit tests:

```bash
pip install pytest
pytest -q
```

Tests cover dimension parsing, file type detection, output naming, and basic resizing operations.

---

## Notes

- **Aspect ratio preservation**: Both scripts maintain the aspect ratio when only one dimension is specified.
- **Output filenames**: Suffixes are appended automatically (e.g., `movie_720p_libx264.mp4`, `photo_800w_q85.jpg`).
- **Dry-run first**: Use `--dry-run` to preview operations before processing large batches.
- **Error handling**: Non-matching files are skipped with a message; invalid options cause early exit.

---

## License

This project is provided as-is. Feel free to modify and distribute.
