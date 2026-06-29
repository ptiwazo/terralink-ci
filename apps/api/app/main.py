"""Point d'entrée de l'API TerraLink CI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.bootstrap import seed_admin
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée le compte admin initial si configuré (et absent). Idempotent.
    seed_admin()
    yield


app = FastAPI(
    title="TerraLink CI — API",
    version="0.1.0",
    description="Place de marché B2B agricole (Côte d'Ivoire).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
