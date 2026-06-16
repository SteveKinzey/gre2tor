## Final Prompt
<taskname="GRE Flashcards"/>
<task>
Create a greenfield flashcard/quiz system in the empty repo at `/Users/skinzey/code/gre2tor`. The app should help users learn theory and solve problems from the PDFs in `/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)`.

Source PDFs are described as `Part 01_Fractions & Decimals.pdf` through `Part 14_Probability.pdf`, covering Fractions & Decimals, Algebra, Geometry, Percents, Word Problems, Ratios & Proportions, Rates, Statistics, Integer Properties, Sequences & Functions, Overlapping Sets, Combinatorics, and Probability.

Build a pragmatic, maintainable local app with minimal dependencies. It should support ingesting or seeding flashcards/quizzes from those PDFs, organizing content by topic, quizzing both theory and problem-solving, tracking progress, and presenting a usable local UI.
</task>

<architecture>
The repository is empty from RepoPrompt's view: no app files, package files, config files, tests, or Git metadata were present in the loaded root. The next model should choose and scaffold the stack/package manager from scratch.

Recommended constraints from the user/context:
- Prefer a small, practical solution over a broad platform.
- Preserve maintainability and avoid unnecessary dependencies.
- Since the PDFs are outside the repo, design the app so source material can be ingested from that external folder or seeded into repo-local structured data.
- Include a local app experience, not just scripts or data generation.
- Progress tracking should persist locally.
</architecture>

<selected_context>
No files are selected because `/Users/skinzey/code/gre2tor` contains no files. This is intentional: there is no existing implementation to preserve or inspect.

External source material, not selectable through RepoPrompt:
`/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)`
- `Part 01_Fractions & Decimals.pdf` through `Part 14_Probability.pdf`
- Topics include Algebra, Geometry, Percents, Word Problems, Ratios & Proportions, Rates, Statistics, Integer Properties, Sequences & Functions, Overlapping Sets, Combinatorics, and Probability.
</selected_context>

<relationships>
- Greenfield repo root -> scaffold package/config/source/test files as needed.
- External PDF folder -> ingestion or seed pipeline -> topic-organized card/question data -> local quiz UI.
- Quiz UI -> answer evaluation/review state -> local progress persistence.
- Topic taxonomy should map directly to the PDF parts so users can study by source/topic.
</relationships>

<ambiguities>
- The exact names/order of all 14 PDF files were supplied only in summary form, not enumerated from the filesystem. The builder should inspect the external PDF directory directly if tool access allows.
- It is not specified whether PDF extraction must happen automatically in-app or whether a seed/import script is acceptable. A pragmatic hybrid is reasonable: structured seed data for immediate usability plus an import path/script for future content expansion.
- No stack preference was specified. The builder should identify the empty repo state and choose a minimal local stack that can be installed, run, and maintained easily.
</ambiguities>

## Selection
- Total tokens: 0 (Auto view)


---

## Generated Plan

## Chat Send ✅
- **Chat**: `gre-flashcards-47B093` | **Mode**: plan

### Response


## 1. **Summary**

Build a greenfield local GRE flashcard/quiz app at `/Users/skinzey/code/gre2tor` using a small Flask + SQLite + vanilla HTML/CSS/JS stack. The app will organize topics to match the 14 Math Bible PDFs, support structured seed data, provide a PDF text-ingestion pipeline for future card creation, quiz users on theory and problem-solving cards, and persist local progress in SQLite. This should be a targeted, pragmatic scaffold rather than a broad platform: server-rendered pages, minimal dependencies, simple schemas, and repo-local data files.

## 2. **Current-state analysis**

The repo is empty from the provided context:

- No existing app files, package files, config, tests, or Git metadata.
- No code needs to be preserved.
- The source PDFs live outside the repo at:

```text
/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)
```

Relevant architecture to introduce:

```text
External PDFs
  -> PDF extraction script
  -> repo-local extracted text / draft card JSON
  -> curated seed JSON
  -> SQLite database
  -> Flask local web app
  -> quiz/review UI
  -> progress tracking in SQLite
```

Reusable constraints/patterns:

- Use local persistence only.
- Avoid SaaS/cloud dependencies.
- Do not embed PDFs in the repo by default.
- Treat generated cards as repo-local structured data, separate from raw copyrighted PDFs.
- Keep the UI usable without a frontend framework.

Blocking items:

