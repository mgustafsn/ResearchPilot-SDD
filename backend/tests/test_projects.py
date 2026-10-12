"""FR-PRJ-002–005/007: strict boundaries and deterministic normalization."""

import pytest
from pydantic import ValidationError
from researchpilot.domain import ProjectInput

VALID = {"title": "A project", "researchQuestion": "A research question", "maxPaperCount": 100}


def test_FR_PRJ_002_003_normalizes_and_preserves_first_spelling():
    model = ProjectInput(**dict(VALID, title="  A project\n", researchQuestion=" Question ",
                               keywords=[" LLM ", "llm", "Straße", "STRASSE", "Testing"]))
    assert model.title == "A project"
    assert model.researchQuestion == "Question"
    assert model.keywords == ["LLM", "Straße", "Testing"]


def test_FR_PRJ_003_004_optional_fields():
    model = ProjectInput(**VALID)
    assert model.keywords == []
    assert model.yearFrom is None and model.yearTo is None


@pytest.mark.parametrize("field,value", [
    ("title", ""), ("title", " \t\n"), ("title", "x" * 201),
    ("researchQuestion", ""), ("researchQuestion", " \n"), ("researchQuestion", "x" * 5001),
    ("keywords", ["x"] * 31), ("keywords", [""]), ("keywords", [" \n"]),
    ("keywords", ["x" * 101]), ("keywords", None), ("keywords", "keyword"),
    ("yearFrom", 0), ("yearFrom", 10000), ("yearTo", 0), ("yearTo", 10000),
    ("maxPaperCount", 0), ("maxPaperCount", 251), ("maxPaperCount", None),
    ("unexpected", "value"), ("title", 123), ("researchQuestion", False),
])
def test_FR_PRJ_002_005_007_rejects_invalid_boundaries(field, value):
    with pytest.raises(ValidationError):
        ProjectInput(**dict(VALID, **{field: value}))


@pytest.mark.parametrize("field", ["yearFrom", "yearTo", "maxPaperCount"])
@pytest.mark.parametrize("value", [True, False, "1", 1.0, 1.5])
def test_FR_PRJ_004_005_rejects_coercible_integers(field, value):
    with pytest.raises(ValidationError):
        ProjectInput(**dict(VALID, **{field: value}))


@pytest.mark.parametrize("values", [
    {"title": "x", "researchQuestion": "y", "maxPaperCount": 1},
    {"title": "x" * 200, "researchQuestion": "y" * 5000, "maxPaperCount": 250},
    {"keywords": [str(i) for i in range(30)]}, {"keywords": ["x" * 100]},
    {"yearFrom": 1, "yearTo": 9999}, {"yearFrom": 9999, "yearTo": None},
    {"yearFrom": None, "yearTo": 1}, {"yearFrom": 2026, "yearTo": 2026},
])
def test_FR_PRJ_002_005_accepts_exact_boundaries(values):
    ProjectInput(**dict(VALID, **values))


def test_FR_PRJ_004_rejects_reversed_years():
    with pytest.raises(ValidationError):
        ProjectInput(**dict(VALID, yearFrom=2026, yearTo=2020))


@pytest.mark.parametrize("field", ["title", "researchQuestion", "maxPaperCount"])
def test_FR_PRJ_002_005_required_fields(field):
    values = dict(VALID)
    values.pop(field)
    with pytest.raises(ValidationError):
        ProjectInput(**values)
