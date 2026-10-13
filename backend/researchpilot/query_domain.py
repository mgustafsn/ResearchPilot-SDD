"""Pure normalized query contracts. No scholarly metadata or vendor imports."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_query(value):
    if not isinstance(value, str):
        raise ValueError("Query text must be text")
    value = " ".join(value.split())
    if not 1 <= len(value) <= 160:
        raise ValueError("Query text must contain 1–160 characters")
    return value


QueryText = Annotated[str, AfterValidator(normalize_query)]


class QueryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class QueryAddInput(QueryModel):
    text: QueryText
    expectedRevision: int = Field(ge=0)
    enabled: bool = True


class QueryPatchInput(QueryModel):
    expectedRevision: int = Field(ge=0)
    text: QueryText | None = None
    enabled: bool | None = None

    @field_validator("text", "enabled", mode="before")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("Supply a real query value")
        return value

    @model_validator(mode="after")
    def require_patch_field(self):
        if not self.model_fields_set.intersection({"text", "enabled"}):
            raise ValueError("Supply query text or enabled state")
        return self


class GenerateInput(QueryModel):
    expectedRevision: int = Field(ge=0)


class SuggestionBatch(QueryModel):
    queries: list[QueryText] = Field(min_length=3, max_length=6)

    @field_validator("queries")
    @classmethod
    def unique_queries(cls, values):
        if len({value.casefold() for value in values}) != len(values):
            raise ValueError("Suggestions must be unique")
        return values


class QueryOutput(QueryModel):
    id: UUID
    projectId: UUID
    text: QueryText
    enabled: bool
    origin: Literal["manual", "generated"]
    userOwned: bool


class QueryListOutput(QueryModel):
    projectId: UUID
    revision: int = Field(ge=0)
    refreshRequired: bool
    generationAvailable: bool
    queries: list[QueryOutput]


def refresh_required(context_revision, generated_revision):
    return context_revision > 0 and generated_revision != context_revision


class NoEnabledQueries(ValueError):
    pass


def enabled_texts(queries):
    result = [query["text"] for query in sorted(queries, key=lambda item: item["slot"])
              if query["enabled"]]
    if not result:
        raise NoEnabledQueries("Enable at least one stored query")
    return result


def becomes_owned(query, text=None, enabled=None):
    return bool(query["user_owned"] or (text is not None and text != query["text"])
                or (enabled is not None and enabled != query["enabled"]))


def merge_plan(queries, batch):
    preserved = [query for query in queries if query["user_owned"]]
    keys = {query["normalized_key"] for query in preserved}
    occupied = {query["slot"] for query in preserved}
    free = iter(slot for slot in range(1, 21) if slot not in occupied)
    additions, duplicates, capacity = [], 0, 0
    for value in batch.queries:
        if value.casefold() in keys:
            duplicates += 1
            continue
        slot = next(free, None)
        if slot is None:
            capacity += 1
        else:
            additions.append({"text": value, "slot": slot})
    return {"preserved": preserved, "additions": additions,
            "replacedCount": len(queries) - len(preserved),
            "duplicateSkippedCount": duplicates, "capacitySkippedCount": capacity}
