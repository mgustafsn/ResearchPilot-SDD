"""Strict project settings; authoritative paper metadata is not part of this slice."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

Keyword = Annotated[str, Field(min_length=1, max_length=100)]


class ProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    researchQuestion: str = Field(min_length=1, max_length=5000)
    keywords: list[Keyword] = Field(default_factory=list, max_length=30)
    yearFrom: int | None = Field(default=None, ge=1, le=9999)
    yearTo: int | None = Field(default=None, ge=1, le=9999)
    maxPaperCount: int = Field(ge=1, le=250)

    @field_validator("keywords")
    @classmethod
    def unique_keywords(cls, values):
        result, seen = [], set()
        for value in values:
            if value.casefold() not in seen:
                seen.add(value.casefold())
                result.append(value)
        return result

    @field_validator("yearTo")
    @classmethod
    def ordered_years(cls, value, info: ValidationInfo):
        start = info.data.get("yearFrom")
        if value is not None and start is not None and value < start:
            raise ValueError("End year must not precede start year")
        return value


class ProjectOutput(ProjectInput):
    id: UUID
    createdAt: datetime
    updatedAt: datetime
