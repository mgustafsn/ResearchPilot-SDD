"""Pure input, vector validation and ranking rules; no vendor dependencies."""

import hashlib
import json
import math
import unicodedata
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from researchpilot.embedding_provider import (
    MODEL_ID,
    MODEL_REVISION,
    EmbeddingBatch,
    EmbeddingError,
)


class RankingProvenance(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    modelId: Literal["sentence-transformers/all-MiniLM-L6-v2"]
    modelRevision: Literal["1110a243fdf4706b3f48f1d95db1a4f5529b4d41"]
    dimension: Literal[384]
    scoringVersion: Literal["calibrated-cosine-v1"]
    inputVersion: Literal["ranking-input-v1"]
    maxTokens: Literal[256]
    inputHash: str = Field(pattern=r"^[a-f0-9]{64}$")
    tokenHash: str = Field(pattern=r"^[a-f0-9]{64}$")
    tokenCount: int = Field(ge=1, le=256)
    truncated: bool
    searchRunId: str


class RunRankingProvenance(RankingProvenance):
    rankedPaperCount: int = Field(ge=1, le=250)
    durationMs: float = Field(ge=0, allow_inf_nan=False)
    packageVersions: dict[str, str]


def make_provenance(item, input_text, run_id: UUID):
    from researchpilot.embedding_provider import INPUT_VERSION, SCORING_VERSION

    return RankingProvenance(
        modelId=MODEL_ID,
        modelRevision=MODEL_REVISION,
        dimension=384,
        scoringVersion=SCORING_VERSION,
        inputVersion=INPUT_VERSION,
        maxTokens=256,
        inputHash=text_hash(input_text),
        tokenHash=item.token_hash,
        tokenCount=item.token_count,
        truncated=item.truncated,
        searchRunId=str(run_id),
    )


def normalize_text(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def context_text(question, keywords):
    normalized = [normalize_text(word) for word in keywords if normalize_text(word)]
    return normalize_text(question) + ("\nKeywords: " + "; ".join(normalized) if normalized else "")


def paper_text(paper):
    abstract = normalize_text(paper.abstract or "")
    return normalize_text(paper.title) + ("\n" + abstract if abstract else "")


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def token_hash(tokens):
    return text_hash(json.dumps(tokens, separators=(",", ":")))


def validate_batch(inputs, batch):
    try:
        # Round-trip model instances too: unsafe model_construct must not bypass checks.
        data = batch.model_dump() if isinstance(batch, EmbeddingBatch) else batch
        parsed = EmbeddingBatch.model_validate(data)
        identities = [item.id for item in inputs]
        if (
            not 1 <= len(inputs) <= 251
            or len(set(identities)) != len(inputs)
            or [item.id for item in parsed.items] != identities
            or parsed.model_id != MODEL_ID
            or parsed.model_revision != MODEL_REVISION
        ):
            raise ValueError
        for item in parsed.items:
            if len(item.vector) != parsed.dimension or not all(map(math.isfinite, item.vector)):
                raise ValueError
        return parsed
    except (ValidationError, ValueError, TypeError, OverflowError):
        raise EmbeddingError("invalid_response") from None


def similarity_score(first, second):
    try:
        if not first or len(first) != len(second):
            raise ValueError
        for vector in (first, second):
            if any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
                raise ValueError
        # Scaling first avoids overflow/underflow even for adversarial finite inputs.
        a_scale, b_scale = max(map(abs, first)), max(map(abs, second))
        if not a_scale or not b_scale:
            return 0.0
        a, b = [x / a_scale for x in first], [x / b_scale for x in second]
        a_norm, b_norm = math.hypot(*a), math.hypot(*b)
        cosine = math.fsum((x / a_norm) * (y / b_norm) for x, y in zip(a, b))
        return round(max(0.0, min(1.0, (cosine - 0.25) / 0.35)), 6)
    except (ValueError, TypeError, OverflowError):
        raise EmbeddingError("invalid_response") from None


def rank_papers(papers, scores):
    if len(papers) != len(scores):
        raise EmbeddingError("invalid_response")
    paired = zip(papers, scores, strict=True)
    return [
        paper
        for paper, _ in sorted(
            paired,
            key=lambda item: (
                -item[1],
                item[0].title.casefold(),
                item[0].provider,
                item[0].provider_id,
            ),
        )
    ]
