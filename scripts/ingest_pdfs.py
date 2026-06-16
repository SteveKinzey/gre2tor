#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gre2tor.pdf_ingest import DEFAULT_DRAFTS_DIR, DEFAULT_EXTRACTED_DIR, extract_all_pdfs, write_draft_cards


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract GRE Math Bible PDFs into repo-local JSON files.")
    parser.add_argument("--source-dir", help="Folder containing the Part 01 through Part 14 PDFs.")
    parser.add_argument("--out-dir", default=str(DEFAULT_EXTRACTED_DIR), help="Directory for extracted page JSON.")
    parser.add_argument("--draft-cards", action="store_true", help="Also create draft card JSON in data/drafts/.")
    parser.add_argument("--draft-out-dir", default=str(DEFAULT_DRAFTS_DIR), help="Directory for draft card JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = extract_all_pdfs(source_dir=args.source_dir, out_dir=args.out_dir)
    inventory = result["inventory"]
    extracted = result["extracted"]
    errors = result["errors"]

    print(f"PDF source: {result['source_dir']}")
    print(f"Found PDFs: {len(inventory['found'])}")

    if inventory["missing"]:
        print("Missing expected PDFs:", file=sys.stderr)
        for filename in inventory["missing"]:
            print(f"  - {filename}", file=sys.stderr)

    if inventory["unexpected"]:
        print("Unexpected PDFs:", file=sys.stderr)
        for filename in inventory["unexpected"]:
            print(f"  - {filename}", file=sys.stderr)

    for item in extracted:
        print(f"Extracted {item['pdf_filename']} -> {item['output_path']} ({item['page_count']} pages)")

    if errors:
        print("Extraction warnings/errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error['pdf_filename']}: {error['error']}", file=sys.stderr)

    if args.draft_cards and extracted:
        draft_outputs = write_draft_cards(extracted, out_dir=args.draft_out_dir)
        for output in draft_outputs:
            print(f"Drafted {output['count']} cards -> {output['path']}")

    if not extracted:
        print("No expected PDFs were extracted.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
