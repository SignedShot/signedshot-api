from fastapi import FastAPI

from app.api import api_router
from app.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)

app.include_router(api_router)
