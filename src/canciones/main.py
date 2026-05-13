from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from canciones.adapters.db.session import create_tables
from canciones.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(
    title="Canciones Mas Escuchadas API",
    description="API personal para consultar las canciones mas escuchadas en YouTube y Spotify",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
