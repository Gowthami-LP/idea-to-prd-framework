from app.schemas.release import ReleaseCreate


class Release(ReleaseCreate):
    release_id: str
