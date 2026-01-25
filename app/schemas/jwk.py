from pydantic import BaseModel


class JWK(BaseModel):
    """JSON Web Key for EC key."""

    kty: str  # Key type, always "EC" for elliptic curve
    crv: str  # Curve, "P-256" for ES256
    x: str  # Base64url-encoded X coordinate
    y: str  # Base64url-encoded Y coordinate
    use: str  # Key usage, "sig" for signature
    alg: str  # Algorithm, "ES256"
    kid: str  # Key ID


class JWKSResponse(BaseModel):
    """JSON Web Key Set response."""

    keys: list[JWK]
