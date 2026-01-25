from fastapi import APIRouter, Depends

from app.schemas.jwk import JWKSResponse
from app.services.jwk import JWKService, get_jwk_service_singleton

router = APIRouter(tags=["jwks"])


@router.get("/.well-known/jwks.json", response_model=JWKSResponse)
def get_jwks(
    jwk_service: JWKService = Depends(get_jwk_service_singleton),
) -> JWKSResponse:
    """
    JSON Web Key Set endpoint for JWT verification.

    Returns the public keys used to verify JWT tokens issued by this service.
    Validators should fetch this endpoint and use the key matching the `kid`
    from the JWT header to verify signatures.
    """
    return jwk_service.get_jwks()
