from gre2tor import db
from gre2tor.quiz import evaluate_answer, normalize_answer, record_card_attempt, select_cards, update_progress


TOPIC = {"id": "rates", "part": 8, "title": "Rates", "pdf_filename": "Part 08_Rates.pdf"}
NUMERIC_CARD = {
    "id": "rates-distance",
    "topic_id": "rates",
    "type": "numeric",
    "prompt": "At 30 mph, how far in 2 hours?",
    "answer": "60",
    "difficulty": 1,
}
THEORY_CARD = {
    "id": "rates-formula",
    "topic_id": "rates",
    "type": "theory",
    "prompt": "What is the distance formula?",
    "answer": "distance = rate × time",
    "difficulty": 1,
}
MULTIPLE_CHOICE_CARD = {
    "id": "rates-unit",
    "topic_id": "rates",
    "type": "multiple_choice",
    "prompt": "Which is a rate?",
    "answer": "miles/hour",
    "choices": ["miles", "hours", "miles/hour"],
    "difficulty": 1,
}


def _seed_quiz_db(database_path):
    db.init_db(database_path)
    with db.connection(database_path) as conn:
        db.upsert_topic(conn, TOPIC)
        db.upsert_card(conn, NUMERIC_CARD)
        db.upsert_card(conn, THEORY_CARD)
        db.upsert_card(conn, MULTIPLE_CHOICE_CARD)


def test_normalize_and_evaluate_answer():
    assert normalize_answer("  A − B. ") == "a-b"
    assert evaluate_answer(MULTIPLE_CHOICE_CARD, " Miles / Hour ") is True
    assert evaluate_answer(NUMERIC_CARD, "60.0") is False
    assert evaluate_answer(THEORY_CARD, "anything", self_grade=True) is True
    assert evaluate_answer(THEORY_CARD, "anything", self_grade=False) is False


def test_progress_update_and_card_selection(tmp_path):
    database_path = tmp_path / "quiz.sqlite3"
    _seed_quiz_db(database_path)

    with db.connection(database_path) as conn:
        new_cards = select_cards(conn, topic_id="rates", mode="new", limit=10)
        first = update_progress(conn, card_id="rates-distance", is_correct=True)
        second = update_progress(conn, card_id="rates-distance", is_correct=False)
        missed_cards = select_cards(conn, topic_id="rates", mode="missed", limit=10)

    assert {card["id"] for card in new_cards} == {"rates-distance", "rates-formula", "rates-unit"}
    assert first["seen_count"] == 1
    assert first["mastery"] == 1
    assert second["seen_count"] == 2
    assert second["streak"] == 0
    assert second["mastery"] == 0
    assert [card["id"] for card in missed_cards] == ["rates-distance"]


def test_record_card_attempt_supports_objective_and_self_grade(tmp_path):
    database_path = tmp_path / "attempts.sqlite3"
    _seed_quiz_db(database_path)

    with db.connection(database_path) as conn:
        objective = record_card_attempt(conn, card_id="rates-distance", user_answer="60")
        self_graded = record_card_attempt(conn, card_id="rates-formula", user_answer=None, self_grade=True)

    assert objective["is_correct"] is True
    assert objective["progress"]["correct_count"] == 1
    assert self_graded["is_correct"] is True
    assert self_graded["progress"]["mastery"] == 1
