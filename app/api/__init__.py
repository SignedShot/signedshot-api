"""API routes."""

from fastapi import APIRouter

from app.api.routes import capture, device, health, publisher

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(publisher.router)
api_router.include_router(device.router)
api_router.include_router(capture.router)
