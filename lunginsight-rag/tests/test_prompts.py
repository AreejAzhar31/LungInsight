"""Tests for agent/prompts.py — specifically build_prediction_context_block,
which was fixed after a real bug: the model was answering "what's my linked
prediction?" generically instead of stating the actual label/confidence,
because the system prompt never explicitly permitted stating those values
directly (they aren't a retrieved/citable knowledge-base fact)."""

from agent.prompts import build_prediction_context_block, SYSTEM_PROMPT


def test_no_context_returns_placeholder():
    assert "no upstream model prediction" in build_prediction_context_block(None)


def test_context_states_label_and_confidence_plainly():
    block = build_prediction_context_block({"predicted_class": "Normal", "confidence": 0.994})
    assert "predicted_class: Normal" in block
    assert "confidence: 99.4%" in block


def test_context_includes_extra_fields_but_not_none_values():
    block = build_prediction_context_block(
        {"predicted_class": "Pneumonia", "confidence": 0.921, "gradcam_region": None}
    )
    assert "predicted_class: Pneumonia" in block
    assert "confidence: 92.1%" in block
    assert "gradcam_region" not in block  # None values omitted, not printed as "None"


def test_system_prompt_explicitly_permits_stating_prediction_context():
    """The actual fix: the model must be told it CAN state predicted_class/
    confidence directly, since rule 1's 'base every claim on RETRIEVED
    CONTEXT' previously left it unclear whether the app's own prediction
    data counted as a fact requiring citation/verification."""
    assert "predicted_class and confidence values are data from THIS app's own model run" in SYSTEM_PROMPT
    assert "my prediction" in SYSTEM_PROMPT
    assert "my result" in SYSTEM_PROMPT


def test_system_prompt_clarifies_citation_rule_excludes_prediction_context():
    assert "does not need a citation" in SYSTEM_PROMPT
