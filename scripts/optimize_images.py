#!/usr/bin/env python3
"""Convert story illustrations (PNG/JPG) into lightweight WebP files.

Usage:
    python scripts/optimize_images.py SOURCE_DIR images/<story-id> [--quality 80] [--max-size 1200x1800]

Each file keeps its name with a .webp extension and its transparency. Images larger
than --max-size are scaled down; smaller ones are left as they are. Item icons only
need --max-size 384x384. Requires Pillow (`pip install pillow`).
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_size(value: str) -> tuple[int, int]:
    width, _, height = value.lower().partition("x")
    try:
        return int(width), int(height)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected WIDTHxHEIGHT, got {value!r}")


def optimize(source: Path, target_dir: Path, quality: int, max_size: tuple[int, int]) -> tuple[int, int]:
    image = Image.open(source)
    image.load()
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
    image = image.convert("RGBA" if has_alpha else "RGB")
    image.thumbnail(max_size, Image.LANCZOS)
    target = target_dir / f"{source.stem}.webp"
    image.save(target, "WEBP", quality=quality, method=6)
    return source.stat().st_size, target.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--quality", type=int, default=80)
    parser.add_argument("--max-size", type=parse_size, default=(1200, 1800))
    args = parser.parse_args()

    files = sorted(p for p in args.source.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not files:
        print(f"No images found in {args.source}", file=sys.stderr)
        return 1

    args.target.mkdir(parents=True, exist_ok=True)
    before = after = 0
    failed = []
    for file in files:
        try:
            original, optimized = optimize(file, args.target, args.quality, args.max_size)
        except OSError as error:
            failed.append(file.name)
            print(f"FAILED {file.name}: {error}", file=sys.stderr)
            continue
        before += original
        after += optimized
        print(f"{file.name}: {original // 1024} KB -> {optimized // 1024} KB")

    print(f"Total: {before / 1024 / 1024:.1f} MB -> {after / 1024 / 1024:.2f} MB")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
