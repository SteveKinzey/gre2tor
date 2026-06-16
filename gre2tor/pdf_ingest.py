from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any, Callable, Iterable

from .config import BASE_DIR, load_settings
from .seed import DEFAULT_TOPICS_PATH, load_json_array, validate_topics

DEFAULT_EXTRACTED_DIR = BASE_DIR / "data" / "extracted"
DEFAULT_DRAFTS_DIR = BASE_DIR / "data" / "drafts"

ReaderFactory = Callable[[Path], Any]


@dataclass(frozen=True)
class PdfInventory:
    source_dir: Path
    expected: list[str]
    found: list[str]
    missing: list[str]
    unexpected: list[str]

    @property
    def has_any_expected(self) -> bool:
        return any(filename in self.found for filename in self.expected)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_dir": str(self.source_dir),
            "expected": self.expected,
            "found": self.found,
            "missing": self.missing,
            "unexpected": self.unexpected,
        }


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "pdf"


def topic_output_name(topic: dict[str, Any]) -> str:
    return f"part-{int(topic['part']):02d}-{_slug(topic['id'])}.json"


def load_topics(topics_path: str | Path = DEFAULT_TOPICS_PATH) -> list[dict[str, Any]]:
    topics = load_json_array(topics_path)
    validate_topics(topics)
    return sorted(topics, key=lambda item: (int(item["part"]), item["title"]))


def expected_pdf_filenames(topics: Iterable[dict[str, Any]]) -> list[str]:
    return [topic["pdf_filename"] for topic in topics if topic.get("pdf_filename")]


def inspect_source_dir(source_dir: str | Path, topics: Iterable[dict[str, Any]]) -> PdfInventory:
    source_path = Path(source_dir).expanduser()
    expected = expected_pdf_filenames(topics)
    expected_set = set(expected)

    if source_path.exists():
        found = sorted(path.name for path in source_path.glob("*.pdf") if path.is_file())
    else:
        found = []

    found_set = set(found)
    missing = [filename for filename in expected if filename not in found_set]
    unexpected = [filename for filename in found if filename not in expected_set]

    return PdfInventory(
        source_dir=source_path,
        expected=expected,
        found=found,
        missing=missing,
        unexpected=unexpected,
    )


def _default_reader_factory(pdf_path: Path) -> Any:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - exercised only without dependency installed
        raise RuntimeError("pypdf is required for PDF ingestion. Run `pip install -r requirements.txt`.") from exc
    return PdfReader(str(pdf_path))


def extract_pdf_pages(pdf_path: str | Path, *, reader_factory: ReaderFactory | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    path = Path(pdf_path)
    reader = (reader_factory or _default_reader_factory)(path)
    pages: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, page in enumerate(getattr(reader, "pages", []), start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # Keep one bad page from aborting the whole PDF.
            text = ""
            errors.append(f"page {index}: {exc}")
        pages.append({"page": index, "text": text.strip()})

    return pages, errors


def extract_topic_pdf(
    topic: dict[str, Any],
    *,
    source_dir: str | Path,
    out_dir: str | Path = DEFAULT_EXTRACTED_DIR,
    reader_factory: ReaderFactory | None = None,
) -> dict[str, Any]:
    pdf_filename = topic.get("pdf_filename")
    if not pdf_filename:
        raise ValueError(f"Topic {topic.get('id', '<unknown>')} has no pdf_filename")
    if Path(str(pdf_filename)).is_absolute() or "/" in str(pdf_filename) or "\\" in str(pdf_filename):
        raise ValueError(f"Topic {topic.get('id', '<unknown>')} pdf_filename must be a plain filename")

    pdf_path = Path(source_dir).expanduser() / str(pdf_filename)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Missing PDF: {pdf_path}")

    pages, errors = extract_pdf_pages(pdf_path, reader_factory=reader_factory)
    extracted = {
        "topic_id": topic["id"],
        "topic_title": topic["title"],
        "part": int(topic["part"]),
        "pdf_filename": pdf_filename,
        "source_path": str(pdf_path),
        "page_count": len(pages),
        "pages": pages,
        "errors": errors,
    }

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    destination = out_path / topic_output_name(topic)
    destination.write_text(json.dumps(extracted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    extracted["output_path"] = str(destination)
    return extracted


def extract_all_pdfs(
    *,
    source_dir: str | Path | None = None,
    out_dir: str | Path = DEFAULT_EXTRACTED_DIR,
    topics_path: str | Path = DEFAULT_TOPICS_PATH,
    reader_factory: ReaderFactory | None = None,
) -> dict[str, Any]:
    settings = load_settings()
    source_path = Path(source_dir).expanduser() if source_dir else settings.PDF_SOURCE_DIR
    topics = load_topics(topics_path)
    inventory = inspect_source_dir(source_path, topics)

    extracted: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for topic in topics:
        pdf_filename = topic.get("pdf_filename")
        if not pdf_filename or pdf_filename in inventory.missing:
            continue
        try:
            result = extract_topic_pdf(topic, source_dir=source_path, out_dir=out_dir, reader_factory=reader_factory)
            extracted.append(result)
            for error in result.get("errors", []):
                errors.append({"pdf_filename": pdf_filename, "error": error})
        except Exception as exc:
            errors.append({"pdf_filename": pdf_filename, "error": str(exc)})

    return {
        "source_dir": str(source_path),
        "out_dir": str(Path(out_dir)),
        "inventory": inventory.as_dict(),
        "extracted": extracted,
        "errors": errors,
    }


def _clean_excerpt(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    truncated = cleaned[:max_chars].rsplit(" ", 1)[0].strip()
    return f"{truncated}…" if truncated else cleaned[:max_chars]


def draft_cards_from_extracted(
    extracted: dict[str, Any],
    *,
    max_excerpt_chars: int = 700,
) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []

    for page in extracted.get("pages", []):
        text = page.get("text") or ""
        excerpt = _clean_excerpt(text, max_excerpt_chars)
        if not excerpt:
            continue
        drafts.append(
            {
                "topic_id": extracted["topic_id"],
                "source_pdf": extracted["pdf_filename"],
                "source_page": page["page"],
                "draft_prompt": "",
                "draft_answer": "",
                "source_excerpt": excerpt,
                "status": "needs_authoring",
            }
        )
    return drafts


def _draft_output_stem(extracted: dict[str, Any]) -> str:
    if extracted.get("output_path"):
        return Path(str(extracted["output_path"])).stem
    part = int(extracted.get("part", 0))
    topic_id = str(extracted.get("topic_id", "drafts"))
    return f"part-{part:02d}-{_slug(topic_id)}" if part else _slug(topic_id)


def write_draft_cards(
    extracted_items: Iterable[dict[str, Any]],
    *,
    out_dir: str | Path = DEFAULT_DRAFTS_DIR,
    max_excerpt_chars: int = 700,
) -> list[dict[str, Any]]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []

    for extracted in extracted_items:
        drafts = draft_cards_from_extracted(extracted, max_excerpt_chars=max_excerpt_chars)
        destination = out_path / f"{_draft_output_stem(extracted)}-drafts.json"
        destination.write_text(json.dumps(drafts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs.append({"path": str(destination), "count": len(drafts), "topic_id": extracted.get("topic_id")})

    return outputs
