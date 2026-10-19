"""Vendor-neutral PaperProvider protocol and bounded search result types."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from researchpilot.paper_domain import Paper


class PaperProviderError(Exception):
    """Sanitized upstream failure category; never carries raw provider text."""

    def __init__(
        self,
        category: Literal["rate_limited", "timeout", "unavailable", "invalid_response"],
        raw_count=0,
        skipped_count=0,
        request_count=0,
        provider_cost_usd=None,
    ):
        self.category = category
        self.raw_count = raw_count
        self.skipped_count = skipped_count
        self.request_count = request_count
        self.provider_cost_usd = provider_cost_usd
        super().__init__("Paper provider request failed")


class PaperSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    papers: list[Paper]
    raw_count: int = Field(ge=0)
    skipped_count: int = Field(default=0, ge=0)
    request_count: int = Field(ge=0)
    provider_cost_usd: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def counts_match(self):
        if self.raw_count != len(self.papers) + self.skipped_count:
            raise ValueError("Raw count must equal normalized plus skipped provider records")
        return self


class PaperProvider(Protocol):
    async def search(
        self, query: str, year_from: int | None, year_to: int | None, limit: int
    ) -> PaperSearchResult: ...
