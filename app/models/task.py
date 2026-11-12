from app.schemas.planning import TaskCreate


class Task(TaskCreate):
    task_id: str
    status: str = "BACKLOG"