- Exact PDF filenames should be validated during implementation.
- Automatic high-quality flashcard generation from PDFs is unreliable without an LLM; the app should support ingestion and draft generation, but final cards should be curated through structured JSON.

## 3. **Design**

### Stack decision

Use:

- **Python 3.11+**
- **Flask** for local web UI and routing
- **SQLite** via Python stdlib `sqlite3`
- **pypdf** for PDF text extraction
- **pytest** for tests
- **Vanilla JS/CSS** for lightweight quiz interactions

Why this stack:

- Minimal dependencies.
- Good PDF extraction support.
- SQLite is built in and ideal for local progress tracking.
- Flask server-rendered pages avoid React/Vite complexity.
- Easy for a developer to run locally.

Package manager:

- Use `venv` + `pip`.
- Include `requirements.txt`.
- Do not introduce Poetry unless specifically desired later.

---

## Core app structure

Planned tree:

```text
/Users/skinzey/code/gre2tor
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── app.py
├── gre2tor/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── seed.py
│   ├── quiz.py
│   └── pdf_ingest.py
├── scripts/
│   ├── init_db.py
│   ├── seed_db.py
│   └── ingest_pdfs.py
├── data/
│   ├── seed/
│   │   ├── topics.json
│   │   └── cards.json
│   ├── extracted/
│   │   └── .gitkeep
│   └── drafts/
│       └── .gitkeep
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── topics.html
│   ├── topic_detail.html
│   ├── quiz.html
│   ├── review.html
│   └── card_detail.html
├── static/
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── quiz.js
└── tests/
    ├── test_seed.py
    ├── test_quiz.py
    └── test_db.py
```

---

## Topic taxonomy

Create `data/seed/topics.json` as the canonical topic list.

The topic IDs should be stable slugs mapped to PDF parts.

Shape:

```json
[
  {
    "id": "fractions-decimals",
    "part": 1,
    "title": "Fractions & Decimals",
    "pdf_filename": "Part 01_Fractions & Decimals.pdf",
    "description": "Fractions, decimals, conversions, operations, and comparisons."
  }
]
```

Include all 14 parts.

Known topics from the prompt:

1. Fractions & Decimals
2. Algebra
3. Geometry
4. Percents
5. Word Problems
6. Ratios & Proportions
7. Rates
8. Statistics
9. Integer Properties
10. Sequences & Functions
11. Overlapping Sets
12. Combinatorics
13. Probability

The prompt says `Part 01` through `Part 14` but lists 13 topic names. Implementation must inspect the PDF folder and add the missing part 14 topic exactly as found. If inspection is unavailable, include a placeholder topic with `"needs_validation": true` and document it in README.

---

## Data model

Use SQLite database at:

```text
instance/gre2tor.sqlite3
```

Create this path automatically.

### Tables

#### `topics`

Owns topic metadata.

Fields:

```sql
id TEXT PRIMARY KEY
part INTEGER NOT NULL
title TEXT NOT NULL
pdf_filename TEXT
description TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

#### `cards`

Stores flashcards and quiz questions.

Fields:

```sql
id TEXT PRIMARY KEY
topic_id TEXT NOT NULL REFERENCES topics(id)
type TEXT NOT NULL
prompt TEXT NOT NULL
answer TEXT NOT NULL
explanation TEXT
choices_json TEXT
difficulty INTEGER NOT NULL DEFAULT 2
source_pdf TEXT
source_page INTEGER
tags_json TEXT NOT NULL DEFAULT '[]'
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

`type` allowed values:

```text
theory
problem
multiple_choice
numeric
```

Rules:

- `theory`: prompt + answer, optional explanation.
- `problem`: prompt + answer + explanation.
- `multiple_choice`: requires `choices_json`.
- `numeric`: answer is normalized string; evaluation supports exact match initially.

#### `attempts`

Stores every answer attempt.

