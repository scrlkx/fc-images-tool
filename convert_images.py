#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

# Registry: source extension (lowercase) -> (target extension, save format)
# To add support for a new format, just add an entry here.
CONVERTERS: dict[str, tuple[str, str]] = {
    ".webp": (".png", "PNG"),
    ".avif": (".png", "PNG"),
    ".jpg": (".png", "PNG"),
    ".jpeg": (".png", "PNG"),
}


def convert_file(src: Path, target_ext: str, save_format: str) -> Path:
    dest = src.with_suffix(target_ext)
    with Image.open(src) as img:
        img.save(dest, format=save_format)
    return dest


def convert_directory(directory: Path) -> None:
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    files = [f for f in directory.iterdir() if f.is_file()]
    convertible = [
        (f, *CONVERTERS[f.suffix.lower()])
        for f in files
        if f.suffix.lower() in CONVERTERS
    ]

    if not convertible:
        print("No convertible files found.")
        return

    for src, target_ext, save_format in convertible:
        try:
            dest = convert_file(src, target_ext, save_format)
            print(f"Converted: {src.name} -> {dest.name}")
            if dest != src:
                src.unlink()
        except Exception as e:
            print(f"Failed: {src.name} ({e})", file=sys.stderr)


def remove_background(src: Path, session) -> None:
    with Image.open(src) as img:
        result = remove(img, session=session)
    result.save(src, format="PNG")


def remove_backgrounds(directory: Path) -> None:
    pngs = sorted(
        f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == ".png"
    )

    if not pngs:
        print("No PNG files found for background removal.")
        return

    session = new_session("birefnet-general")
    for png in pngs:
        try:
            remove_background(png, session)
            print(f"Background removed: {png.name}")
        except Exception as e:
            print(f"Failed background removal: {png.name} ({e})", file=sys.stderr)


def crop_objects(directory: Path) -> None:
    pngs = sorted(
        f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == ".png"
    )

    if not pngs:
        print("No PNG files found for cropping.")
        return

    for png in pngs:
        try:
            with Image.open(png) as img:
                if img.mode != "RGBA":
                    continue
                bbox = img.getbbox()
                if bbox is None or bbox == (0, 0, img.width, img.height):
                    continue
                cropped = img.crop(bbox)
            cropped.save(png, format="PNG")
            print(f"Cropped: {png.name}")
        except Exception as e:
            print(f"Failed cropping: {png.name} ({e})", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert WebP, AVIF, and JPEG images to PNG, remove backgrounds, "
            "and crop transparent padding using birefnet-general segmentation."
        )
    )
    parser.add_argument(
        "directory", type=Path, help="Directory containing images to process"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--keep-background",
        action="store_true",
        help="Skip background removal and cropping; only perform format conversion.",
    )
    group.add_argument(
        "--backgrounds-only",
        action="store_true",
        help="Skip format conversion; only perform background removal on existing PNGs.",
    )
    group.add_argument(
        "--crop-only",
        action="store_true",
        help="Skip conversion and background removal; only crop transparent padding from existing PNGs.",
    )
    args = parser.parse_args()

    if not args.backgrounds_only and not args.crop_only:
        convert_directory(args.directory)

    if not args.keep_background and not args.crop_only:
        remove_backgrounds(args.directory)

    if not args.keep_background and not args.backgrounds_only:
        crop_objects(args.directory)


if __name__ == "__main__":
    main()
