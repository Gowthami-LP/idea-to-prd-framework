from app.schemas.outcomes import MetricCreate


class Metric(MetricCreate):
    metric_id: str
    project_id: str
