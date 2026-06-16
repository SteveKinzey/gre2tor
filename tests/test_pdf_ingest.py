import json
import sys

from gre2tor.pdf_ingest import (
    draft_cards_from_extracted,
    extract_all_pdfs,
    extract_topic_pdf,
    inspect_source_dir,
    write_draft_cards,
)


class FakePage:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error

    def extract_text(self):
        if self.error:
            raise self.error
        return self.text


class FakeReader:
    def __init__(self, _path):
        self.pages = [FakePage("Page one text."), FakePage(error=RuntimeError("bad scan")), FakePage("Page three text.")]


TOPICS = [
    {
        "id": "algebra",
        "part": 2,
        "title": "Algebra",
        "pdf_filename": "Part 02_Algebra.pdf",
    },
    {
        "id": "geometry",
        "part": 4,
        "title": "Geometry",
        "pdf_filename": "Part 04_Geometry.pdf",
    },
]


def test_inspect_source_dir_reports_missing_and_unexpected(tmp_path):
    (tmp_path / "Part 02_Algebra.pdf").write_bytes(b"fake")
    (tmp_path / "Extra.pdf").write_bytes(b"fake")

    inventory = inspect_source_dir(tmp_path, TOPICS)

    assert inventory.found == ["Extra.pdf", "Part 02_Algebra.pdf"]
    assert inventory.missing == ["Part 04_Geometry.pdf"]
    assert inventory.unexpected == ["Extra.pdf"]
    assert inventory.has_any_expected is True


def test_extract_topic_pdf_rejects_unsafe_pdf_filename(tmp_path):
    unsafe_topic = {**TOPICS[0], "pdf_filename": "../Part 02_Algebra.pdf"}

    try:
        extract_topic_pdf(unsafe_topic, source_dir=tmp_path, out_dir=tmp_path, reader_factory=FakeReader)
    except ValueError as exc:
        assert "plain filename" in str(exc)
    else:  # pragma: no cover - defensive assertion style keeps dependencies minimal
        raise AssertionError("unsafe pdf_filename was accepted")


def test_extract_topic_pdf_writes_page_json_and_keeps_page_errors(tmp_path):
    source_dir = tmp_path / "source"
    out_dir = tmp_path / "extracted"
    source_dir.mkdir()
    (source_dir / "Part 02_Algebra.pdf").write_bytes(b"fake")

    extracted = extract_topic_pdf(TOPICS[0], source_dir=source_dir, out_dir=out_dir, reader_factory=FakeReader)
    output_path = out_dir / "part-02-algebra.json"
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert extracted["page_count"] == 3
    assert extracted["errors"] == ["page 2: bad scan"]
    assert written["topic_id"] == "algebra"
    assert written["pages"][0] == {"page": 1, "text": "Page one text."}
    assert written["pages"][1] == {"page": 2, "text": ""}


def test_extract_all_continues_when_some_pdfs_are_missing(tmp_path):
    source_dir = tmp_path / "source"
    out_dir = tmp_path / "extracted"
    topics_path = tmp_path / "topics.json"
    source_dir.mkdir()
    (source_dir / "Part 02_Algebra.pdf").write_bytes(b"fake")
    topics_path.write_text(json.dumps(TOPICS), encoding="utf-8")

    result = extract_all_pdfs(source_dir=source_dir, out_dir=out_dir, topics_path=topics_path, reader_factory=FakeReader)

    assert len(result["extracted"]) == 1
    assert result["inventory"]["missing"] == ["Part 04_Geometry.pdf"]
    assert result["errors"] == [{"pdf_filename": "Part 02_Algebra.pdf", "error": "page 2: bad scan"}]


def test_draft_cards_are_short_authoring_placeholders(tmp_path):
    extracted = {
        "topic_id": "algebra",
        "topic_title": "Algebra",
        "part": 2,
        "pdf_filename": "Part 02_Algebra.pdf",
        "pages": [
            {"page": 1, "text": "  This is source text. " * 50},
            {"page": 2, "text": ""},
        ],
    }

    drafts = draft_cards_from_extracted(extracted, max_excerpt_chars=80)
    outputs = write_draft_cards([extracted], out_dir=tmp_path / "drafts", max_excerpt_chars=80)
    written = json.loads((tmp_path / "drafts" / "part-02-algebra-drafts.json").read_text(encoding="utf-8"))

    assert len(drafts) == 1
    assert drafts[0]["draft_prompt"] == ""
    assert drafts[0]["draft_answer"] == ""
    assert drafts[0]["status"] == "needs_authoring"
    assert len(drafts[0]["source_excerpt"]) <= 81
    assert outputs == [{"path": str(tmp_path / "drafts" / "part-02-algebra-drafts.json"), "count": 1, "topic_id": "algebra"}]
    assert written == drafts


def test_ingest_cli_draft_flag_and_exit_codes(monkeypatch, tmp_path):
    from scripts import ingest_pdfs

    extracted_item = {"topic_id": "algebra", "pdf_filename": "Part 02_Algebra.pdf", "output_path": str(tmp_path / "out.json"), "page_count": 1}
    calls = {"drafts": False}

    def fake_extract_all_pdfs(source_dir=None, out_dir=None):
        assert source_dir == "source"
        assert out_dir == "out"
        return {
            "source_dir": "source",
            "inventory": {"found": ["Part 02_Algebra.pdf"], "missing": [], "unexpected": []},
            "extracted": [extracted_item],
            "errors": [],
        }

    def fake_write_draft_cards(extracted, out_dir=None):
        calls["drafts"] = True
        assert extracted == [extracted_item]
        assert out_dir == "drafts"
        return [{"path": "drafts/part-02-algebra-drafts.json", "count": 1, "topic_id": "algebra"}]

    monkeypatch.setattr(ingest_pdfs, "extract_all_pdfs", fake_extract_all_pdfs)
    monkeypatch.setattr(ingest_pdfs, "write_draft_cards", fake_write_draft_cards)
    monkeypatch.setattr(sys, "argv", ["ingest_pdfs.py", "--source-dir", "source", "--out-dir", "out", "--draft-cards", "--draft-out-dir", "drafts"])

    assert ingest_pdfs.main() == 0
    assert calls["drafts"] is True

    def fake_empty_extract(source_dir=None, out_dir=None):
        return {
            "source_dir": "source",
            "inventory": {"found": [], "missing": ["Part 02_Algebra.pdf"], "unexpected": []},
            "extracted": [],
            "errors": [],
        }

    monkeypatch.setattr(ingest_pdfs, "extract_all_pdfs", fake_empty_extract)
    monkeypatch.setattr(sys, "argv", ["ingest_pdfs.py", "--source-dir", "source"])

    assert ingest_pdfs.main() == 1
