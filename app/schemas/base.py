from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

# Custom datetime type that serializes without microseconds
APIDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        return_type=str,
    ),
]


class APIResponse(BaseModel):
    """Base model for API responses. Use APIDatetime for datetime fields."""

    pass