Fields:

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
card_id TEXT NOT NULL REFERENCES cards(id)
topic_id TEXT NOT NULL REFERENCES topics(id)
user_answer TEXT
is_correct INTEGER NOT NULL
elapsed_ms INTEGER
created_at TEXT NOT NULL
```

#### `card_progress`

Stores current learning state per card.

Fields:

```sql
card_id TEXT PRIMARY KEY REFERENCES cards(id)
seen_count INTEGER NOT NULL DEFAULT 0
correct_count INTEGER NOT NULL DEFAULT 0
incorrect_count INTEGER NOT NULL DEFAULT 0
streak INTEGER NOT NULL DEFAULT 0
last_seen_at TEXT
next_review_at TEXT
mastery INTEGER NOT NULL DEFAULT 0
updated_at TEXT NOT NULL
```

`mastery` range:

```text
0 = new
1 = learning
2 = familiar
3 = strong
```

Keep this simple; do not implement full spaced repetition yet.

---

## Seed data

Create `data/seed/cards.json`.

Shape:

```json
[
  {
    "id": "fractions-decimals-convert-decimal-to-fraction",
    "topic_id": "fractions-decimals",
    "type": "theory",
    "prompt": "How do you convert a terminating decimal to a fraction?",
    "answer": "Write the decimal over the matching power of 10, then reduce.",
    "explanation": "For example, 0.375 = 375/1000 = 3/8.",
    "difficulty": 1,
    "source_pdf": "Part 01_Fractions & Decimals.pdf",
    "source_page": null,
    "tags": ["conversion", "fractions", "decimals"]
  }
]
```

Initial seed requirement:

- Add at least a small starter set so the app is usable immediately.
- Minimum suggested:
  - 2 theory cards per topic.
  - 2 problem cards per topic.
- Use original summaries/examples, not copied large PDF passages.

Seed behavior:

- `scripts/seed_db.py` should upsert topics/cards.
- Existing progress must not be deleted during reseed.
- Card IDs are stable; changing a card ID creates a new card.

---

## PDF ingestion

### Purpose

The PDF pipeline should make it easy to extract text from the external folder and produce draft source files for card authoring. It does not need to automatically create perfect flashcards.

### Config

Add `.env.example`:

```text
PDF_SOURCE_DIR="/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)"
DATABASE_PATH="instance/gre2tor.sqlite3"
FLASK_DEBUG=1
```

`gre2tor/config.py` should read:

- `PDF_SOURCE_DIR`
- `DATABASE_PATH`
- `FLASK_DEBUG`

Fallback PDF path should be the provided external path.

### `gre2tor/pdf_ingest.py`

Responsibilities:

- List expected PDFs.
- Validate missing/unexpected files.
- Extract text page-by-page using `pypdf`.
- Write JSON files into `data/extracted/`.

Output shape per PDF:

```json
{
  "topic_id": "fractions-decimals",
  "pdf_filename": "Part 01_Fractions & Decimals.pdf",
  "pages": [
    {
      "page": 1,
      "text": "..."
    }
  ]
}
```

### `scripts/ingest_pdfs.py`

CLI behavior:

```bash
python scripts/ingest_pdfs.py
```

Options:

```bash
--source-dir PATH
--out-dir data/extracted
--draft-cards
```

If `--draft-cards` is passed, create simple draft JSON in `data/drafts/`.

Draft card shape:

```json
{
  "topic_id": "algebra",
  "source_pdf": "Part 02_Algebra.pdf",
  "source_page": 4,
  "draft_prompt": "",
  "draft_answer": "",
  "source_excerpt": "short extracted text chunk",
  "status": "needs_authoring"
}
```

Important:

- Do not overwrite curated `data/seed/cards.json`.
- Do not fail the whole import if one PDF has extraction issues; log the error and continue.

---

## Flask routes and UI

### `app.py`

Entrypoint:

- Creates Flask app using `gre2tor.create_app()`.
- Runs local development server.

### `gre2tor/__init__.py`

App factory:

```python
def create_app(config_override=None):
    ...
