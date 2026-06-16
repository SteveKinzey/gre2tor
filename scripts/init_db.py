#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gre2tor.config import load_settings
from gre2tor.db import init_db


def main() -> None:
    settings = load_settings()
    init_db(settings.DATABASE_PATH)
    print(f"Initialized database: {settings.DATABASE_PATH}")


if __name__ == "__main__":
    main()
