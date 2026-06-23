from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys


def _is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def _resource_base_dir() -> Path:
    if _is_packaged():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def _user_data_dir() -> Path:
    override = os.environ.get("GRE2TOR_USER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "GRE2Tor"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "GRE2Tor"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "gre2tor"


BASE_DIR = _resource_base_dir()
DEFAULT_PDF_SOURCE_DIR = Path(
    "/Users/skinzey/Library/CloudStorage/GoogleDrive-steve@sk-america.com/My Drive/Math Bible (1)"
)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(value: str | Path, *, base_dir: Path = BASE_DIR) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path


@dataclass(frozen=True)
class Settings:
    BASE_DIR: Path
    INSTANCE_PATH: Path
    DATABASE_PATH: Path
    PDF_SOURCE_DIR: Path
    FLASK_DEBUG: bool
    SECRET_KEY: str
    AUTH_ALLOWED_EMAILS: set[str]
    AUTH_ALLOW_DEV_MAGIC_LINK: bool
    SMTP_HOST: str | None
    SMTP_PORT: int
    SMTP_USERNAME: str | None
    SMTP_PASSWORD: str | None
    SMTP_FROM: str | None
    SMTP_USE_TLS: bool

    def as_flask_config(self) -> dict:
        return {
            "BASE_DIR": self.BASE_DIR,
            "DATABASE_PATH": self.DATABASE_PATH,
            "PDF_SOURCE_DIR": self.PDF_SOURCE_DIR,
            "FLASK_DEBUG": self.FLASK_DEBUG,
            "SECRET_KEY": self.SECRET_KEY,
            "AUTH_ALLOWED_EMAILS": self.AUTH_ALLOWED_EMAILS,
            "AUTH_ALLOW_DEV_MAGIC_LINK": self.AUTH_ALLOW_DEV_MAGIC_LINK,
        }


def load_settings(*, env_file: bool = True, overrides: dict | None = None) -> Settings:
    if env_file:
        _load_env_file(BASE_DIR / ".env")

    overrides = overrides or {}
    default_instance_path = _user_data_dir() if _is_packaged() else BASE_DIR / "instance"
    default_database_path = default_instance_path / "gre2tor.sqlite3" if _is_packaged() else "instance/gre2tor.sqlite3"
    instance_path = _resolve_path(overrides.get("INSTANCE_PATH", os.environ.get("INSTANCE_PATH", default_instance_path)))
    database_path = _resolve_path(overrides.get("DATABASE_PATH", os.environ.get("DATABASE_PATH", default_database_path)))
    pdf_source_dir = _resolve_path(overrides.get("PDF_SOURCE_DIR", os.environ.get("PDF_SOURCE_DIR", DEFAULT_PDF_SOURCE_DIR)))

    allowed_emails_raw = str(overrides.get("AUTH_ALLOWED_EMAILS", os.environ.get("AUTH_ALLOWED_EMAILS", "")))
    allowed_emails = {email.strip().lower() for email in allowed_emails_raw.split(",") if email.strip()}

    return Settings(
        BASE_DIR=BASE_DIR,
        INSTANCE_PATH=instance_path,
        DATABASE_PATH=database_path,
        PDF_SOURCE_DIR=pdf_source_dir,
        FLASK_DEBUG=bool(overrides.get("FLASK_DEBUG", _bool_env("FLASK_DEBUG", False))),
        SECRET_KEY=str(overrides.get("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-only-secret-key"))),
        AUTH_ALLOWED_EMAILS=allowed_emails,
        AUTH_ALLOW_DEV_MAGIC_LINK=bool(overrides.get("AUTH_ALLOW_DEV_MAGIC_LINK", _bool_env("AUTH_ALLOW_DEV_MAGIC_LINK", False))),
        SMTP_HOST=overrides.get("SMTP_HOST", os.environ.get("SMTP_HOST")),
        SMTP_PORT=int(overrides.get("SMTP_PORT", os.environ.get("SMTP_PORT", "587"))),
        SMTP_USERNAME=overrides.get("SMTP_USERNAME", os.environ.get("SMTP_USERNAME")),
        SMTP_PASSWORD=overrides.get("SMTP_PASSWORD", os.environ.get("SMTP_PASSWORD")),
        SMTP_FROM=overrides.get("SMTP_FROM", os.environ.get("SMTP_FROM")),
        SMTP_USE_TLS=bool(overrides.get("SMTP_USE_TLS", _bool_env("SMTP_USE_TLS", True))),
    )
