"""Vendor-free local embedding contract."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
INPUT_VERSION = "ranking-input-v1"
SCORING_VERSION = "calibrated-cosine-v1"


class EmbeddingInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class EmbeddingItem(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    id: str
    vector: list[float]
    token_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    token_count: int = Field(ge=1, le=256)
    truncated: bool

    @field_validator("vector", mode="before")
    @classmethod
    def numeric_components(cls, value):
        if (
            not isinstance(value, list)
            or not value
            or any(type(component) not in (int, float) for component in value)
        ):
            raise ValueError("Invalid vector components")
        return value


class EmbeddingBatch(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    model_id: str
    model_revision: str
    dimension: int = Field(ge=1)
    items: list[EmbeddingItem]
    package_versions: dict[str, str]


class EmbeddingError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__("Local embedding operation failed")


class EmbeddingProvider(Protocol):
    async def embed(self, inputs: list[EmbeddingInput]) -> EmbeddingBatch: ...
