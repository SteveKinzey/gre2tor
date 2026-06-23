from __future__ import annotations

from email.message import EmailMessage
import re
import smtplib
import sqlite3
from typing import Any

from flask import url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .db import utc_now

MAGIC_LINK_MAX_AGE_SECONDS = 15 * 60


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def allowed_email(email: str, allowed_emails: set[str]) -> bool:
    return not allowed_emails or email in allowed_emails


def serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret_key, salt="gre2tor-magic-link")


def create_magic_token(secret_key: str, email: str) -> str:
    return serializer(secret_key).dumps({"email": normalize_email(email)})


def verify_magic_token(secret_key: str, token: str) -> str | None:
    try:
        data = serializer(secret_key).loads(token, max_age=MAGIC_LINK_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    email = normalize_email(data.get("email") if isinstance(data, dict) else None)
    return email if is_valid_email(email) else None


def magic_link_for(email: str, token: str) -> str:
    return url_for("magic_login", token=token, _external=True)


def smtp_is_configured(settings: Any) -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_magic_link(settings: Any, *, email: str, link: str) -> None:
    if not smtp_is_configured(settings):
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = "Your GRE2Tor login link"
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message.set_content(
        "Use this secure link to sign in to GRE2Tor.\n\n"
        f"{link}\n\n"
        "This link expires in 15 minutes. If you did not request it, ignore this email."
    )

    if settings.SMTP_USE_TLS:
        smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        try:
            smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        finally:
            smtp.quit()
    else:
        smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        try:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        finally:
            smtp.quit()


def upsert_user_login(conn: sqlite3.Connection, email: str) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO users (email, created_at, last_login_at)
        VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            last_login_at = excluded.last_login_at
        """,
        (email, now, now),
    )
