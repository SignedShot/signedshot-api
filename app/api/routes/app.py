from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.app import AppRegisterRequest, AppRegisterResponse
from app.services.app import AppAlreadyExistsError, app_service

router = APIRouter(prefix="/apps", tags=["apps"])


@router.post(
    "/register",
    response_model=AppRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "App already registered"},
    },
)
async def register_app(
    request: AppRegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> AppRegisterResponse:
    """
    Register a new application.

    Returns app details including the app_id needed for capture sessions.
    """
    try:
        app = await app_service.register(
            session,
            name=request.name,
            firebase_project_id=request.firebase_project_id,
            track_devices=request.track_devices,
        )
    except AppAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None

    return AppRegisterResponse(
        app_id=str(app.id),
        name=app.name,
        firebase_project_id=app.firebase_project_id,
        track_devices=app.track_devices,
        sandbox=app.sandbox,
        created_at=app.created_at,
    )
