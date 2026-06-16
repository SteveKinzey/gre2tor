#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gre2tor.seed import upsert_seed_data


def main() -> None:
    result = upsert_seed_data()
    print(f"Seeded {result['topics']} topics and {result['cards']} cards.")


if __name__ == "__main__":
    main()
