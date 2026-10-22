"""Provider-derived, immutable saved-reference snapshots and API models."""

import json
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from researchpilot.paper_domain import Paper


class ReferenceSaveInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paperId: UUID


class ReferenceOutput(Paper):
    """Provider paper facts plus saved-reference identity, without ranking state."""

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(alias="projectId")
    provider: Literal["openalex"]
    provider_id: str = Field(alias="providerId", min_length=1, max_length=255)
    doi: str | None
    title: str
    abstract: str | None
    authors: list[str]
    publication_year: int | None = Field(alias="publicationYear", ge=1, le=9999)
    publication_date: date | None = Field(alias="publicationDate")
    venue: str | None
    citation_count: int | None = Field(alias="citationCount", ge=0)
    source_url: str = Field(alias="sourceUrl")
    publication_url: str | None = Field(alias="publicationUrl")
    full_text_url: str | None = Field(alias="fullTextUrl")
    is_open_access: StrictBool | None = Field(alias="isOpenAccess")
    saved_at: datetime = Field(alias="savedAt")


class ReferenceListOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    projectId: UUID
    references: list[ReferenceOutput]


class ReferenceError(Exception):
    def __init__(self, code):
        self.code = code


def paper_snapshot(paper: Paper) -> dict:
    """Return only normalized provider fields, serialized as JSON-safe primitives."""
    if not isinstance(paper, Paper):
        raise TypeError("A normalized provider Paper is required")
    return paper.model_dump(mode="json")


def reference_output(row) -> ReferenceOutput:
    # JSONB returns JSON primitives (including ISO date strings); JSON-mode
    # validation preserves the strict Paper model while parsing those values.
    paper = Paper.model_validate_json(json.dumps(row["paper_snapshot"]))
    values = paper.model_dump(mode="python")
    values.update(id=row["id"], project_id=row["project_id"], saved_at=row["saved_at"])
    return ReferenceOutput.model_validate(values)


def sort_references(values: list[ReferenceOutput]) -> list[ReferenceOutput]:
    return sorted(
        values,
        key=lambda item: (
            item.title.casefold(),
            item.provider,
            item.provider_id,
        ),
    )
