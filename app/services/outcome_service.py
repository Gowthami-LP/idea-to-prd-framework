from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.outcomes import (
    MeasurementCreate,
    MetricCreate,
    OutcomeDecisionCreate,
)


def calculate_metric_achievement(
    baseline: float | None,
    target: float | None,
    actual: float | None,
    direction: str = "HIGHER_IS_BETTER",
) -> dict:
    if baseline is None or target is None or actual is None:
        return {"status": "INSUFFICIENT_DATA", "achievement": None}
    if direction == "HIGHER_IS_BETTER":
        improvement_needed = target - baseline
        already_met = actual >= target
    elif direction == "LOWER_IS_BETTER":
        improvement_needed = baseline - target
        already_met = actual <= target
    else:
        raise ValueError("Direction must be HIGHER_IS_BETTER or LOWER_IS_BETTER")
    if improvement_needed == 0:
        return {
            "status": "TARGET_ALREADY_MET",
            "achievement": 100.0 if already_met else 0.0,
        }
    improvement = (
        actual - baseline
        if direction == "HIGHER_IS_BETTER"
        else baseline - actual
    )
    return {
        "status": "MEASURED",
        "achievement": round((improvement / improvement_needed) * 100, 2),
    }


def _ensure_project(db: Database, project_id: str) -> None:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")


def create_metric(db: Database, project_id: str, data: MetricCreate) -> dict:
    _ensure_project(db, project_id)
    if data.direction not in {"HIGHER_IS_BETTER", "LOWER_IS_BETTER"}:
        raise ValueError("Invalid metric direction")
    metric = {
        "metric_id": f"MET-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    db["metrics"].insert_one(metric)
    metric.pop("_id", None)
    return metric


def get_metrics(db: Database, project_id: str) -> list[dict]:
    _ensure_project(db, project_id)
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["metrics"].find({"project_id": project_id})
    ]


def create_measurement(
    db: Database,
    project_id: str,
    data: MeasurementCreate,
) -> dict:
    _ensure_project(db, project_id)
    metric = db["metrics"].find_one(
        {"metric_id": data.metric_id, "project_id": project_id}
    )
    if metric is None:
        raise LookupError("Metric not found for project")
    achievement = calculate_metric_achievement(
        metric.get("baseline"),
        metric.get("target"),
        data.actual,
        metric["direction"],
    )
    measurement = {
        "measurement_id": f"MEAS-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        **achievement,
        "measured_at": datetime.now(timezone.utc),
    }
    db["measurements"].insert_one(measurement)
    measurement.pop("_id", None)
    return measurement


def get_outcome_report(db: Database, project_id: str) -> dict:
    _ensure_project(db, project_id)
    metrics = list(db["metrics"].find({"project_id": project_id}))
    measurements = list(db["measurements"].find({"project_id": project_id}))
    latest = {}
    for measurement in measurements:
        previous = latest.get(measurement["metric_id"])
        if previous is None or measurement["measured_at"] > previous["measured_at"]:
            latest[measurement["metric_id"]] = measurement
    report = []
    for metric in metrics:
        current = latest.get(metric["metric_id"])
        report.append(
            {
                **{key: value for key, value in metric.items() if key != "_id"},
                "latest_measurement": (
                    {key: value for key, value in current.items() if key != "_id"}
                    if current else None
                ),
            }
        )
    return {"project_id": project_id, "metrics": report}


def record_outcome_decision(
    db: Database,
    project_id: str,
    data: OutcomeDecisionCreate,
) -> dict:
    _ensure_project(db, project_id)
    if data.decision not in {"CONTINUE", "CHANGE", "STOP"}:
        raise ValueError("Decision must be CONTINUE, CHANGE, or STOP")
    decision = {
        "decision_id": f"OUT-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    db["outcome_decisions"].insert_one(decision)
    decision.pop("_id", None)
    return decision