```

Responsibilities:

- Load config.
- Ensure instance folder exists.
- Register routes.
- Initialize DB if missing.

### Routes

#### `GET /`

Dashboard.

Shows:

- Total cards.
- Cards attempted.
- Accuracy.
- Topic progress list.
- CTA buttons:
  - “Study All”
  - “Choose Topic”
  - “Review Missed”

#### `GET /topics`

List all topics.

Each topic card shows:

- Title
- Part number
- Total cards
- Attempted count
- Accuracy
- “Study” button

#### `GET /topics/<topic_id>`

Topic detail.

Shows:

- Topic metadata
- Progress stats
- Card list summary
- Study buttons:
  - All cards
  - New cards
  - Missed cards

#### `GET /quiz`

Query params:

```text
topic_id optional
mode optional: all | new | missed | review
limit optional integer default 10
```

Creates a quiz session in memory from DB query results. Since this is local/single-user, no server-side session table is needed initially. The page can render the selected card IDs into the HTML as JSON.

#### `POST /api/attempts`

Receives:

```json
{
  "card_id": "fractions-example-id",
  "user_answer": "3/8",
  "elapsed_ms": 12000
}
```

Returns:

```json
{
  "is_correct": true,
  "correct_answer": "3/8",
  "explanation": "...",
  "progress": {
    "mastery": 1,
    "streak": 1
  }
}
```

#### `GET /review`

Shows missed/low-mastery cards.

#### `GET /cards/<card_id>`

Shows full card details, answer, explanation, and progress history.

---

## Answer evaluation

Create `gre2tor/quiz.py`.

Core functions:

```python
normalize_answer(value: str) -> str
evaluate_answer(card: CardLike, user_answer: str) -> bool
select_cards(topic_id=None, mode="all", limit=10) -> list
update_progress(card_id, is_correct) -> None
```

Evaluation rules:

- `multiple_choice`: compare normalized selected choice to answer.
- `numeric`: compare normalized strings.
- `theory` and `problem`: initially self-graded unless exact match is practical.

For theory/problem cards, the UI should show:

- “Reveal Answer”
- “I got it right”
- “I missed it”

The API should accept `is_correct` from self-grade for those card types.

For objective cards, the UI can submit `user_answer` and receive automatic correctness.

This avoids pretending free-text math reasoning can be reliably auto-graded.

---

## Progress tracking flow

### User studies a card

```text
Quiz page loads selected cards
  -> User answers or reveals answer
  -> Browser posts attempt
  -> Flask route validates card exists
  -> quiz evaluator determines correctness or accepts self-grade
  -> attempts row inserted
  -> card_progress upserted
  -> JSON response updates UI
