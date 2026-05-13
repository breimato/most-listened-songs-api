from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from canciones.adapters.db.repository import SQLiteRepository
from canciones.adapters.db.session import get_session


def get_repository(
    session: Session = Depends(get_session),
) -> Generator[SQLiteRepository, None, None]:
    repo = SQLiteRepository(session)
    try:
        yield repo
        session.commit()
    except Exception:
        session.rollback()
        raise
