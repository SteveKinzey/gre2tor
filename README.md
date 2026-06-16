# GRE2Tor

GRE2Tor (GRE Tutor) is a local GRE math flashcard and quiz app built with Flask and SQLite. It is designed for fast practice, spaced review, and PDF-grounded question-bank growth from the Sherpa Math Bible source PDFs.

## Current status

- 14 GRE math topic areas.
- 698 seed flashcards.
- 642 PDF-grounded cards with source PDF, source page, and source excerpt metadata.
- A local Flask web UI for browsing topics, studying cards, taking quizzes, and reviewing missed/due cards.
- SQLite persistence for attempts, progress, mastery, and next-review scheduling.
- PDF ingestion tools for extracting source text and creating draft authoring files.

## Tech stack

- Python 3
- Flask
- SQLite
- Jinja templates
- Vanilla JavaScript
- Pytest
- pypdf for PDF text extraction

## Project structure

```text
app.py                     Flask entrypoint
gre2tor/                   Application package
  config.py                Environment/settings loader
  db.py                    SQLite schema, migrations, queries, progress helpers
  models.py                Dataclasses
  pdf_ingest.py            PDF extraction and draft-card helpers
  quiz.py                  Quiz selection, answer evaluation, progress updates
  seed.py                  JSON seed loading and validation

data/seed/                 Committed curated seed data
  topics.json              Topic list and expected PDF filenames
  cards.json               Flashcard bank

data/extracted/            Ignored generated PDF extraction JSON
data/drafts/               Ignored generated draft authoring JSON
scripts/                   CLI helpers
templates/                 Flask/Jinja pages
static/                    CSS and JavaScript
tests/                     Pytest suite
```

## Download and run

GRE2Tor is a local web app. You run it on a Mac or Windows computer, then use it in a browser. A phone or tablet can use it too if it is on the same Wi-Fi network as the computer running the app.

### macOS

1. Download or clone this repo.
2. Open the folder in Finder.
3. Double-click `Start GRE2Tor.command`.
4. If macOS blocks the file because it came from the internet, right-click it, choose **Open**, then confirm.

The launcher creates a local Python environment, installs dependencies, seeds the flashcards, starts the app, and opens your browser.

### Windows

1. Download or clone this repo.
2. Open the folder in File Explorer.
3. Double-click `Start GRE2Tor.bat`.

The launcher creates a local Python environment, installs dependencies, seeds the flashcards, starts the app, and opens your browser.

### Phone or tablet access

After starting GRE2Tor on your computer, the terminal prints two URLs:

```text
Open on this computer: http://127.0.0.1:5000
Open on a phone/tablet on the same Wi-Fi: http://YOUR-COMPUTER-IP:5000
```

On your phone or tablet, connect to the same Wi-Fi network and open the second URL in Safari, Chrome, or another browser.

Notes:

- The computer must stay awake while you study from a phone.
- Some firewalls may ask whether Python can accept local network connections. Allow it for private/local networks.
- This is not yet a packaged native iOS/Android app; mobile use is through the browser.

## Manual setup

Use this if you prefer running commands yourself.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
python scripts/seed_db.py
python scripts/run_local.py
```

Then open:

```text
http://127.0.0.1:5000
```

The default SQLite database is:

```text
instance/gre2tor.sqlite3
```

## Environment variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Available settings:

```text
PDF_SOURCE_DIR="/path/to/Math Bible (1)"
DATABASE_PATH="instance/gre2tor.sqlite3"
FLASK_DEBUG=1
SECRET_KEY="change-me-for-local-dev"
```

Do not commit `.env`; it is ignored.

## Common commands

Initialize the database:

```bash
python scripts/init_db.py
```

Load or refresh seed topics/cards:

```bash
python scripts/seed_db.py
```

Run the app for local/network browser access:

```bash
python scripts/run_local.py
```

Run the Flask entrypoint directly for development:

```bash
python app.py
```

Run tests:

```bash
PYTHONPATH=. pytest
```

If using the bundled virtualenv:

```bash
PYTHONPATH=. venv/bin/pytest
```

## Flashcard data model

Seed cards live in `data/seed/cards.json`.

Important fields:

```json
{
  "id": "unique-card-id",
  "topic_id": "algebra",
  "type": "multiple_choice",
  "prompt": "Question shown to the learner",
  "answer": "Exact correct answer value",
  "choices": ["A choice", "B choice", "C choice", "D choice", "E choice"],
  "explanation": "How the answer is found",
  "difficulty": 2,
  "source_pdf": "Part 02_Algebra.pdf",
  "source_page": 12,
  "source_excerpt": "Concise source text excerpt",
  "grounding_status": "grounded",
  "concept_id": "stable-concept-id",
  "variant_kind": "base",
  "tags": ["pdf-example"]
}
```

Card types currently supported by the app:

- `multiple_choice` — primary format for GRE-style cards.
- `numeric` — legacy exact-match typed answer.
- `problem` — legacy/self-study problem type.
- `theory` — concept recall/self-grade style.

For new GRE cards, prefer `multiple_choice` with exactly five choices.

## Quiz and review behavior

The quiz system supports these modes:

- `all` — mixed card pool.
- `new` — cards with no attempts.
- `missed` — cards previously answered incorrectly.
- `review` — cards due for review or below mastery.

Progress is stored per card in SQLite:

- seen count
- correct count
- incorrect count
- streak
- mastery level
- last seen timestamp
- next review timestamp

Seeding is idempotent and preserves attempts/progress.

## PDF ingestion workflow

Source PDFs are intentionally not committed to the repo. By default, the app expects them at:

```text
/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)
```

Extract all expected PDFs:

```bash
python scripts/ingest_pdfs.py
```

Use a custom folder:

```bash
python scripts/ingest_pdfs.py --source-dir "/path/to/Math Bible (1)"
```

Also create draft page-level authoring files:

```bash
python scripts/ingest_pdfs.py --draft-cards
```

Generated files are ignored:

```text
data/extracted/*.json
data/drafts/*.json
```

Only reviewed, curated cards should be promoted into `data/seed/cards.json`.

## Current source coverage

The 14 PDFs currently extract to 545 pages. A conservative parser found 642 clean quoted question/answer examples and promoted them into the seed deck as PDF-grounded cards.

There are more `Answer:` markers in the PDFs than promoted cards. Those remaining examples likely require a broader parser and manual cleanup because PDF text extraction can flatten formulas, tables, answer choices, and multi-line worked examples.

## Data and security notes

- Do not commit raw PDFs.
- Do not commit `.env`.
- Do not commit local SQLite databases under `instance/`.
- Treat any future user progress, private notes, or source documents as local/private data.

## Development notes

Before changing card behavior or schema:

1. Read the existing tests.
2. Make the smallest safe change.
3. Run `PYTHONPATH=. pytest`.
4. Re-run `python scripts/seed_db.py` if seed data changed.

## License

See `LICENSE`.
