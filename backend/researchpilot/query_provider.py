"""Common async suggestion capability, with no vendor dependency."""

from dataclasses import dataclass
from typing import Protocol

from pydantic import Field

from researchpilot.query_domain import QueryModel, SuggestionBatch


@dataclass(frozen=True)
class SuggestionContext:
    question: str
    keywords: tuple[str, ...]


class SuggestionMetadata(QueryModel):
    model: str
    promptVersion: str
    durationSeconds: float = Field(default=0, ge=0)
    inputTokens: int | None = Field(default=None, ge=0)
    outputTokens: int | None = Field(default=None, ge=0)
    totalTokens: int | None = Field(default=None, ge=0)


class SuggestionResult(QueryModel):
    batch: SuggestionBatch
    metadata: SuggestionMetadata | None = None


class QuerySuggestionProvider(Protocol):
    async def suggest(self, context: SuggestionContext) -> SuggestionResult: ...


class SuggestionProviderError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__("Suggestion provider failed")
