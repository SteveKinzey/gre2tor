from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import BASE_DIR, load_settings
from .db import connection, init_db, upsert_card, upsert_topic

DEFAULT_TOPICS_PATH = BASE_DIR / "data" / "seed" / "topics.json"
DEFAULT_CARDS_PATH = BASE_DIR / "data" / "seed" / "cards.json"

REQUIRED_TOPIC_FIELDS = {"id", "part", "title"}
REQUIRED_CARD_FIELDS = {"id", "topic_id", "type", "prompt", "answer"}


def load_json_array(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{path} must contain an array of objects")
    return data


def _require_fields(kind: str, item: dict[str, Any], required: set[str]) -> None:
    missing = sorted(field for field in required if item.get(field) in (None, ""))
    if missing:
        item_id = item.get("id", "<missing id>")
        raise ValueError(f"{kind} {item_id} missing required fields: {', '.join(missing)}")


def validate_topics(topics: list[dict[str, Any]]) -> None:
    seen = set()
    for topic in topics:
        _require_fields("Topic", topic, REQUIRED_TOPIC_FIELDS)
        if topic["id"] in seen:
            raise ValueError(f"Duplicate topic id: {topic['id']}")
        seen.add(topic["id"])
        topic["part"] = int(topic["part"])


def validate_cards(cards: list[dict[str, Any]], topic_ids: set[str]) -> None:
    seen = set()
    for card in cards:
        _require_fields("Card", card, REQUIRED_CARD_FIELDS)
        if card["id"] in seen:
            raise ValueError(f"Duplicate card id: {card['id']}")
        seen.add(card["id"])
        if card["topic_id"] not in topic_ids:
            raise ValueError(f"Card {card['id']} references unknown topic_id {card['topic_id']}")
        if "difficulty" in card:
            difficulty = int(card["difficulty"])
            if difficulty < 1 or difficulty > 5:
                raise ValueError(f"Card {card['id']} difficulty must be 1-5")
            card["difficulty"] = difficulty
        if card["type"] == "multiple_choice" and not card.get("choices"):
            raise ValueError(f"Card {card['id']} is multiple_choice but has no choices")


def upsert_seed_data(
    *,
    database_path: str | Path | None = None,
    topics_path: str | Path = DEFAULT_TOPICS_PATH,
    cards_path: str | Path = DEFAULT_CARDS_PATH,
) -> dict[str, int]:
    settings = load_settings()
    db_path = Path(database_path) if database_path else settings.DATABASE_PATH

    topics = load_json_array(topics_path)
    cards = load_json_array(cards_path)
    validate_topics(topics)
    validate_cards(cards, {topic["id"] for topic in topics})

    init_db(db_path)
    with connection(db_path) as conn:
        for topic in topics:
            upsert_topic(conn, topic)
        for card in cards:
            upsert_card(conn, card)

    return {"topics": len(topics), "cards": len(cards)}
