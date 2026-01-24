from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidCredentialsError,
    InvalidNonceError,
)
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


@app.exception_handler(EntityAlreadyExistsError)
async def entity_already_exists_handler(
    _: Request, exc: EntityAlreadyExistsError
) -> JSONResponse:
    """Handle duplicate entity errors."""
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    _: Request, exc: EntityNotFoundError
) -> JSONResponse:
    """Handle entity not found errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    _: Request, exc: InvalidCredentialsError
) -> JSONResponse:
    """Handle invalid credentials errors."""
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidNonceError)
async def invalid_nonce_handler(_: Request, exc: InvalidNonceError) -> JSONResponse:
    """Handle invalid nonce errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
