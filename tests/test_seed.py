import json

from gre2tor import db
from gre2tor.quiz import record_card_attempt
from gre2tor.seed import load_json_array, upsert_seed_data, validate_cards, validate_topics


def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_seed_validation_and_idempotent_upsert_preserves_progress(tmp_path):
    topics = [
        {
            "id": "fractions-decimals",
            "part": 1,
            "title": "Fractions & Decimals",
            "pdf_filename": "Part 01_Fractions & Decimals.pdf",
        }
    ]
    cards = [
        {
            "id": "fractions-decimals-half",
            "topic_id": "fractions-decimals",
            "type": "numeric",
            "prompt": "What is 1/2 as a decimal?",
            "answer": "0.5",
            "difficulty": 1,
            "tags": ["conversion"],
        }
    ]
    topics_path = tmp_path / "topics.json"
    cards_path = tmp_path / "cards.json"
    database_path = tmp_path / "gre2tor.sqlite3"
    _write_json(topics_path, topics)
    _write_json(cards_path, cards)

    loaded_topics = load_json_array(topics_path)
    loaded_cards = load_json_array(cards_path)
    validate_topics(loaded_topics)
    validate_cards(loaded_cards, {"fractions-decimals"})

    first = upsert_seed_data(database_path=database_path, topics_path=topics_path, cards_path=cards_path)
    with db.connection(database_path) as conn:
        result = record_card_attempt(conn, card_id="fractions-decimals-half", user_answer="0.5")
        progress_before = db.get_card_progress(conn, "fractions-decimals-half")

    second = upsert_seed_data(database_path=database_path, topics_path=topics_path, cards_path=cards_path)
    with db.connection(database_path) as conn:
        progress_after = db.get_card_progress(conn, "fractions-decimals-half")
        attempts = db.list_attempts(conn, card_id="fractions-decimals-half")

    assert first == {"topics": 1, "cards": 1}
    assert second == {"topics": 1, "cards": 1}
    assert result["is_correct"] is True
    assert progress_before["seen_count"] == 1
    assert progress_after["seen_count"] == 1
    assert progress_after["correct_count"] == 1
    assert len(attempts) == 1
