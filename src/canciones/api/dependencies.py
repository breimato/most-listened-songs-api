from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from canciones.adapters.db.repository import CancionesRepository
from canciones.adapters.db.session import get_session


def get_repository(
    session: Session = Depends(get_session),
) -> Generator[CancionesRepository, None, None]:
    repo = CancionesRepository(session)
    try:
        yield repo
        session.commit()
    except Exception:
        session.rollback()
        raise