```

### Progress update rules

On correct:

```text
seen_count += 1
correct_count += 1
streak += 1
mastery = min(3, mastery + 1 when streak threshold reached)
next_review_at = now + interval based on mastery
```

On incorrect:

```text
seen_count += 1
incorrect_count += 1
streak = 0
mastery = max(0, mastery - 1)
next_review_at = now
```

Suggested intervals:

```text
mastery 0: now
mastery 1: +1 day
mastery 2: +3 days
mastery 3: +7 days
```

Keep this deterministic and easy to test.

---

## Error handling and edge cases

### Missing DB

- App should auto-create schema on startup.
- README should still recommend running:

```bash
python scripts/init_db.py
python scripts/seed_db.py
```

### Missing PDFs

- App still works from seed data.
- `ingest_pdfs.py` reports missing PDFs and exits non-zero only if no PDFs were found.

### Empty seed data

- Dashboard displays an empty-state message:
  - “No cards yet. Run `python scripts/seed_db.py`.”

### No quiz cards match filter

- Quiz page displays:
  - “No cards found for this mode/topic.”
  - Link back to topics.

### Duplicate attempts

- Attempts are append-only.
- Progress updates every submitted attempt.
- UI should disable the submit button after one submission per card to reduce accidental duplicates.

### Out-of-order submissions

- Since this is local/single-user, accept them.
- Each attempt records its own timestamp.

---

## 4. **File-by-file impact**

### `README.md`

Add:

- Project purpose.
- Setup instructions.
- Run commands.
- PDF ingestion command.
- Seed workflow.
- Local data locations.
- Known limitation: PDF ingestion extracts text but curated cards should be reviewed.

Depends on all design decisions.

---

### `requirements.txt`

Add:

```text
Flask
pypdf
pytest
```

Optional but useful:

```text
python-dotenv
```

If avoiding extra dependency, implement env loading manually and skip `python-dotenv`.

---

### `.gitignore`

Include:

```text
venv/
__pycache__/
.pytest_cache/
instance/
.env
data/extracted/*.json
data/drafts/*.json
```

Keep `data/extracted/.gitkeep` and `data/drafts/.gitkeep`.

---

### `.env.example`

Add default local configuration.

---

### `app.py`

Add Flask entrypoint.

Depends on `gre2tor.create_app`.

---

### `gre2tor/__init__.py`

Add app factory, route registration, DB initialization hook.

Depends on `config.py`, `db.py`, `quiz.py`.

---

### `gre2tor/config.py`

Add environment/config loading.

Owns:

- PDF source dir
- DB path
- debug flag

---

### `gre2tor/db.py`

Add:

- SQLite connection helper.
- Schema creation.
- Query helpers for topics/cards/progress/attempts.

Should not own quiz-selection logic.

---

### `gre2tor/models.py`

Add lightweight dataclasses or typed dict helpers for:

- Topic
- Card
- Attempt
- CardProgress

Keep them simple; do not add ORM.

---

### `gre2tor/seed.py`

Add JSON loading and upsert logic.

Responsibilities:

- Validate topic/card fields.
- Insert/update topics/cards.
- Preserve attempts/progress.

---

### `gre2tor/quiz.py`

Add answer normalization, evaluation, card selection, progress update logic.

Depends on `db.py`.

---

### `gre2tor/pdf_ingest.py`

Add PDF listing/extraction/draft generation helpers.

Depends on `pypdf`, `topics.json`.

---

### `scripts/init_db.py`

Creates schema.

---

### `scripts/seed_db.py`

Loads `data/seed/topics.json` and `data/seed/cards.json`.

---

### `scripts/ingest_pdfs.py`

Extracts external PDFs into `data/extracted/`.

Optional draft mode creates `data/drafts/*.json`.

---

### `data/seed/topics.json`

Canonical topic taxonomy.

Must map to PDF parts.

---

### `data/seed/cards.json`

Starter flashcards/problems.

Use original concise educational content.

---

### Templates

#### `templates/base.html`

Shared layout/nav.

#### `templates/index.html`

Dashboard.

#### `templates/topics.html`

Topic list.

#### `templates/topic_detail.html`

Topic detail/progress.

#### `templates/quiz.html`

Quiz experience.

#### `templates/review.html`

Missed/low-mastery cards.

#### `templates/card_detail.html`

Card details/progress.

---

### Static files

#### `static/css/app.css`

Simple responsive layout.

#### `static/js/quiz.js`

Client quiz flow:

- reveal answer
- submit answer
- self-grade
- move to next card
- update visible progress

---

### Tests

#### `tests/test_seed.py`

Validate:

- topics load
- cards load
- reseed is idempotent
- progress is preserved

#### `tests/test_quiz.py`

Validate:

- answer normalization
- multiple-choice evaluation
- progress update rules

#### `tests/test_db.py`

Validate:

- schema creation
- insert/query helpers
- attempt persistence

---

## 5. **Risks and migration**

No existing data migration is needed because the repo is empty.

Main risks:

- **PDF filename mismatch:** implementation must inspect the external folder and update `topics.json`.
- **PDF extraction quality:** math PDFs may extract symbols poorly. Treat extraction as source assistance, not final card quality.
- **Copyright/source handling:** avoid committing raw PDFs or large copied passages. Store concise original flashcards and optional short source excerpts only.
- **Missing 14th topic name:** validate directly from filesystem during implementation.

Rollback concern:

- If schema changes later, add explicit migrations. For v1, simple schema creation is enough.

## 6. **Implementation order**

1. Scaffold project files: `README.md`, `.gitignore`, `requirements.txt`, `.env.example`, package directories.
2. Implement config and SQLite schema in `gre2tor/config.py` and `gre2tor/db.py`.
3. Add seed topic/card JSON files.
4. Implement `gre2tor/seed.py`, `scripts/init_db.py`, and `scripts/seed_db.py`.
5. Implement Flask app factory and core routes.
6. Add templates and CSS for dashboard, topics, quiz, review.
7. Implement quiz logic and progress tracking.
8. Add `static/js/quiz.js` for answer/reveal/self-grade flow.
9. Implement PDF ingestion script and extracted/draft output format.
10. Add tests for DB, seed idempotency, quiz evaluation, and progress updates.
11. Validate locally with:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_db.py
python app.py
pytest
```

12. Inspect the external PDF folder, correct the full 14-topic mapping, and run:

```bash
python scripts/ingest_pdfs.py
```

No files were changed and no tests were run because this response is an implementation plan only.

---

## Orchestrator progress

- [x] Item 1: Core Flask/SQLite scaffold, config/schema helpers, seed scripts, and starter seed data. Verified corrected taxonomy against actual 14 PDF filenames; seed validates with 14 topics and 56 cards.
- [x] Item 2: Web quiz UI, routes, answer/reveal/self-grade flow, attempts API, and progress/review behavior. Smoke-tested dashboard/topics/quiz/review/card routes and attempts API.
- [x] Item 3: PDF ingestion pipeline, tests, docs polish, and final validation. Added ingestion CLI/module, automated tests, README updates, validated all 14 source PDFs, and confirmed `11 passed`.


> 💡 Continue this plan conversation with ask_oracle(chat_id: "gre-flashcards-47B093", new_chat: false)