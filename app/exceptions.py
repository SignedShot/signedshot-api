"""Domain exceptions for the application.

These exceptions represent business logic errors and are converted
to HTTP responses by FastAPI exception handlers.
"""


class DomainException(Exception):
    """Base class for all domain exceptions."""

    pass


class EntityAlreadyExistsError(DomainException):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} '{identifier}' already exists")


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} '{identifier}' not found")


class InvalidCredentialsError(DomainException):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message)


class InvalidNonceError(DomainException):
    """Raised when a nonce is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired nonce") -> None:
        super().__init__(message)


class AppCheckError(DomainException):
    """Raised when Firebase App Check verification fails."""

    def __init__(self, message: str = "App Check verification failed") -> None:
        super().__init__(message)
