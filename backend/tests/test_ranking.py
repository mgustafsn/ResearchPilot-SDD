"""FR-RNK-001–004/006 pure rule tests, no services or model weights."""

import hashlib
import math

import pytest
from researchpilot.embedding_provider import (
    MODEL_ID,
    MODEL_REVISION,
    EmbeddingBatch,
    EmbeddingError,
    EmbeddingInput,
    EmbeddingItem,
)
from researchpilot.paper_domain import Paper
from researchpilot.ranking_domain import (
    context_text,
    normalize_text,
    paper_text,
    rank_papers,
    similarity_score,
    text_hash,
    token_hash,
    validate_batch,
)


def paper(identity="W1", title="Title", abstract=None):
    return Paper(
        provider="openalex",
        provider_id=identity,
        title=title,
        abstract=abstract,
        source_url=f"https://openalex.org/{identity}",
    )


def batch_for(inputs):
    return EmbeddingBatch(
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        dimension=2,
        package_versions={"test": "1"},
        items=[
            EmbeddingItem(
                id=i.id, vector=[1.0, 0.0], token_hash="a" * 64, token_count=3, truncated=False
            )
            for i in inputs
        ],
    )


def test_FR_RNK_001_exact_inputs():
    assert normalize_text("  Cafe\u0301\n\tStudy! ") == "Café Study!"
    assert context_text("  Why\nAI? ", [" education ", "", "  ML\tmodels "]) == (
        "Why AI?\nKeywords: education; ML models"
    )
    assert context_text(" Question ", []) == "Question"
    assert paper_text(paper(abstract="Available abstract")) == "Title\nAvailable abstract"
    assert paper_text(paper()) == "Title"


def test_FR_RNK_006_hashes_are_exact():
    assert text_hash("Café\nTitle") == hashlib.sha256("Café\nTitle".encode()).hexdigest()
    assert token_hash([101, 12, 102]) == hashlib.sha256(b"[101,12,102]").hexdigest()
    assert text_hash("Title") != text_hash("title")


@pytest.mark.parametrize(
    "cosine,expected", [(-1, 0), (0, 0), (0.25, 0), (0.425, 0.5), (0.6, 1), (1, 1)]
)
def test_FR_RNK_003_calibration(cosine, expected):
    assert similarity_score([1.0, 0.0], [cosine, math.sqrt(1 - cosine**2)]) == expected


def test_FR_RNK_003_zero_and_large_finite_vectors():
    assert similarity_score([0, 0], [1, 2]) == 0
    assert similarity_score([1e308, 1e308], [1e308, 1e308]) == 1
    assert similarity_score([1e-308, 0], [1e-308, 0]) == 1


@pytest.mark.parametrize(
    "vector", [[True, 0], [float("nan"), 0], [float("inf"), 0], [], ["1", 0], [1]]
)
def test_FR_RNK_002_reject_invalid_cosine_vectors(vector):
    with pytest.raises(EmbeddingError):
        similarity_score(vector, [1, 0])


def test_FR_RNK_002_complete_ordered_batch():
    inputs = [EmbeddingInput(id="context", text="Q"), EmbeddingInput(id="W1", text="T")]
    assert validate_batch(inputs, batch_for(inputs)).dimension == 2


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "extra",
        "duplicate",
        "order",
        "dimension",
        "nan",
        "boolean",
        "hash",
        "tokens",
        "model",
        "revision",
        "empty",
        "duplicate_input",
    ],
)
def test_FR_RNK_002_batch_failures(defect):
    inputs = [EmbeddingInput(id="context", text="Q"), EmbeddingInput(id="W1", text="T")]
    data = batch_for(inputs).model_dump()
    if defect == "missing":
        data["items"].pop()
    elif defect == "extra":
        data["items"].append(dict(data["items"][0], id="other"))
    elif defect == "duplicate":
        data["items"][1]["id"] = "context"
    elif defect == "order":
        data["items"].reverse()
    elif defect == "dimension":
        data["dimension"] = 3
    elif defect == "nan":
        data["items"][0]["vector"][0] = float("nan")
    elif defect == "boolean":
        data["items"][0]["vector"][0] = True
    elif defect == "hash":
        data["items"][0]["token_hash"] = "bad"
    elif defect == "tokens":
        data["items"][0]["token_count"] = 257
    elif defect == "model":
        data["model_id"] = "other"
    elif defect == "revision":
        data["model_revision"] = "main"
    elif defect == "empty":
        inputs = []
    elif defect == "duplicate_input":
        inputs[1] = inputs[0]
    with pytest.raises(EmbeddingError):
        validate_batch(inputs, data)


def test_FR_RNK_004_score_then_casefolded_title_then_source():
    papers = [paper("W3", "z"), paper("W2", "Alpha"), paper("W1", "alpha")]
    assert [p.provider_id for p in rank_papers(papers, [1, 0.5, 0.5])] == ["W3", "W1", "W2"]
    assert len(rank_papers(papers, [0, 0, 0])) == 3
