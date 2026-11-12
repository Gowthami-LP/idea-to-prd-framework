import pytest
from pydantic import ValidationError

from app.schemas.outcomes import MetricCreate, OutcomeDecisionCreate


@pytest.mark.parametrize("direction", ["HIGHER_IS_BETTER", "LOWER_IS_BETTER"])
def test_metric_create_accepts_supported_directions(direction):
    metric = MetricCreate(name="Conversion rate", direction=direction)

    assert metric.direction == direction


def test_metric_create_rejects_unsupported_direction():
    with pytest.raises(ValidationError):
        MetricCreate(name="Conversion rate", direction="NEUTRAL")


@pytest.mark.parametrize("decision", ["CONTINUE", "CHANGE", "STOP"])
def test_outcome_decision_accepts_supported_decisions(decision):
    outcome = OutcomeDecisionCreate(
        decision=decision,
        rationale="Decision rationale.",
        decided_by="product-owner",
    )

    assert outcome.decision == decision


def test_outcome_decision_rejects_unsupported_decision():
    with pytest.raises(ValidationError):
        OutcomeDecisionCreate(
            decision="PAUSE",
            rationale="Decision rationale.",
            decided_by="product-owner",
        )
