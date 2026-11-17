from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from canciones.adapters.db.models import Base
from canciones.config import settings

_database_url = settings.sqlalchemy_url
_is_sqlite = _database_url.startswith("sqlite")

engine = create_engine(
    _database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ensure_schema() -> None:
    """Migraciones ligeras para bases de datos ya creadas.

    ``create_all`` no añade columnas a tablas existentes; este paso cubre las
    columnas nuevas que necesita la app (por ahora, la duración de las canciones).
    """
    inspector = inspect(engine)
    if "songs" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("songs")}
    if "duration_seconds" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE songs ADD COLUMN duration_seconds INTEGER")
            )


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
