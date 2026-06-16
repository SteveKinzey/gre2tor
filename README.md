# GRE2Tor

Local GRE math flashcards and quiz practice built with Flask and SQLite.

## Status

This app includes the database schema, seed loader, starter seed data, local web UI, quiz/self-grading flow, progress tracking, and a PDF ingestion pipeline that extracts source PDFs into repo-local JSON for card authoring.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
python scripts/seed_db.py
python app.py
```

The default SQLite database path is `instance/gre2tor.sqlite3`.

## Seed workflow

Seed files live in:

- `data/seed/topics.json`
- `data/seed/cards.json`

Run this any time seed content changes:

```bash
python scripts/seed_db.py
```

Seeding upserts topics/cards by stable IDs and preserves attempts/progress.

## PDF ingestion workflow

The source PDFs live outside the repo by default:

```text
/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)
```

Extract page text into `data/extracted/`:

```bash
python scripts/ingest_pdfs.py
```

Use a custom source folder if needed:

```bash
python scripts/ingest_pdfs.py --source-dir "/path/to/Math Bible (1)"
```

Create draft authoring placeholders in `data/drafts/` as well:

```bash
python scripts/ingest_pdfs.py --draft-cards
```

The ingestion script validates expected vs. missing/unexpected PDFs, continues if one PDF/page has extraction issues, and exits non-zero only when no expected PDFs can be extracted.

## Generated data policy

Do not commit raw PDFs or generated extraction output. These are ignored by `.gitignore`:

- `data/extracted/*.json`
- `data/drafts/*.json`
- `instance/`

Keep curated, original flashcards in `data/seed/cards.json`. Draft JSON is only an authoring aid and should be reviewed before any content is promoted to seed data.

## Tests

```bash
pytest
```

Tests cover seed validation/idempotency, SQLite helpers, quiz/progress behavior, and PDF ingestion/draft JSON helpers.

## Notes

- Starter cards are concise original study material, not copied PDF passages.
- PDF text extraction quality varies for math-heavy files; inspect draft excerpts before authoring cards.
