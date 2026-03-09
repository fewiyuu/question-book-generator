from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".pdf"}


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.stem.lower())
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    key.append(path.suffix.lower())
    return key


def extract_leading_number(path: Path) -> int | None:
    match = re.match(r"^\D*(\d+)", path.stem)
    return int(match.group(1)) if match else None


def tex_escape_path(path: Path) -> str:
    return path.as_posix()


def detect_background_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    sample_points = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, 0),
        (width // 2, height - 1),
        (0, height // 2),
        (width - 1, height // 2),
    ]
    channels = list(zip(*(rgb.getpixel(point) for point in sample_points)))
    return tuple(sorted(channel)[len(channel) // 2] for channel in channels)


def crop_whitespace(source_path: Path, target_path: Path, tolerance: int = 12, margin: int = 4) -> Path:
    if source_path.suffix.lower() == ".pdf":
        return source_path

    image = Image.open(source_path)
    rgb = image.convert("RGB")
    background = detect_background_color(rgb)
    width, height = rgb.size

    left, top = width, height
    right, bottom = -1, -1

    for y in range(height):
        for x in range(width):
            pixel = rgb.getpixel((x, y))
            if any(abs(pixel[index] - background[index]) > tolerance for index in range(3)):
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)

    if right == -1 or bottom == -1:
        cropped = image.copy()
    else:
        crop_box = (
            max(0, left - margin),
            max(0, top - margin),
            min(width, right + margin + 1),
            min(height, bottom + margin + 1),
        )
        cropped = image.crop(crop_box)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(target_path)
    return target_path


def sort_key(path: Path, mode: str) -> object:
    if mode == "name":
        return natural_key(path)
    stat = path.stat()
    return (stat.st_mtime, stat.st_ctime, natural_key(path))


def build_commands(
    image_dir: Path,
    processed_dir: Path | None,
    start_number: int,
    mode: str,
    use_filename_number: bool,
    auto_crop: bool,
) -> list[str]:
    files = sorted(
        [path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda path: sort_key(path, mode),
    )

    commands: list[str] = []
    next_number = start_number
    for path in files:
        question_number = extract_leading_number(path) if use_filename_number else None
        if question_number is None:
            question_number = next_number
            next_number += 1
        else:
            next_number = question_number + 1

        output_path = path
        if auto_crop:
            if processed_dir is None:
                raise ValueError("processed_dir must be provided when auto_crop is enabled")
            output_path = crop_whitespace(path, processed_dir / path.name)

        commands.append(
            rf"\questionimagepage{{{question_number}}}{{{tex_escape_path(output_path.relative_to(image_dir.parent))}}}"
        )
    return commands


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LaTeX pages from question images.")
    parser.add_argument("--image-dir", default="images", help="Folder containing question images.")
    parser.add_argument("--output", default="questions_generated.tex", help="Generated TeX file path.")
    parser.add_argument("--start", type=int, default=1, help="Starting question number when filenames have no leading number.")
    parser.add_argument(
        "--sort",
        choices=["time", "name"],
        default="time",
        help="How to sort images before generating pages.",
    )
    parser.add_argument(
        "--use-filename-number",
        action="store_true",
        help="Use leading numbers in filenames as question numbers.",
    )
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="Disable automatic whitespace cropping.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    image_dir = (root / args.image_dir).resolve()
    processed_dir = (root / ".build_images").resolve() if not args.no_crop else None
    output_path = (root / args.output).resolve()

    image_dir.mkdir(parents=True, exist_ok=True)
    if processed_dir is not None:
        processed_dir.mkdir(parents=True, exist_ok=True)

    commands = build_commands(
        image_dir,
        processed_dir,
        args.start,
        args.sort,
        args.use_filename_number,
        not args.no_crop,
    )

    lines = [
        "% This file is auto-generated by generate_questions.py.",
        "% Put your question images into the images/ folder and rerun the script.",
        "",
    ]

    if commands:
        lines.extend(commands)
    else:
        lines.extend(
            [
                r"\begin{center}",
                r"\vspace*{8cm}",
                r"{\Large images/ 文件夹里还没有题目图片。}",
                r"\end{center}",
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
