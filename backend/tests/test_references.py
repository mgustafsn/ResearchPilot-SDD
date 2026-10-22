"""FR-REF-002/004/008 snapshot and response-domain tests."""

import json
from datetime import UTC, datetime
from importlib import import_module
from uuid import uuid4

import pytest
from pydantic import ValidationError
from researchpilot.paper_domain import Paper


def domain():
    return import_module("researchpilot.references_domain")


def paper(provider_id="W1", title="Provider title", **updates):
    value = {
        "provider": "openalex",
        "provider_id": provider_id,
        "doi": None,
        "title": title,
        "abstract": None,
        "authors": ["Author Name"],
        "publication_year": 2024,
        "source_url": f"https://openalex.org/{provider_id}",
        "publication_url": None,
    }
    value.update(updates)
    return Paper.model_validate(value)


def reference(title, provider_id="W1"):
    output = domain().ReferenceOutput
    item = paper(provider_id, title)
    return output(
        id=uuid4(),
        projectId=uuid4(),
        savedAt=datetime.now(UTC),
        **item.model_dump(mode="json", by_alias=True),
    )


def test_FR_REF_002_snapshot_copies_only_normalized_provider_facts():
    value = paper("W17", "  Provider title  ", citation_count=3)
    snapshot = domain().paper_snapshot(value)
    assert snapshot == value.model_dump(mode="json")
    assert snapshot["title"] == "Provider title"
    assert snapshot["provider_id"] == "W17"
    assert not {"embedding_score", "ranking_provenance", "vector"} & set(snapshot)


def test_FR_REF_004_reference_sort_uses_casefold_then_identity():
    values = [reference("Zebra", "W3"), reference("straße", "W2"), reference("STRASSE", "W1")]
    ordered = domain().sort_references(values)
    assert [(item.title.casefold(), item.provider_id) for item in ordered] == [
        ("strasse", "W1"),
        ("strasse", "W2"),
        ("zebra", "W3"),
    ]


def test_FR_REF_008_save_request_is_strict_and_accepts_only_paper_id():
    paper_id = uuid4()
    request_type = domain().ReferenceSaveInput
    request = request_type.model_validate_json(json.dumps({"paperId": str(paper_id)}))
    assert request.paperId == paper_id
    with pytest.raises(ValidationError):
        request_type.model_validate_json(
            json.dumps(
                {
                    "paperId": str(paper_id),
                    "title": "invented",
                }
            )
        )
    with pytest.raises(ValidationError):
        request_type.model_validate_json('{"paperId":"not-a-uuid"}')


def test_FR_REF_008_reference_response_rejects_ranking_fields():
    ReferenceOutput = domain().ReferenceOutput
    value = reference("Saved paper").model_dump(mode="json", by_alias=True)
    value["embeddingScore"] = 0.8
    with pytest.raises(ValidationError):
        ReferenceOutput.model_validate(value)
