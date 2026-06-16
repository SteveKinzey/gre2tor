from gre2tor import db


TOPIC = {
    "id": "algebra",
    "part": 2,
    "title": "Algebra",
    "pdf_filename": "Part 02_Algebra.pdf",
    "description": "Equations and expressions.",
}

CARD = {
    "id": "algebra-solve-linear",
    "topic_id": "algebra",
    "type": "numeric",
    "prompt": "Solve x + 2 = 5.",
    "answer": "3",
    "difficulty": 1,
    "tags": ["equations"],
}


def test_schema_upsert_query_and_attempts(tmp_path):
    database_path = tmp_path / "gre2tor.sqlite3"
    db.init_db(database_path)

    with db.connection(database_path) as conn:
        db.upsert_topic(conn, TOPIC)
        db.upsert_card(conn, CARD)
        attempt_id = db.record_attempt(
            conn,
            card_id=CARD["id"],
            topic_id=TOPIC["id"],
            user_answer="3",
            is_correct=True,
            elapsed_ms=1200,
        )

        topics = db.list_topics(conn)
        cards = db.list_cards(conn)
        attempts = db.list_attempts(conn, card_id=CARD["id"])

    assert attempt_id == 1
    assert [topic["id"] for topic in topics] == [TOPIC["id"]]
    assert cards[0]["choices"] is None
    assert cards[0]["tags"] == ["equations"]
    assert attempts[0]["is_correct"] == 1
    assert attempts[0]["user_answer"] == "3"
