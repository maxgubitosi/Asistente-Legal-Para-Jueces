#!/usr/bin/env python3
"""
Dado un directorio con JSONs modificados (e.g. datasets_evaluation/test2/2024)
y el directorio base de los JSONs originales (e.g. datasets/fallos_json/2024),
este srcipt copia todos los originales correspondientes a los modificados 
a una nueva carpeta (default: <modified>_originals), preservando la estructura de carpetas.

Usage:
    python copy_originals.py --modified-dir datasets_evaluation/test2/2024 \
                             --original-base datasets/fallos_json/2024

Optional:
    --output-dir  Explicit output directory (default auto-generated)
    --verbose     Print every file copied / missing
"""

import argparse
import logging
import shutil
from pathlib import Path
from typing import List
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def gather_json_files(base_dir: Path) -> List[Path]:
    """Recursively collect all .json files under a directory."""
    return list(base_dir.rglob("*.json"))


def copy_originals(modified_dir: Path, original_base: Path, output_dir: Path, verbose: bool = False):
    modified_files = gather_json_files(modified_dir)
    total = len(modified_files)
    if total == 0:
        logger.error(f"No JSON files found in {modified_dir}")
        return

    logger.info(f"📁 Modified files found: {total}")
    logger.info(f"🔄 Copying originals into: {output_dir}")

    copied = 0
    missing = 0

    for mod_file in tqdm(modified_files, desc="Copying originals"):
        rel_path = mod_file.relative_to(modified_dir)
        orig_file = original_base / rel_path

        if orig_file.exists():
            dest_file = output_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(orig_file, dest_file)
            copied += 1
            if verbose:
                logger.debug(f"✅ Copied {orig_file} -> {dest_file}")
        else:
            missing += 1
            if verbose:
                logger.warning(f"⚠️ Original not found for {rel_path}")

    logger.info("\n📊 Summary")
    logger.info(f"  Total modified files : {total}")
    logger.info(f"  Originals copied     : {copied}")
    logger.info(f"  Originals missing    : {missing}")


def main():
    parser = argparse.ArgumentParser(description="Copy original JSONs matching a modified dataset directory.")
    parser.add_argument("--modified-dir", required=True, help="Path to modified dataset directory")
    parser.add_argument("--original-base", required=True, help="Base path of original JSONs")
    parser.add_argument("--output-dir", help="Output directory for copied originals (default: <modified>_originals)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    modified_dir = Path(args.modified_dir).expanduser().resolve()
    original_base = Path(args.original_base).expanduser().resolve()

    if not modified_dir.exists():
        logger.error(f"Modified directory not found: {modified_dir}")
        return
    if not original_base.exists():
        logger.error(f"Original base directory not found: {original_base}")
        return

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path(str(modified_dir) + "_originals")
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_originals(modified_dir, original_base, output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main() 