import secrets
from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from canciones.adapters.db.repository import CancionesRepository
from canciones.adapters.db.session import get_session
from canciones.config import settings


def require_access_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> None:
    """Exige la llave compartida en todas las rutas de /api/v1.

    Acepta ``Authorization: Bearer <llave>`` o ``X-Api-Key: <llave>``. Si
    ``ACCESS_KEY`` está vacío (desarrollo local) la autenticación queda
    desactivada.
    """
    if not settings.access_key:
        return

    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_api_key:
        token = x_api_key.strip()

    if not token or not secrets.compare_digest(token, settings.access_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Llave de acceso incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
