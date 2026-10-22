"""Provider-normalized scholarly models and deterministic pure retrieval rules."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from researchpilot.ranking_domain import RankingProvenance, RunRankingProvenance


class Paper(BaseModel):
    """Normalized provider facts; never populated from an LLM response."""

    model_config = ConfigDict(extra="forbid", strict=True)

    provider: Literal["openalex"]
    provider_id: str = Field(min_length=1, max_length=255)
    doi: str | None = None
    title: str = Field(min_length=1)
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list, max_length=100)
    publication_year: int | None = Field(default=None, ge=1, le=9999)
    publication_date: date | None = None
    venue: str | None = None
    citation_count: int | None = Field(default=None, ge=0)
    source_url: str
    publication_url: str | None = None
    full_text_url: str | None = None
    is_open_access: StrictBool | None = None

    @field_validator("provider_id", "title", mode="before")
    @classmethod
    def reject_blank_required_text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Required text is missing")
        return value.strip()

    @field_validator("doi", mode="before")
    @classmethod
    def normalize_optional_doi(cls, value):
        return normalize_doi(value)

    @field_validator("abstract", "venue", mode="before")
    @classmethod
    def collapse_optional_text(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Optional metadata must be text")
        value = " ".join(value.split())
        return value or None

    @field_validator("authors", mode="before")
    @classmethod
    def normalize_authors(cls, value):
        if not isinstance(value, list):
            raise ValueError("Authors must be a list")
        return [
            " ".join(author.split())
            for author in value
            if isinstance(author, str) and author.strip()
        ]

    @field_validator("source_url", "publication_url", "full_text_url", mode="before")
    @classmethod
    def require_safe_url(cls, value):
        if value is None:
            return None
        safe = safe_provider_url(value)
        if safe is None:
            raise ValueError("Provider URLs must use http or https")
        return safe

    @model_validator(mode="after")
    def require_valid_source_identity(self):
        if self.provider_id.startswith("http") and safe_provider_url(self.provider_id) is None:
            raise ValueError("Invalid provider identity")
        if not self.source_url:
            raise ValueError("Source URL is required")
        return self


@dataclass(frozen=True)
class QueryAllocation:
    id: str
    text: str
    slot: int
    limit: int


@dataclass(frozen=True)
class DeduplicationResult:
    papers: list[Paper]
    duplicate_count: int


class PaperOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: UUID
    provider: Literal["openalex"]
    providerId: str
    doi: str | None
    title: str
    abstract: str | None
    authors: list[str]
    publicationYear: int | None
    publicationDate: date | None
    venue: str | None
    citationCount: int | None
    sourceUrl: str
    publicationUrl: str | None
    fullTextUrl: str | None
    isOpenAccess: StrictBool | None
    embeddingScore: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    rankingProvenance: RankingProvenance | None = None


class SearchQueryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    allocatedLimit: int = Field(ge=0, le=250)


class SearchAttemptOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    searchRunId: UUID
    status: Literal["pending", "succeeded", "failed"]
    provider: Literal["openalex"]
    startedAt: datetime
    finishedAt: datetime | None
    rawFetchedCount: int = Field(ge=0)
    skippedCount: int = Field(ge=0)
    duplicateCount: int = Field(ge=0)
    queriesUsed: list[SearchQueryOutput]
    queriesUnused: list[SearchQueryOutput]
    errorCode: str | None = None
    rankingProvenance: RunRankingProvenance | None = None


class SearchOutput(SearchAttemptOutput):
    projectId: UUID
    papers: list[PaperOutput]


class CurrentPapersOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    projectId: UUID
    latestAttempt: SearchAttemptOutput | None
    papers: list[PaperOutput]
    rankingProvenance: RunRankingProvenance | None = None


def normalize_doi(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.casefold().startswith("doi:"):
        candidate = candidate[4:].strip()
    try:
        parsed = urlsplit(candidate)
        if parsed.scheme.casefold() in {"http", "https"} and parsed.hostname:
            if parsed.hostname.casefold() in {"doi.org", "dx.doi.org", "www.doi.org"}:
                candidate = parsed.path.lstrip("/")
    except ValueError:
        return None
    candidate = candidate.strip().casefold()
    if not re.fullmatch(r"10\.\d{4,9}/\S+", candidate):
        return None
    return candidate


def normalize_title(value):
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    tokens, current = [], []
    for character in normalized:
        if ord(character) < 128 and character.isalnum():
            current.append(character.lower())
        elif unicodedata.category(character).startswith("M"):
            continue
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return " ".join(tokens)


def publication_year_filters(year_from, year_to):
    for value in (year_from, year_to):
        if value is not None and (type(value) is not int or not 1 <= value <= 9999):
            raise ValueError("Publication years must be whole years from 1 to 9999")
    if year_from is not None and year_to is not None and year_from > year_to:
        raise ValueError("End year must not precede start year")
    filters = {}
    if year_from is not None:
        filters["from_publication_date"] = f"{year_from:04d}-01-01"
    if year_to is not None:
        filters["to_publication_date"] = f"{year_to:04d}-12-31"
    return filters


def allocate_query_budgets(queries, paper_limit):
    if type(paper_limit) is not int or not 1 <= paper_limit <= 250:
        raise ValueError("Paper limit must be an integer from 1 to 250")
    ordered = sorted(queries, key=lambda query: query["slot"])
    if len(ordered) > 20:
        raise ValueError("A project can have at most 20 saved queries")
    for query in ordered:
        if type(query.get("slot")) is not int or query["slot"] < 1:
            raise ValueError("Query slots must be positive integers")
        if type(query.get("enabled")) is not bool:
            raise ValueError("Query enabled state must be boolean")
    enabled = [query for query in ordered if query["enabled"]]
    if not enabled:
        raise NoEnabledQueries("Enable at least one saved query before searching")
    quotient, remainder = divmod(paper_limit, len(enabled))
    used, unused = [], []
    for index, query in enumerate(enabled):
        allocation = quotient + (1 if index < remainder else 0)
        item = QueryAllocation(
            id=str(query["id"]), text=query["text"], slot=query["slot"], limit=allocation
        )
        (used if allocation else unused).append(item)
    return used, unused


class NoEnabledQueries(ValueError):
    pass


def reconstruct_abstract(inverted_index):
    if inverted_index is None:
        return None
    if not isinstance(inverted_index, dict):
        return None
    positioned = []
    for word, positions in inverted_index.items():
        if not isinstance(word, str) or not isinstance(positions, list):
            return None
        for position in positions:
            if type(position) is not int or position < 0:
                return None
            positioned.append((position, word))
    if not positioned:
        return None
    positioned.sort(key=lambda item: item[0])
    if any(left[0] == right[0] for left, right in zip(positioned, positioned[1:])):
        return None
    return " ".join(word for _, word in positioned)


def safe_provider_url(value):
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate or len(candidate) > 4096 or any(ord(char) < 32 for char in candidate):
        return None
    try:
        parsed = urlsplit(candidate)
        _ = parsed.port  # Validate malformed ports.
    except ValueError:
        return None
    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return candidate


def deduplicate_papers(records):
    papers = [
        record if isinstance(record, Paper) else Paper.model_validate(record) for record in records
    ]
    count = len(papers)
    parent = list(range(count))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def component_dois(index):
        representative = root(index)
        return {
            normalize_doi(paper.doi)
            for item, paper in enumerate(papers)
            if root(item) == representative and normalize_doi(paper.doi)
        }

    def merge(left, right):
        left_root, right_root = root(left), root(right)
        if left_root == right_root:
            return True
        if len(component_dois(left_root) | component_dois(right_root)) > 1:
            return False
        # Lower original index is the stable representative, independent of hash order.
        if left_root > right_root:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        return True

    # Identity priorities are applied to complete groups before title fallback.
    doi_groups = {}
    for index, paper in enumerate(papers):
        doi = normalize_doi(paper.doi)
        if doi:
            doi_groups.setdefault(doi, []).append(index)
    for indexes in doi_groups.values():
        for index in indexes[1:]:
            merge(indexes[0], index)

    provider_groups = {}
    for index, paper in enumerate(papers):
        provider_groups.setdefault((paper.provider, paper.provider_id), []).append(index)
    for indexes in provider_groups.values():
        for index in indexes[1:]:
            merge(indexes[0], index)

    title_groups = {}
    for index, paper in enumerate(papers):
        title = normalize_title(paper.title)
        if title:
            title_groups.setdefault(title, []).append(index)
    for indexes in title_groups.values():
        components = []
        for index in indexes:
            representative = root(index)
            if representative not in components:
                components.append(representative)
        distinct_dois = set().union(*(component_dois(item) for item in components))
        if len(distinct_dois) <= 1:
            for component in components[1:]:
                merge(components[0], component)
            continue
        # Ambiguous title groups may merge matching DOI components and DOI-less
        # components among themselves, but a DOI-less record cannot bridge DOIs.
        by_doi = {}
        for component in components:
            dois = component_dois(component)
            key = next(iter(dois)) if dois else None
            by_doi.setdefault(key, []).append(component)
        for same_identity in by_doi.values():
            for component in same_identity[1:]:
                merge(same_identity[0], component)

    groups = {}
    for index, paper in enumerate(papers):
        groups.setdefault(root(index), []).append(index)

    def richness(paper):
        optional = (
            paper.doi,
            paper.abstract,
            paper.authors or None,
            paper.publication_year,
            paper.publication_date,
            paper.venue,
            paper.citation_count,
            paper.publication_url,
            paper.full_text_url,
            paper.is_open_access,
        )
        return sum(value is not None for value in optional)

    merged = []
    for indexes in sorted(groups.values(), key=lambda group: min(group)):
        ordered = sorted(indexes, key=lambda index: (-richness(papers[index]), index))
        primary = papers[ordered[0]].model_copy(
            update={"doi": normalize_doi(papers[ordered[0]].doi)}
        )
        updates = {}
        for field in (
            "doi",
            "abstract",
            "authors",
            "publication_year",
            "publication_date",
            "venue",
            "citation_count",
            "source_url",
            "publication_url",
            "full_text_url",
            "is_open_access",
        ):
            if getattr(primary, field) is not None and getattr(primary, field) != []:
                continue
            for index in ordered[1:]:
                value = getattr(papers[index], field)
                if value is not None and value != []:
                    updates[field] = normalize_doi(value) if field == "doi" else value
                    break
        if updates:
            primary = primary.model_copy(update=updates)
        merged.append(primary)
    return DeduplicationResult(papers=merged, duplicate_count=count - len(merged))
