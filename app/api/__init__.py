"""API routes."""

from fastapi import APIRouter

from app.api.routes import device, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(device.router)
