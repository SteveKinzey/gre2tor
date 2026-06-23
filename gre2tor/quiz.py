from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
import sqlite3

from .db import get_card, get_card_progress, record_attempt, utc_now

OBJECTIVE_CARD_TYPES = {"multiple_choice", "numeric"}
REVIEW_INTERVALS = {
    0: timedelta(0),
    1: timedelta(days=1),
    2: timedelta(days=3),
    3: timedelta(days=7),
}


def normalize_answer(value: str | None) -> str:
    if value is None:
        return ""
    normalized = value.strip().lower()
    normalized = normalized.replace("−", "-").replace("×", "x")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.strip(". ")
    return normalized


def evaluate_answer(card: dict, user_answer: str | None, self_grade: bool | None = None) -> bool:
    if card["type"] not in OBJECTIVE_CARD_TYPES and self_grade is not None:
        return bool(self_grade)
    return normalize_answer(user_answer) == normalize_answer(card.get("answer"))


def _clamp_limit(limit: int | str | None, default: int = 10) -> int:
    try:
        parsed = int(limit) if limit is not None else default
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, 50))


def select_cards(
    conn: sqlite3.Connection,
    *,
    topic_id: str | None = None,
    mode: str = "all",
    limit: int | str | None = 10,
    user_email: str = "",
) -> list[dict]:
    mode = mode if mode in {"all", "new", "missed", "review"} else "all"
    limit_value = _clamp_limit(limit)
    clauses = []
    params: list[object] = [user_email]

    if topic_id:
        clauses.append("c.topic_id = ?")
        params.append(topic_id)

    if mode == "new":
        clauses.append("COALESCE(p.seen_count, 0) = 0")
    elif mode == "missed":
        clauses.append("COALESCE(p.incorrect_count, 0) > 0")
    elif mode == "review":
        clauses.append("COALESCE(p.seen_count, 0) > 0")
        clauses.append("(COALESCE(p.mastery, 0) < 3 OR p.next_review_at <= ?)")
        params.append(utc_now())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit_value)

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
        LEFT JOIN card_progress p ON p.card_id = c.id AND p.user_email = ?
        {where}
        ORDER BY COALESCE(p.mastery, 0), COALESCE(p.seen_count, 0), t.part, c.difficulty, c.id
        LIMIT ?
        """,
        params,
    ).fetchall()

    cards = []
    for row in rows:
        card = dict(row)
        import json

        card["choices"] = json.loads(card.pop("choices_json") or "null")
        card["tags"] = json.loads(card.pop("tags_json") or "[]")
        cards.append(card)
    return cards


def _next_review_at(mastery: int, is_correct: bool) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if not is_correct:
        return now.isoformat()
    return (now + REVIEW_INTERVALS.get(mastery, timedelta(days=1))).isoformat()


def update_progress(conn: sqlite3.Connection, *, card_id: str, is_correct: bool, user_email: str = "") -> dict:
    current = get_card_progress(conn, card_id, user_email=user_email) or {
        "seen_count": 0,
        "correct_count": 0,
        "incorrect_count": 0,
        "streak": 0,
        "mastery": 0,
    }

    seen_count = int(current["seen_count"]) + 1
    correct_count = int(current["correct_count"]) + (1 if is_correct else 0)
    incorrect_count = int(current["incorrect_count"]) + (0 if is_correct else 1)
    streak = int(current["streak"]) + 1 if is_correct else 0
    previous_mastery = int(current["mastery"])
    mastery = min(3, previous_mastery + 1) if is_correct else max(0, previous_mastery - 1)
    now = utc_now()
    next_review_at = _next_review_at(mastery, is_correct)

    conn.execute(
        """
        INSERT INTO card_progress (
            user_email, card_id, seen_count, correct_count, incorrect_count, streak,
            last_seen_at, next_review_at, mastery, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_email, card_id) DO UPDATE SET
            seen_count = excluded.seen_count,
            correct_count = excluded.correct_count,
            incorrect_count = excluded.incorrect_count,
            streak = excluded.streak,
            last_seen_at = excluded.last_seen_at,
            next_review_at = excluded.next_review_at,
            mastery = excluded.mastery,
            updated_at = excluded.updated_at
        """,
        (user_email, card_id, seen_count, correct_count, incorrect_count, streak, now, next_review_at, mastery, now),
    )

    return {
        "card_id": card_id,
        "seen_count": seen_count,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "streak": streak,
        "last_seen_at": now,
        "next_review_at": next_review_at,
        "mastery": mastery,
    }


def record_card_attempt(
    conn: sqlite3.Connection,
    *,
    card_id: str,
    user_answer: str | None,
    elapsed_ms: int | None = None,
    self_grade: bool | None = None,
    user_email: str = "",
) -> dict:
    card = get_card(conn, card_id)
    if card is None:
        raise ValueError("Card not found")

    is_correct = evaluate_answer(card, user_answer, self_grade)
    attempt_id = record_attempt(
        conn,
        card_id=card["id"],
        topic_id=card["topic_id"],
        user_answer=user_answer,
        is_correct=is_correct,
        elapsed_ms=elapsed_ms,
        user_email=user_email,
    )
    progress = update_progress(conn, card_id=card["id"], is_correct=is_correct, user_email=user_email)

    return {
        "attempt_id": attempt_id,
        "is_correct": is_correct,
        "correct_answer": card["answer"],
        "explanation": card.get("explanation"),
        "progress": progress,
    }
