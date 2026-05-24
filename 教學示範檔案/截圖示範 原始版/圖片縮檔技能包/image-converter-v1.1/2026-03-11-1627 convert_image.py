import argparse
import os
from pathlib import Path

from PIL import Image, ImageOps


JPEG_QUALITY_STEPS = list(range(95, 25, -5))
RESIZE_SCALE = 0.9
MIN_EDGE = 320
DEFAULT_MAX_KB = 500
DEFAULT_AGGRESSIVE_RATIO = 0.2
DEFAULT_AGGRESSIVE_THRESHOLD = 2.5
DEFAULT_IMPROVEMENT_RATIO = 0.8
SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".gif",
    ".heic",
    ".heif",
    ".avif",
}


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Convert common image formats to JPG. "
            "Default behavior skips files already within 500KB."
        )
    )
    parser.add_argument("input_path", help="Source image or directory path")
    parser.add_argument(
        "--max-kb",
        type=int,
        default=DEFAULT_MAX_KB,
        help=f"Maximum output size in KB (default: {DEFAULT_MAX_KB})",
    )
    parser.add_argument(
        "--mode",
        choices=("smart", "limit", "force-jpg", "aggressive"),
        default="smart",
        help=(
            "smart: keep JPGs already <= max-kb, but test non-JPG files to see if JPG is meaningfully smaller; "
            "limit: skip files already <= max-kb; "
            "force-jpg: always output JPG; "
            "aggressive: for large originals, target the smaller of max-kb or "
            "a ratio of the original size."
        ),
    )
    parser.add_argument(
        "--aggressive-ratio",
        type=float,
        default=DEFAULT_AGGRESSIVE_RATIO,
        help=(
            "When mode=aggressive and the source is much larger than max-kb, "
            "target this ratio of the original size (default: 0.2)."
        ),
    )
    parser.add_argument(
        "--aggressive-threshold",
        type=float,
        default=DEFAULT_AGGRESSIVE_THRESHOLD,
        help=(
            "When mode=aggressive, ratio compression only kicks in if source size "
            "is at least this multiple of max-kb (default: 2.5)."
        ),
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Resize output width in pixels. Keeps aspect ratio unless --height is also set.",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Resize output height in pixels. Keeps aspect ratio unless --width is also set.",
    )
    parser.add_argument(
        "--max-pixels",
        type=int,
        help=(
            "Limit total output pixels. The image is scaled down proportionally until "
            "width * height <= this value."
        ),
    )
    parser.add_argument(
        "--output",
        help="Optional output JPG path. Only valid for single-file input.",
    )
    parser.add_argument(
        "--improvement-ratio",
        type=float,
        default=DEFAULT_IMPROVEMENT_RATIO,
        help=(
            "When mode=smart and the source is not JPG, keep the converted JPG only if "
            "its size is <= source_size * this ratio. Default 0.8 means at least 20%% smaller."
        ),
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When input_path is a directory, include supported images recursively.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "When resizing (--width/--height/--max-pixels), overwrite the original file "
            "instead of creating a new file with '_small' suffix. "
            "WARNING: the original file will be permanently replaced."
        ),
    )
    return parser


def normalize_image(src_path):
    image = Image.open(src_path)
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")
    return image


def resize_to_constraints(image, width=None, height=None, max_pixels=None):
    current = image

    if width or height:
        src_w, src_h = current.size
        if width and height:
            target_size = (width, height)
        elif width:
            target_size = (width, max(1, round(src_h * (width / src_w))))
        else:
            target_size = (max(1, round(src_w * (height / src_h))), height)
        current = current.resize(target_size, Image.LANCZOS)

    if max_pixels and current.width * current.height > max_pixels:
        scale = (max_pixels / float(current.width * current.height)) ** 0.5
        target_size = (
            max(1, round(current.width * scale)),
            max(1, round(current.height * scale)),
        )
        current = current.resize(target_size, Image.LANCZOS)

    return current


def try_save_with_quality(image, dst_path, max_kb):
    final_size = None
    final_quality = None

    for quality in JPEG_QUALITY_STEPS:
        image.save(
            dst_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )
        size_kb = os.path.getsize(dst_path) / 1024
        final_size = size_kb
        final_quality = quality
        if size_kb <= max_kb:
            return True, final_quality, final_size

    return False, final_quality, final_size


def shrink_image(image):
    new_width = max(MIN_EDGE, round(image.width * RESIZE_SCALE))
    new_height = max(MIN_EDGE, round(image.height * RESIZE_SCALE))

    if new_width >= image.width and new_height >= image.height:
        return image

    return image.resize((new_width, new_height), Image.LANCZOS)


def resolve_target_kb(source_kb, max_kb, mode, aggressive_ratio, aggressive_threshold):
    if mode != "aggressive":
        return max_kb

    if source_kb < max_kb * aggressive_threshold:
        return max_kb

    ratio_target = max(1, round(source_kb * aggressive_ratio))
    return min(max_kb, ratio_target)


