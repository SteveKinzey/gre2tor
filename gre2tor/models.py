from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Topic:
    id: str
    part: int
    title: str
    pdf_filename: str | None = None
    description: str | None = None
    needs_validation: bool = False


@dataclass(frozen=True)
class Card:
    id: str
    topic_id: str
    type: str
    prompt: str
    answer: str
    explanation: str | None = None
    choices: list[str] | None = None
    difficulty: int = 2
    source_pdf: str | None = None
    source_page: int | None = None
    source_excerpt: str | None = None
    grounding_status: str = "legacy"
    concept_id: str | None = None
    variant_of: str | None = None
    variant_kind: str = "base"
    tags: list[str] = field(default_factory=list)


CardRow = dict[str, Any]
TopicRow = dict[str, Any]
