from fastapi import FastAPI

from app.api import api_router
from app.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="""
SignedShot API provides cryptographic proof of authenticity for photos and videos.

## Overview

The API enables devices to register and obtain trust tokens that certify when and where media was captured.

## Flow

1. **Register a device** - Get a device token for authentication
2. **Create a capture session** - Get a one-time nonce before capturing media
3. **Exchange nonce for trust token** - Get a signed JWT proving capture authenticity
""",
    openapi_tags=[
        {
            "name": "devices",
            "description": "Device registration and management",
        },
        {
            "name": "capture",
            "description": "Capture sessions and trust token generation",
        },
        {
            "name": "health",
            "description": "Health check endpoints",
        },
    ],
)

app.include_router(api_router)