def should_skip(src, source_kb, max_kb, mode, width, height, max_pixels, output):
    has_transform_override = any(value is not None for value in (width, height, max_pixels, output))
    if has_transform_override:
        return False

    if mode == "force-jpg":
        return False

    if mode == "smart":
        return src.suffix.lower() in (".jpg", ".jpeg") and source_kb <= max_kb

    return source_kb <= max_kb


def build_output_path(src, output=None, has_resize=False, overwrite=False):
    if output:
        return Path(output)

    # When resizing, default to creating a new file with _small suffix
    # to avoid overwriting the original. Use --overwrite to replace in-place.
    if has_resize and not overwrite:
        stem = src.stem
        return src.with_name(f"{stem}_small.jpg")

    return src.with_suffix(".jpg")


def should_keep_smart_result(src, source_kb, result_size_kb, target_kb, improvement_ratio):
    if src.suffix.lower() in (".jpg", ".jpeg"):
        return True

    if source_kb > target_kb:
        return True

    return result_size_kb <= source_kb * improvement_ratio


def convert_image(
    src_path,
    target_kb=DEFAULT_MAX_KB,
    mode="smart",
    aggressive_ratio=DEFAULT_AGGRESSIVE_RATIO,
    aggressive_threshold=DEFAULT_AGGRESSIVE_THRESHOLD,
    improvement_ratio=DEFAULT_IMPROVEMENT_RATIO,
    width=None,
    height=None,
    max_pixels=None,
    output=None,
    overwrite=False,
):
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {src}")

    source_kb = src.stat().st_size / 1024
    if should_skip(src, source_kb, target_kb, mode, width, height, max_pixels, output):
        return {
            "status": "skipped",
            "path": str(src),
            "size_kb": round(source_kb, 2),
            "reason": f"already <= {target_kb}KB",
        }

    has_resize = any(value is not None for value in (width, height, max_pixels))
    dst = build_output_path(src, output=output, has_resize=has_resize, overwrite=overwrite)
    effective_target_kb = resolve_target_kb(
        source_kb, target_kb, mode, aggressive_ratio, aggressive_threshold
    )
    image = normalize_image(src)
    image = resize_to_constraints(image, width=width, height=height, max_pixels=max_pixels)

    while True:
        success, quality, size_kb = try_save_with_quality(image, dst, effective_target_kb)
        if success:
            if mode == "smart" and not should_keep_smart_result(
                src, source_kb, size_kb, target_kb, improvement_ratio
            ):
                if dst.exists() and dst != src:
                    dst.unlink()
                return {
                    "status": "skipped",
                    "path": str(src),
                    "size_kb": round(source_kb, 2),
                    "reason": (
                        "non-JPG source already within limit and JPG result was not "
                        f"at least {(1 - improvement_ratio) * 100:.0f}% smaller"
                    ),
                }
            return {
                "status": "converted",
                "path": str(dst),
                "size_kb": round(size_kb, 2),
                "quality": quality,
                "width": image.width,
                "height": image.height,
                "source_kb": round(source_kb, 2),
                "target_kb": effective_target_kb,
            }

        smaller = shrink_image(image)
        if smaller.size == image.size:
            return {
                "status": "converted",
                "path": str(dst),
                "size_kb": round(size_kb, 2),
                "quality": quality,
                "width": image.width,
                "height": image.height,
                "source_kb": round(source_kb, 2),
                "target_kb": effective_target_kb,
                "warning": (
                    f"Could not reduce below {effective_target_kb}KB without shrinking under "
                    f"{MIN_EDGE}px on one edge."
                ),
            }
        image = smaller


def iter_supported_images(input_path, recursive=False):
    root = Path(input_path)
    if root.is_file():
        yield root
        return

    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.glob("*")

    for path in iterator:
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input_path)

    if not input_path.exists():
        print(f"Error during conversion: File not found: {input_path}")
        return 1

    if input_path.is_dir() and args.output:
        print("Error during conversion: --output can only be used with a single file.")
        return 1

    results = []
    try:
        for src in iter_supported_images(input_path, recursive=args.recursive):
            result = convert_image(
                src,
                target_kb=args.max_kb,
                mode=args.mode,
                aggressive_ratio=args.aggressive_ratio,
                aggressive_threshold=args.aggressive_threshold,
                improvement_ratio=args.improvement_ratio,
                width=args.width,
                height=args.height,
                max_pixels=args.max_pixels,
                output=args.output if input_path.is_file() else None,
                overwrite=args.overwrite,
            )
            results.append(result)
    except Exception as exc:
        print(f"Error during conversion: {exc}")
        return 1

    if not results:
        print("No supported image files found.")
        return 0

    converted_count = 0
    skipped_count = 0
    for result in results:
        if result["status"] == "skipped":
            skipped_count += 1
            print(f"Skipped: {result['path']} ({result['size_kb']:.2f} KB, {result['reason']})")
            continue

        converted_count += 1
        print(
            "Converted: "
            f"{result['path']} ({result['size_kb']:.2f} KB, "
            f"{result['width']}x{result['height']}, quality={result['quality']}, "
            f"target<={result['target_kb']}KB, source={result['source_kb']}KB)"
        )
        if "warning" in result:
            print(f"Warning: {result['warning']}")

    print(
        f"Done. converted={converted_count}, skipped={skipped_count}, total={len(results)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
