# PDF-Grounded Flashcard Answer Flow: Plan

## Goal
Upgrade the quiz experience so each flashcard shows the question first, presents five multiple-choice answers labeled A–E, and after submission shows a top `Correct`/`Incorrect` result in green/red followed by the explanation. Choices should be written like an expert GRE math professor: one correct answer, several tempting counterfeit answers based on common GRE mistakes, and at least one concept-relevant answer that is clearly not close. Missed concepts should come back for review, preferably through curated variants of the same concept, and future question-bank growth must stay grounded in the source PDFs rather than invented content.

## Background
- The app is a small Flask + SQLite project with Jinja templates, vanilla JS, JSON seed data, PDF extraction, and pytest coverage.
- `/quiz` selects cards and renders `templates/quiz.html`; `/api/attempts` records answers and returns correctness, answer, explanation, and progress through `gre2tor/quiz.py:163-190`.
- The quiz template already renders prompt, answer controls, hidden answer/explanation panel, self-grade controls, result region, and next button in `templates/quiz.html:26-73`.
- `static/js/quiz.js:32-71` already posts attempts, reveals the answer panel, locks controls, and shows next navigation.
- Missed/review behavior already exists through `attempts`, `card_progress.incorrect_count`, `mastery`, and `next_review_at` in `gre2tor/db.py:41-62`, with `all`, `new`, `missed`, and `review` selection modes in `gre2tor/quiz.py:41-98`.
- PDF extraction can produce page-level source text and draft placeholders with `source_pdf`, `source_page`, and `source_excerpt` in `gre2tor/pdf_ingest.py:112-204`.
- Persisted cards support `source_pdf` and `source_page`, but not `source_excerpt`, grounding status, concept grouping, variants, or answer aliases (`gre2tor/db.py:26-39`). Current visible seed cards have `source_page: null` (`data/seed/cards.json:1-45`).
- Generated extracted/draft data is intentionally ignored; curated cards belong in `data/seed/cards.json` and must be reviewed before promotion (`README.md:36-87`).

## Approach
Keep the current route and attempt pipeline. Make a focused UI pass for the answer flow, then add the minimum persistent metadata needed for source-grounded cards and reviewed variants.

1. **UI answer flow**: Reorder each quiz card so the result banner is at the top, the question/front is visually distinct, and the answer workspace sits below the prompt. After submission, show only `Correct` or `Incorrect` in the banner, then reveal the answer and an explanation headed “How this answer was found.”
2. **Evaluation policy**: Make A–E multiple choice the default study format. `multiple_choice` cards auto-grade by selected option; legacy `numeric`/`problem` cards can still auto-grade during migration, but new authored question variants should prefer A–E choices. Keep `theory` as reveal + self-grade only when a concept is not naturally testable as a GRE-style choice question.
3. **PDF grounding**: Add card metadata for `source_excerpt`, `grounding_status`, `concept_id`, `variant_of`, `variant_kind`, `answer_choice`, and choice-quality notes if useful. Persist and backfill `concept_id = id` for legacy rows so SQL selection can safely group by concept.
4. **Missed concept loop**: Store alternate phrasings/problems as normal reviewed cards sharing the same `concept_id`. For v1, repeat the missed card when no reviewed variant exists; variant-aware selection can follow once concepts are persisted.
5. **No hallucinated generation**: Do not generate live questions from an LLM in the app. New questions should come from reviewed seed cards or source-backed drafts promoted by a human.

## Work Items

### 1. Schema and model foundation
Files: `gre2tor/db.py`, `gre2tor/models.py`, `tests/test_db.py`

- Add additive card fields:
  - `answer_aliases_json TEXT DEFAULT '[]'`
  - `source_excerpt TEXT`
  - `grounding_status TEXT DEFAULT 'legacy'`
  - `concept_id TEXT`
  - `variant_of TEXT`
  - `variant_kind TEXT DEFAULT 'base'`
- Add a small non-destructive migration helper for existing SQLite DBs after `SCHEMA_SQL` runs.
- Persist/backfill defaults during migration and upsert, not only during Python decode:
  - `answer_aliases = []`
  - `grounding_status = 'legacy'`
  - `concept_id = card.id`
  - `variant_kind = 'base'`
- Keep decode fallbacks as defensive compatibility only.
- Extend the `Card` dataclass to match the new fields.
- Test upsert/decode/default behavior.

### 2. Seed validation and multiple-choice quality
Files: `gre2tor/seed.py`, `tests/test_seed.py`

- Validate optional `grounding_status`, `variant_kind`, `concept_id`, and `variant_of`.
- Require `source_pdf`, positive `source_page`, and non-empty `source_excerpt` only when a card is marked `grounding_status == 'grounded'`.
- Default missing `concept_id` to the card ID before upsert so selection sees real stored values.
- Validate that `variant_of`, when present, references another seed card and does not equal the current card ID.
- For `multiple_choice` cards, require exactly five choices labeled/displayed as A–E by the UI, with the stored correct answer matching one choice exactly.
- Add a seed-level distribution check/report so correct answers do not cluster in one position, especially not mostly C. This can warn at first rather than fail existing data.
- Authoring rule: choices should include the correct answer, 2–3 tempting counterfeit answers based on likely GRE math errors, and at least one concept-relevant outlier that is clearly not close.

