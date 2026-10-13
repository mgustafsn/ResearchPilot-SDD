"""FR-QRY-001–010: pure query invariants, without provider/network calls."""

import pytest
from pydantic import ValidationError
from researchpilot import query_domain as domain
from researchpilot.query_provider import SuggestionContext, SuggestionMetadata


def test_FR_QRY_002_whitespace_normalization():
    assert domain.normalize_query("  AI\n\t tutoring\u2003education ") == "AI tutoring education"


@pytest.mark.parametrize("value", ["", " \n\t", "x" * 161, None, 1, True])
def test_FR_QRY_002_bad_query_text(value):
    with pytest.raises((ValueError, TypeError)):
        domain.normalize_query(value)


@pytest.mark.parametrize("value", ["x", "x" * 160, " \n" + "x" * 160 + " \n"])
def test_FR_QRY_002_exact_bounds(value):
    assert len(domain.normalize_query(value)) in {1, 160}


@pytest.mark.parametrize("value", [-1, True, "0", 0.0, None])
def test_FR_QRY_003_007_strict_revisions(value):
    with pytest.raises(ValidationError):
        domain.QueryAddInput(text="A query", expectedRevision=value)


@pytest.mark.parametrize("value", [1, "false", None])
def test_FR_QRY_003_strict_enabled(value):
    with pytest.raises(ValidationError):
        domain.QueryAddInput(text="A query", expectedRevision=0, enabled=value)


def test_FR_QRY_003_defaults_normalization_and_extra_fields():
    query = domain.QueryAddInput(text=" AI\n tutoring ", expectedRevision=0)
    assert query.enabled is True and query.text == "AI tutoring"
    with pytest.raises(ValidationError):
        domain.QueryAddInput(text="Query", expectedRevision=0, origin="generated")


@pytest.mark.parametrize("values", [{}, {"text": None}, {"enabled": None}, {"enabled": 1}])
def test_FR_QRY_003_patch_requires_real_supplied_change(values):
    with pytest.raises(ValidationError):
        domain.QueryPatchInput(expectedRevision=0, **values)


@pytest.mark.parametrize("queries", [[], ["one", "two"], [str(i) for i in range(7)],
    ["AI", "ai", "Education"], ["Straße", "STRASSE", "Education"],
    ["one", "two", "  "], ["one", "two", "x" * 161]])
def test_FR_QRY_001_002_batch_rejected_as_whole(queries):
    with pytest.raises(ValidationError):
        domain.SuggestionBatch(queries=queries)


def test_FR_QRY_001_batch_normalized_without_paper_fields():
    batch = domain.SuggestionBatch(queries=[" AI\n tutors ", "education", "learning"])
    assert batch.queries == ["AI tutors", "education", "learning"]
    with pytest.raises(ValidationError):
        domain.SuggestionBatch(queries=batch.queries, papers=[])


@pytest.mark.parametrize("context_revision,generated,expected", [
    (0, None, False), (1, None, True), (1, 0, True), (1, 1, False), (2, 1, True),
])
def test_FR_QRY_009_durable_notice(context_revision, generated, expected):
    assert domain.refresh_required(context_revision, generated) is expected


def test_FR_QRY_006_exact_enabled_selection():
    queries = [{"text": "Disabled", "enabled": False, "slot": 1},
               {"text": "Second", "enabled": True, "slot": 3},
               {"text": "First", "enabled": True, "slot": 2}]
    assert domain.enabled_texts(queries) == ["First", "Second"]


def test_FR_QRY_006_empty_selection_rejected():
    with pytest.raises(ValueError):
        domain.enabled_texts([])


def test_FR_QRY_004_sticky_ownership_and_noop():
    query = {"text": "Original", "enabled": True, "user_owned": False}
    assert domain.becomes_owned(query, text="Original", enabled=True) is False
    assert domain.becomes_owned(query, enabled=False) is True
    assert domain.becomes_owned(query, text="Edited") is True
    query["user_owned"] = True
    assert domain.becomes_owned(query, text="Original", enabled=True) is True


def test_FR_QRY_004_008_merge_preserves_owned_and_orders_free_slots():
    owned = {"text": "Straße", "normalized_key": "strasse", "slot": 2,
             "user_owned": True, "enabled": False}
    generated = {"text": "Old", "normalized_key": "old", "slot": 1,
                 "user_owned": False, "enabled": True}
    plan = domain.merge_plan([generated, owned], domain.SuggestionBatch(
        queries=["STRASSE", "First new", "Second new"]))
    assert plan["preserved"] == [owned]
    assert plan["additions"] == [{"text": "First new", "slot": 1},
                                 {"text": "Second new", "slot": 3}]
    assert plan["duplicateSkippedCount"] == 1 and plan["replacedCount"] == 1


def test_FR_QRY_008_full_owned_capacity_allows_zero_additions():
    queries = [{"text": f"Saved {i}", "normalized_key": f"saved {i}", "slot": i + 1,
                "user_owned": True, "enabled": False} for i in range(20)]
    plan = domain.merge_plan(queries, domain.SuggestionBatch(queries=["New1", "New2", "New3"]))
    assert plan["preserved"] == queries and plan["additions"] == []
    assert plan["capacitySkippedCount"] == 3


@pytest.mark.parametrize("values", [{"inputTokens": -1}, {"outputTokens": True},
                                   {"totalTokens": "10"}, {"durationSeconds": -1},
                                   {"rawResponse": "secret"}])
def test_FR_QRY_001_metadata_strict_and_bounded(values):
    with pytest.raises(ValidationError):
        SuggestionMetadata(model="fake", promptVersion="test", **values)


def test_FR_QRY_007_provider_context_is_immutable():
    from dataclasses import FrozenInstanceError

    snapshot = SuggestionContext(question="Question", keywords=("AI",))
    with pytest.raises(FrozenInstanceError):
        snapshot.question = "Overwritten"
