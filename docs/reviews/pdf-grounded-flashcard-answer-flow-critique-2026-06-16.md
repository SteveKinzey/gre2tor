# Critique: PDF-Grounded Flashcard Answer Flow Plan

Scope: critique only of `docs/plans/pdf-grounded-flashcard-answer-flow-2026-06-16.md`. No scope added.

## 1. Top 3 under-specified seams

1. **Concept dedup vs. `LIMIT` in `select_cards`** (`gre2tor/quiz.py:78-92`). Selection is one SQL query ending `ORDER BY ... LIMIT ?`. Work item 4 ("at most one card per concept per session," with a 5-key preference order) doesn't say *where* dedup happens: a SQL window function (`ROW_NUMBER() OVER (PARTITION BY concept_id ...)`) or a Python post-filter. If dedup runs in Python *after* `LIMIT`, the quiz silently under-fills (fewer than `limit` cards). This is the single largest unspecified decision and it drives the whole item-4 design.

2. **`concept_id` storage vs. defaulting** (`gre2tor/db.py` + `gre2tor/quiz.py`). Item 1 says default `concept_id = card.id` "at decode." Item 4 says "group by `concept_id` during selection," which happens in SQL. If `concept_id` is left `NULL` in the table and only defaulted in Python, SQL grouping collapses *all* legacy cards into one `NULL` bucket → at most one legacy card per quiz. The plan never states that legacy `concept_id` must be backfilled at write/migration time. (See Contradictions.)

3. **Alias threading into `evaluate_answer`** (`gre2tor/quiz.py:28-31`). `evaluate_answer(card, ...)` compares `card.get("answer")`. Item 3 wants comparison against `answer + answer_aliases`, but the plan doesn't name `get_card` as the place that must decode `answer_aliases_json` onto the card dict. Without that, aliases are invisible at eval time.

## 2. Contradictions / missing dependencies

- **Decode-time default vs. SQL grouping** (seam 2 above) is a genuine contradiction: "default at decode" and "group by `concept_id` in selection" cannot both hold unless `concept_id` is persisted/backfilled. Resolve by backfilling on migration/upsert, not at decode.
- **`problem` already auto-grades, and seed cards exist.** `OBJECTIVE_CARD_TYPES = {"multiple_choice","numeric"}` (`quiz.py:9`); `problem` cards are present in `data/seed/cards.json` (28 type entries). Moving `problem` to auto-eval (item 3) is a *behavior change* for existing cards, not a no-op. It depends on aliases being authored first (item 1/2) or some current problem answers will start failing exact match. Item 3 should be sequenced after, or explicitly note the regression window.
- **Missing dep, item 4 → item 1:** variant/grounded selection needs `grounding_status` and `concept_id` populated for legacy rows; fine as written, but only if the backfill above exists.

## 3. Over-planning — cut or simplify

- **Item 6 (PDF authoring workflow / draft enrichment)** is orthogonal to the stated user-facing goal (question-first answer flow). It's the largest non-UI surface and produces only ignored draft files. Cut to a separate follow-up plan; the answer flow ships without it.
- **Item 2's `--require-grounding` strict gate** builds enforcement for a state that doesn't exist yet (every current card is `legacy`; no `grounded` cards). Defer until the first grounded card is authored. Keep only the additive validation.
- **Item 4's full 5-key preference tuple** restates the existing `ORDER BY mastery, seen_count, part, difficulty, id` (`quiz.py:88`). Don't re-specify it — just prepend `grounded DESC`. The rest is already there.

## 4. Questions that change implementation order

1. **Is `concept_id` persisted/backfilled in the DB, or defaulted only in Python?** Answer decides whether item 4 is SQL or Python, and whether item 1 must include a backfill UPDATE. This reorders items 1 and 4.
2. **Do current `problem` seed cards have clean exact-match answers, or do they rely on self-grade today?** If they need aliases, item 2/alias authoring must precede item 3; if answers are already exact, item 3 is safe to do first.
3. **Are reviewed variants actually required for v1, or does "repeat the missed card" suffice?** If variants defer, item 4's concept logic and most of item 6 drop, collapsing the plan to UI (item 5) + evaluation (item 3) + minimal schema (item 1).
