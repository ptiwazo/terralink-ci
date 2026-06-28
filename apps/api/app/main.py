"""Point d'entrée de l'API TerraLink CI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="TerraLink CI — API",
    version="0.1.0",
    description="Place de marché B2B agricole (Côte d'Ivoire). Phase 0.",
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
