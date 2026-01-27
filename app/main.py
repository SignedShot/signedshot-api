import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidCredentialsError,
    InvalidNonceError,
)
from app.settings import settings


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that formats datetimes without microseconds."""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%SZ")
        return super().default(o)


class CustomJSONResponse(JSONResponse):
    """JSON response that uses custom datetime formatting."""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder,
        ).encode("utf-8")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    default_response_class=CustomJSONResponse,
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

# CORS configuration
cors_origins = ["https://signedshot.io"]
if settings.debug:
    cors_origins.extend([
        "http://localhost:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if settings.debug else None,
    allow_methods=["*"],
    allow_headers=["*"],
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
