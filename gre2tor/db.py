from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Iterator

VALID_CARD_TYPES = {"theory", "problem", "multiple_choice", "numeric"}

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    part INTEGER NOT NULL,
    title TEXT NOT NULL,
    pdf_filename TEXT,
    description TEXT,
    needs_validation INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('theory', 'problem', 'multiple_choice', 'numeric')),
    prompt TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT,
    choices_json TEXT,
    difficulty INTEGER NOT NULL DEFAULT 2 CHECK (difficulty BETWEEN 1 AND 5),
    source_pdf TEXT,
    source_page INTEGER,
    source_excerpt TEXT,
    grounding_status TEXT NOT NULL DEFAULT 'legacy',
    concept_id TEXT,
    variant_of TEXT,
    variant_kind TEXT NOT NULL DEFAULT 'base',
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    user_answer TEXT,
    is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    elapsed_ms INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS card_progress (
    card_id TEXT PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
    seen_count INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    incorrect_count INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT,
    next_review_at TEXT,
    mastery INTEGER NOT NULL DEFAULT 0 CHECK (mastery BETWEEN 0 AND 3),
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cards_topic_id ON cards(topic_id);
CREATE INDEX IF NOT EXISTS idx_attempts_card_id ON attempts(card_id);
CREATE INDEX IF NOT EXISTS idx_attempts_topic_id ON attempts(topic_id);
CREATE INDEX IF NOT EXISTS idx_attempts_created_at ON attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_card_progress_next_review ON card_progress(next_review_at);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    conn = connect(database_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrate_cards_table(conn: sqlite3.Connection) -> None:
    columns = _column_names(conn, "cards")
    migrations = {
        "source_excerpt": "ALTER TABLE cards ADD COLUMN source_excerpt TEXT",
        "grounding_status": "ALTER TABLE cards ADD COLUMN grounding_status TEXT NOT NULL DEFAULT 'legacy'",
        "concept_id": "ALTER TABLE cards ADD COLUMN concept_id TEXT",
        "variant_of": "ALTER TABLE cards ADD COLUMN variant_of TEXT",
        "variant_kind": "ALTER TABLE cards ADD COLUMN variant_kind TEXT NOT NULL DEFAULT 'base'",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)

    conn.execute("UPDATE cards SET grounding_status = 'legacy' WHERE grounding_status IS NULL OR grounding_status = ''")
    conn.execute("UPDATE cards SET concept_id = id WHERE concept_id IS NULL OR concept_id = ''")
    conn.execute("UPDATE cards SET variant_kind = 'base' WHERE variant_kind IS NULL OR variant_kind = ''")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cards_concept_id ON cards(concept_id)")


def init_db(database_path: str | Path) -> None:
    with connection(database_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _migrate_cards_table(conn)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def _decode_card_row(row: sqlite3.Row | dict | None) -> dict | None:
    if row is None:
        return None
    card = dict(row)
    card["choices"] = json.loads(card.pop("choices_json", None) or "null")
    card["tags"] = json.loads(card.pop("tags_json", None) or "[]")
    card["grounding_status"] = card.get("grounding_status") or "legacy"
    card["concept_id"] = card.get("concept_id") or card.get("id")
    card["variant_kind"] = card.get("variant_kind") or "base"
    return card


def _accuracy(correct_count: int, attempt_count: int) -> float | None:
    if attempt_count <= 0:
        return None
    return round((correct_count / attempt_count) * 100, 1)


def upsert_topic(conn: sqlite3.Connection, topic: dict) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO topics (id, part, title, pdf_filename, description, needs_validation, created_at, updated_at)
        VALUES (:id, :part, :title, :pdf_filename, :description, :needs_validation, :created_at, :updated_at)
        ON CONFLICT(id) DO UPDATE SET
            part = excluded.part,
            title = excluded.title,
            pdf_filename = excluded.pdf_filename,
            description = excluded.description,
            needs_validation = excluded.needs_validation,
            updated_at = excluded.updated_at
        """,
        {
            "id": topic["id"],
            "part": topic["part"],
            "title": topic["title"],
            "pdf_filename": topic.get("pdf_filename"),
            "description": topic.get("description"),
            "needs_validation": 1 if topic.get("needs_validation") else 0,
            "created_at": now,
            "updated_at": now,
        },
    )


def upsert_card(conn: sqlite3.Connection, card: dict) -> None:
    now = utc_now()
    card_type = card["type"]
    if card_type not in VALID_CARD_TYPES:
        raise ValueError(f"Invalid card type for {card['id']}: {card_type}")

    choices = card.get("choices")
    tags = card.get("tags", [])
    conn.execute(
        """
        INSERT INTO cards (
            id, topic_id, type, prompt, answer, explanation, choices_json, difficulty,
            source_pdf, source_page, source_excerpt, grounding_status, concept_id, variant_of,
            variant_kind, tags_json, created_at, updated_at
        )
        VALUES (
            :id, :topic_id, :type, :prompt, :answer, :explanation, :choices_json, :difficulty,
            :source_pdf, :source_page, :source_excerpt, :grounding_status, :concept_id, :variant_of,
            :variant_kind, :tags_json, :created_at, :updated_at
        )
        ON CONFLICT(id) DO UPDATE SET
            topic_id = excluded.topic_id,
            type = excluded.type,
            prompt = excluded.prompt,
            answer = excluded.answer,
            explanation = excluded.explanation,
            choices_json = excluded.choices_json,
            difficulty = excluded.difficulty,
            source_pdf = excluded.source_pdf,
            source_page = excluded.source_page,
            source_excerpt = excluded.source_excerpt,
            grounding_status = excluded.grounding_status,
            concept_id = excluded.concept_id,
            variant_of = excluded.variant_of,
            variant_kind = excluded.variant_kind,
            tags_json = excluded.tags_json,
            updated_at = excluded.updated_at
        """,
        {
            "id": card["id"],
            "topic_id": card["topic_id"],
            "type": card_type,
            "prompt": card["prompt"],
            "answer": card["answer"],
            "explanation": card.get("explanation"),
            "choices_json": json.dumps(choices) if choices is not None else None,
            "difficulty": int(card.get("difficulty", 2)),
            "source_pdf": card.get("source_pdf"),
            "source_page": card.get("source_page"),
            "source_excerpt": card.get("source_excerpt"),
            "grounding_status": card.get("grounding_status") or "legacy",
            "concept_id": card.get("concept_id") or card["id"],
            "variant_of": card.get("variant_of"),
            "variant_kind": card.get("variant_kind") or "base",
            "tags_json": json.dumps(tags),
            "created_at": now,
            "updated_at": now,
        },
    )


def get_topic(conn: sqlite3.Connection, topic_id: str) -> dict | None:
    return row_to_dict(conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone())


def list_topics(conn: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM topics ORDER BY part, title").fetchall()]


def get_card(conn: sqlite3.Connection, card_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return _decode_card_row(row)


def list_cards(conn: sqlite3.Connection, topic_id: str | None = None) -> list[dict]:
    if topic_id:
        rows = conn.execute("SELECT * FROM cards WHERE topic_id = ? ORDER BY id", (topic_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM cards ORDER BY topic_id, id").fetchall()
    return [_decode_card_row(row) for row in rows if row is not None]


def get_card_progress(conn: sqlite3.Connection, card_id: str) -> dict | None:
    return row_to_dict(conn.execute("SELECT * FROM card_progress WHERE card_id = ?", (card_id,)).fetchone())


def list_cards_with_progress(conn: sqlite3.Connection, topic_id: str | None = None) -> list[dict]:
    params: tuple = ()
    where = ""
    if topic_id:
        where = "WHERE c.topic_id = ?"
        params = (topic_id,)

    rows = conn.execute(
        f"""
        SELECT
            c.*,
            t.title AS topic_title,
            t.part AS topic_part,
            COALESCE(p.seen_count, 0) AS seen_count,
            COALESCE(p.correct_count, 0) AS correct_count,
            COALESCE(p.incorrect_count, 0) AS incorrect_count,
            COALESCE(p.streak, 0) AS streak,
            p.last_seen_at,
            p.next_review_at,
            COALESCE(p.mastery, 0) AS mastery
        FROM cards c
        JOIN topics t ON t.id = c.topic_id
        LEFT JOIN card_progress p ON p.card_id = c.id
        {where}
        ORDER BY t.part, c.difficulty, c.id
        """,
        params,
    ).fetchall()
    return [_decode_card_row(row) for row in rows if row is not None]


def record_attempt(
    conn: sqlite3.Connection,
    *,
    card_id: str,
    topic_id: str,
    user_answer: str | None,
    is_correct: bool,
    elapsed_ms: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO attempts (card_id, topic_id, user_answer, is_correct, elapsed_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (card_id, topic_id, user_answer, 1 if is_correct else 0, elapsed_ms, utc_now()),
    )
    return int(cursor.lastrowid)


def list_attempts(conn: sqlite3.Connection, card_id: str | None = None, limit: int = 25) -> list[dict]:
    limit = max(1, min(int(limit), 100))
    if card_id:
        rows = conn.execute(
            """
            SELECT a.*, c.prompt, c.answer, t.title AS topic_title
            FROM attempts a
            JOIN cards c ON c.id = a.card_id
            JOIN topics t ON t.id = a.topic_id
            WHERE a.card_id = ?
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT ?
            """,
            (card_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT a.*, c.prompt, c.answer, t.title AS topic_title
            FROM attempts a
            JOIN cards c ON c.id = a.card_id
            JOIN topics t ON t.id = a.topic_id
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_overall_progress(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM topics) AS topic_count,
            (SELECT COUNT(*) FROM cards) AS card_count,
            (SELECT COUNT(*) FROM attempts) AS attempt_count,
            (SELECT COUNT(*) FROM card_progress WHERE seen_count > 0) AS attempted_cards,
            COALESCE((SELECT SUM(correct_count) FROM card_progress), 0) AS correct_count,
            COALESCE((SELECT SUM(incorrect_count) FROM card_progress), 0) AS incorrect_count,
            (SELECT COUNT(*) FROM card_progress WHERE mastery >= 3) AS mastered_cards
        """
    ).fetchone()
    stats = dict(row)
    stats["accuracy"] = _accuracy(int(stats["correct_count"]), int(stats["attempt_count"]))
    return stats


def _decorate_topic_stats(topic: dict) -> dict:
    topic["accuracy"] = _accuracy(int(topic["correct_count"]), int(topic["attempt_count"]))
    total_cards = int(topic["total_cards"])
    topic["attempted_percent"] = round((int(topic["attempted_cards"]) / total_cards) * 100, 1) if total_cards else 0
    topic["mastery_percent"] = round((int(topic["mastered_cards"]) / total_cards) * 100, 1) if total_cards else 0
    return topic


def list_topic_stats(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            t.*,
            COUNT(c.id) AS total_cards,
            COALESCE(SUM(CASE WHEN p.seen_count > 0 THEN 1 ELSE 0 END), 0) AS attempted_cards,
            COALESCE(SUM(CASE WHEN p.mastery >= 3 THEN 1 ELSE 0 END), 0) AS mastered_cards,
            COALESCE(SUM(p.seen_count), 0) AS attempt_count,
            COALESCE(SUM(p.correct_count), 0) AS correct_count,
            COALESCE(SUM(p.incorrect_count), 0) AS incorrect_count
        FROM topics t
        LEFT JOIN cards c ON c.topic_id = t.id
        LEFT JOIN card_progress p ON p.card_id = c.id
        GROUP BY t.id
        ORDER BY t.part, t.title
        """
    ).fetchall()
    return [_decorate_topic_stats(dict(row)) for row in rows]


def get_topic_stats(conn: sqlite3.Connection, topic_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT
            t.*,
            COUNT(c.id) AS total_cards,
            COALESCE(SUM(CASE WHEN p.seen_count > 0 THEN 1 ELSE 0 END), 0) AS attempted_cards,
            COALESCE(SUM(CASE WHEN p.mastery >= 3 THEN 1 ELSE 0 END), 0) AS mastered_cards,
            COALESCE(SUM(p.seen_count), 0) AS attempt_count,
            COALESCE(SUM(p.correct_count), 0) AS correct_count,
            COALESCE(SUM(p.incorrect_count), 0) AS incorrect_count
        FROM topics t
        LEFT JOIN cards c ON c.topic_id = t.id
        LEFT JOIN card_progress p ON p.card_id = c.id
        WHERE t.id = ?
        GROUP BY t.id
        """,
        (topic_id,),
    ).fetchone()
    return _decorate_topic_stats(dict(row)) if row else None


def list_review_cards(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    limit = max(1, min(int(limit), 100))
    rows = conn.execute(
        """
        SELECT
            c.*,
            t.title AS topic_title,
            t.part AS topic_part,
            p.seen_count,
            p.correct_count,
            p.incorrect_count,
            p.streak,
            p.last_seen_at,
            p.next_review_at,
            p.mastery
        FROM cards c
        JOIN topics t ON t.id = c.topic_id
        JOIN card_progress p ON p.card_id = c.id
        WHERE p.seen_count > 0 AND (p.mastery < 3 OR p.next_review_at <= ?)
        ORDER BY p.incorrect_count DESC, p.mastery ASC, p.last_seen_at ASC
        LIMIT ?
        """,
        (utc_now(), limit),
    ).fetchall()
    return [_decode_card_row(row) for row in rows if row is not None]


def get_summary_stats(database_path: str | Path) -> dict:
    init_db(database_path)
    with connection(database_path) as conn:
        progress = get_overall_progress(conn)
    return {
        "topic_count": progress["topic_count"],
        "card_count": progress["card_count"],
        "attempt_count": progress["attempt_count"],
    }
