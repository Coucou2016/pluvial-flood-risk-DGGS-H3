#!/usr/bin/env python3
"""Reconstruct the original directory tree from the flat repository.

Reads FILE_INDEX.csv (flat_name -> original_path) and COPIES every file into
its original location under --into (default ./_restored). The flat folder is
never modified.

CSV mirrors (category == "data_mirror") and flat-review docs (category ==
"review_doc", which have no original path) are skipped.
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--into", default="./_restored",
                    help="destination root for the reconstructed tree")
    ap.add_argument("--index", default=str(HERE / "FILE_INDEX.csv"),
                    help="path to FILE_INDEX.csv")
    args = ap.parse_args()

    index_path = Path(args.index)
    if not index_path.is_file():
        raise SystemExit(f"FILE_INDEX.csv not found at {index_path}")

    dest_root = Path(args.into).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    restored = skipped = missing = 0
    with index_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("category") in ("data_mirror", "review_doc"):
                skipped += 1
                continue
            src = HERE / row["flat_name"]
            if not src.is_file():
                missing += 1
                continue
            dest = dest_root / row["original_path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            restored += 1

    print(f"restored {restored} files into {dest_root}")
    print(f"skipped  {skipped} csv mirrors")
    if missing:
        print(f"missing  {missing} (flat file absent)")


if __name__ == "__main__":
    main()