### 3. Quiz evaluation and answer positions
Files: `gre2tor/db.py`, `gre2tor/quiz.py`, `tests/test_quiz.py`

- Keep `multiple_choice` auto-grading as the primary path: compare the selected choice value to the stored correct `answer`.
- Keep legacy `numeric`/`problem` exact-match behavior available so existing cards do not break during migration.
- Keep `theory` self-graded for true recall/explanation cards only.
- Add support for tracking or deriving the correct choice letter A–E so explanations and tests can verify the correct position.
- Keep `/api/attempts` response shape backward-compatible.
- Add tests for A–E choice evaluation, non-C-biased answer distribution helpers/reporting, legacy exact-match cards, and self-graded theory cards.

### 4. Variant-aware missed/review selection
Files: `gre2tor/quiz.py`, possibly `gre2tor/db.py`, `tests/test_quiz.py`

- Group cards by persisted `concept_id`, never by decode-only defaults.
- Implement dedup before `LIMIT`, either with a SQLite window function (`ROW_NUMBER() OVER (PARTITION BY concept_id ...)`) or by fetching enough rows and filtering before applying the final limit. Do not filter after the existing SQL `LIMIT`, or quizzes can under-fill.
- For `missed` and `review`, make a concept eligible if any variant has misses, low mastery, or is due.
- Preserve the current ordering as much as possible; only add a grounded-card preference when variants exist.
- Do not add concept-level progress yet; keep progress per card to avoid a larger refactor.

### 5. Quiz UI polish
Files: `templates/quiz.html`, `static/js/quiz.js`, `static/css/app.css`

- Move `.result` to the top of each `.quiz-card` and hide it initially.
- Add wrappers such as `.question-face` and `.answer-workspace` for clearer layout.
- Render multiple-choice cards as five options labeled A–E. Do not rely on the correct answer being in a predictable position.
- During migration, keep text-answer rendering for legacy `numeric`/`problem` cards; new GRE-style cards should be authored as A–E multiple choice whenever practical.
- Update `showResult()` so successful attempts show exactly `Correct` or `Incorrect`, apply `.good`/`.bad`, reveal the answer panel, lock controls, and show next navigation.
- The answer panel should identify the correct choice and then explain how the answer was found.
- Keep empty-answer and API errors as validation messages that do not reveal the answer panel or mark the card submitted.
- Add a top banner style using the existing green/red visual language.

### 6. PDF-backed authoring workflow follow-up
Files: `gre2tor/pdf_ingest.py`, `tests/test_pdf_ingest.py`, `README.md`

- Keep this as a follow-up after the answer flow and metadata are in place.
- Extend draft card output so drafts include promotable seed-like fields, especially five A–E choices, the correct answer, `source_excerpt`, `grounding_status`, `concept_id`, and variant fields.
- Keep generated draft files ignored. They are authoring aids only.
- Document the workflow: ingest PDFs, create drafts, author/review from `source_excerpt`, then promote reviewed cards to `data/seed/cards.json`.
- Defer a `--require-grounding` CLI gate until the seed file contains real grounded cards.

### 7. Verification
Run after implementation:

```bash
pytest
python scripts/init_db.py
python scripts/seed_db.py
```

Manual browser checks:
- correct auto-graded answer
- incorrect auto-graded answer
- empty submission
- A–E multiple-choice submission
- theory reveal/self-grade
- final-card completion
- missed/review mode showing a missed concept again or a curated variant

## Open Questions
- Should all future problem-style cards be converted to A–E multiple choice, leaving text-entry only for legacy cards and rare theory/self-grade cases?
- Should grounded cards eventually require committed `source_excerpt`, or should excerpts stay only in ignored draft/extraction files with a validation report? This plan supports committed concise excerpts, but strict enforcement is deferred until reviewed grounded cards exist.

## Risks and Follow-up
- Existing cards are legacy and not fully PDF-grounded. Do not add or enable strict grounding until source pages/excerpts are reviewed.
- Multiple choice avoids most symbolic-equivalence grading problems, but bad distractors can teach the wrong lesson. Distractors need expert review and source grounding.
- Variant progress remains per card. That is acceptable for this phase; concept-level mastery would be a separate refactor.
- Avoid runtime question generation unless a future plan introduces a retrieval-and-citation pipeline with hard source constraints.

## References
- `templates/quiz.html:26-73`
- `static/js/quiz.js:32-71`
- `gre2tor/quiz.py:41-98`, `gre2tor/quiz.py:163-190`
- `gre2tor/db.py:26-62`
- `gre2tor/pdf_ingest.py:112-204`
- `data/seed/cards.json:1-45`
- `README.md:36-87`
