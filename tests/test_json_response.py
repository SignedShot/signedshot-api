"""Tests for custom JSON response formatting."""

import json
from datetime import UTC, datetime

from app.main import CustomJSONEncoder, CustomJSONResponse


class TestCustomJSONEncoder:
    """Tests for CustomJSONEncoder datetime formatting."""

    def test_datetime_without_microseconds(self) -> None:
        """Datetime should be formatted without microseconds."""
        dt = datetime(2026, 1, 25, 12, 30, 45, 123456, tzinfo=UTC)
        result = json.dumps({"created_at": dt}, cls=CustomJSONEncoder)
        assert result == '{"created_at": "2026-01-25T12:30:45Z"}'

    def test_datetime_already_without_microseconds(self) -> None:
        """Datetime without microseconds should still work."""
        dt = datetime(2026, 1, 25, 12, 30, 45, tzinfo=UTC)
        result = json.dumps({"created_at": dt}, cls=CustomJSONEncoder)
        assert result == '{"created_at": "2026-01-25T12:30:45Z"}'

    def test_non_datetime_passthrough(self) -> None:
        """Non-datetime values should pass through normally."""
        data = {"name": "test", "count": 42, "active": True}
        result = json.dumps(data, cls=CustomJSONEncoder)
        assert json.loads(result) == data


class TestCustomJSONResponse:
    """Tests for CustomJSONResponse."""

    def test_response_datetime_format(self) -> None:
        """Response should format datetime without microseconds."""
        dt = datetime(2026, 1, 25, 12, 30, 45, 999999, tzinfo=UTC)
        response = CustomJSONResponse(content={"expires_at": dt})
        body = json.loads(response.body.decode())
        assert body["expires_at"] == "2026-01-25T12:30:45Z"

    def test_response_nested_datetime(self) -> None:
        """Nested datetime should also be formatted correctly."""
        dt = datetime(2026, 1, 25, 12, 30, 45, 123456, tzinfo=UTC)
        response = CustomJSONResponse(
            content={"data": {"timestamp": dt, "value": "test"}}
        )
        body = json.loads(response.body.decode())
        assert body["data"]["timestamp"] == "2026-01-25T12:30:45Z"
