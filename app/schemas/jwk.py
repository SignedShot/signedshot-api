from pydantic import BaseModel, Field


class JWK(BaseModel):
    """JSON Web Key for EC key."""

    kty: str = Field(
        description="Key type. Always 'EC' for elliptic curve keys.",
        examples=["EC"],
    )
    crv: str = Field(
        description="Cryptographic curve. 'P-256' for ES256 algorithm.",
        examples=["P-256"],
    )
    x: str = Field(
        description="Base64url-encoded X coordinate of the elliptic curve point.",
    )
    y: str = Field(
        description="Base64url-encoded Y coordinate of the elliptic curve point.",
    )
    use: str = Field(
        description="Key usage. 'sig' indicates this key is used for signatures.",
        examples=["sig"],
    )
    alg: str = Field(
        description="Algorithm. 'ES256' for ECDSA using P-256 and SHA-256.",
        examples=["ES256"],
    )
    kid: str = Field(
        description="Key ID. Unique identifier for this key, used to match JWT headers.",
    )


class JWKSResponse(BaseModel):
    """JSON Web Key Set response for JWT verification."""

    keys: list[JWK] = Field(
        description="List of public keys available for JWT verification.",
    )
