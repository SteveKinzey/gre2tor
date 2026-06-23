from __future__ import annotations

from .config import load_settings
from .db import (
    connection,
    get_card,
    get_overall_progress,
    get_topic_stats,
    init_db,
    list_attempts,
    list_cards_with_progress,
    list_review_cards,
    list_topic_stats,
)
from .quiz import record_card_attempt, select_cards
from .seed import upsert_seed_data
from .updates import check_for_updates
from .version import APP_VERSION


def create_app(config_override: dict | None = None):
    """Create the local Flask app."""

    from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

    settings = load_settings(overrides=config_override)
    app = Flask(
        __name__,
        instance_path=str(settings.INSTANCE_PATH),
        instance_relative_config=True,
        template_folder=str(settings.BASE_DIR / "templates"),
        static_folder=str(settings.BASE_DIR / "static"),
    )
    app.config.from_mapping(settings.as_flask_config())

    settings.INSTANCE_PATH.mkdir(parents=True, exist_ok=True)
    init_db(settings.DATABASE_PATH)
    upsert_seed_data(database_path=settings.DATABASE_PATH)

    @app.template_filter("pct")
    def pct(value):
        if value is None:
            return "—"
        return f"{float(value):.1f}%"

    @app.context_processor
    def inject_app_metadata():
        return {"app_version": APP_VERSION, "update_info": check_for_updates()}

    @app.get("/")
    def index():
        with connection(settings.DATABASE_PATH) as conn:
            stats = get_overall_progress(conn)
            topics = list_topic_stats(conn)
            recent_attempts = list_attempts(conn, limit=5)
        return render_template("index.html", stats=stats, topics=topics, recent_attempts=recent_attempts)

    @app.get("/topics")
    def topics():
        with connection(settings.DATABASE_PATH) as conn:
            topic_stats = list_topic_stats(conn)
        return render_template("topics.html", topics=topic_stats)

    @app.get("/topics/<topic_id>")
    def topic_detail(topic_id: str):
        with connection(settings.DATABASE_PATH) as conn:
            topic = get_topic_stats(conn, topic_id)
            if topic is None:
                abort(404)
            cards = list_cards_with_progress(conn, topic_id=topic_id)
        return render_template("topic_detail.html", topic=topic, cards=cards)

    @app.get("/quiz")
    def quiz():
        topic_id = request.args.get("topic_id") or None
        mode = request.args.get("mode", "all")
        limit = request.args.get("limit", 10)
        with connection(settings.DATABASE_PATH) as conn:
            cards = select_cards(conn, topic_id=topic_id, mode=mode, limit=limit)
            topic = get_topic_stats(conn, topic_id) if topic_id else None
        return render_template("quiz.html", cards=cards, topic=topic, mode=mode, limit=limit)

    @app.post("/api/attempts")
    def api_attempts():
        payload = request.get_json(silent=True) or {}
        card_id = payload.get("card_id")
        if not card_id:
            return jsonify({"error": "card_id is required"}), 400

        elapsed_ms = payload.get("elapsed_ms")
        try:
            elapsed_ms = int(elapsed_ms) if elapsed_ms is not None else None
        except (TypeError, ValueError):
            elapsed_ms = None

        self_grade = payload.get("is_correct")
        if self_grade is not None and not isinstance(self_grade, bool):
            return jsonify({"error": "is_correct must be a boolean when provided"}), 400

        try:
            with connection(settings.DATABASE_PATH) as conn:
                result = record_card_attempt(
                    conn,
                    card_id=card_id,
                    user_answer=payload.get("user_answer"),
                    elapsed_ms=elapsed_ms,
                    self_grade=self_grade,
                )
        except ValueError:
            return jsonify({"error": "Card not found"}), 404

        return jsonify(result)

    @app.get("/review")
    def review():
        with connection(settings.DATABASE_PATH) as conn:
            cards = list_review_cards(conn)
        return render_template("review.html", cards=cards)

    @app.get("/cards/<card_id>")
    def card_detail(card_id: str):
        with connection(settings.DATABASE_PATH) as conn:
            card = get_card(conn, card_id)
            if card is None:
                abort(404)
            cards_with_progress = list_cards_with_progress(conn, topic_id=card["topic_id"])
            progress_card = next((item for item in cards_with_progress if item["id"] == card_id), card)
            attempts = list_attempts(conn, card_id=card_id, limit=20)
        return render_template("card_detail.html", card=progress_card, attempts=attempts)

    @app.get("/health")
    def health():
        with connection(settings.DATABASE_PATH) as conn:
            stats = get_overall_progress(conn)
        return jsonify({"ok": True, "version": APP_VERSION, **stats})

    @app.get("/api/updates")
    def api_updates():
        force = request.args.get("force") == "1"
        return jsonify(check_for_updates(force=force))

    @app.get("/study")
    def study_redirect():
        return redirect(url_for("quiz"))

    return app
