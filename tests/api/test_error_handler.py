"""Test error handler middleware with real exception scenarios"""

from unittest.mock import Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from nedc_bench.api.middleware.error_handler import (
    NEDCAPIError,
    error_handler_middleware,
)


class TestErrorHandlerMiddleware:
    """Test error handling middleware paths"""

    @pytest.fixture
    def mock_request(self):
        """Create mock request with headers"""
        request = Mock(spec=Request)
        request.headers = {"X-Request-ID": "test-123"}
        return request

    @pytest.mark.asyncio
    async def test_nedc_api_error_handling(self, mock_request):
        """Test handling of custom NEDCAPIError"""

        # Create a call_next that raises NEDCAPIError
        async def failing_handler(request):
            raise NEDCAPIError(
                status_code=400, detail="Invalid file format", error_code="INVALID_FORMAT"
            )

        response = await error_handler_middleware(mock_request, failing_handler)

        # Should return JSON response with error details
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

        # Check response content
        body = response.body.decode()
        assert "INVALID_FORMAT" in body
        assert "Invalid file format" in body
        assert "test-123" in body  # Request ID

    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, mock_request):
        """Test handling of unexpected exceptions"""

        # Create a call_next that raises unexpected error
        async def crashing_handler(request):
            raise RuntimeError("Unexpected database error")

        with patch("nedc_bench.api.middleware.error_handler.logger") as mock_logger:
            response = await error_handler_middleware(mock_request, crashing_handler)

            # Should log the error with format string and exception as arg
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0]
            assert call_args[0].startswith("Unexpected error")
            # Second arg is the exception instance
            assert "Unexpected database error" in str(call_args[1])

        # Should return 500 response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # Check generic error message
        body = response.body.decode()
        assert "INTERNAL_SERVER_ERROR" in body
        assert "An unexpected error occurred" in body
        assert "test-123" in body  # Request ID

    @pytest.mark.asyncio
    async def test_successful_request_passthrough(self, mock_request):
        """Test middleware passes through successful requests"""
        # Create a successful handler
        expected_response = JSONResponse({"status": "ok"})

        async def success_handler(request):
            return expected_response

        response = await error_handler_middleware(mock_request, success_handler)

        # Should return the original response
        assert response is expected_response

    @pytest.mark.asyncio
    async def test_missing_request_id(self):
        """Test handling when X-Request-ID is missing"""
        # Request without X-Request-ID header
        request = Mock(spec=Request)
        request.headers = {}

        async def failing_handler(request):
            raise NEDCAPIError(404, "Not found", "NOT_FOUND")

        response = await error_handler_middleware(request, failing_handler)

        # Should handle gracefully with None request_id
        body = response.body.decode()
        assert "null" in body  # JSON null for None

    @pytest.mark.asyncio
    async def test_nedc_api_error_properties(self):
        """Test NEDCAPIError exception properties"""
        error = NEDCAPIError(
            status_code=422, detail="Validation failed", error_code="VALIDATION_ERROR"
        )

        assert error.status_code == 422
        assert error.detail == "Validation failed"
        assert error.error_code == "VALIDATION_ERROR"
        assert str(error) == "Validation failed"

    @pytest.mark.asyncio
    async def test_logging_levels(self, mock_request):
        """Test appropriate logging levels for different errors"""
        with patch("nedc_bench.api.middleware.error_handler.logger") as mock_logger:
            # NEDCAPIError should use warning level
            async def api_error_handler(request):
                raise NEDCAPIError(400, "Bad request", "BAD_REQUEST")

            await error_handler_middleware(mock_request, api_error_handler)
            mock_logger.warning.assert_called_once()
            fmt, code, detail = mock_logger.warning.call_args[0]
            assert fmt.startswith("API error")
            assert code == "BAD_REQUEST"
            assert detail == "Bad request"

            # Reset mock
            mock_logger.reset_mock()

            # Unexpected errors should use error level
            async def unexpected_handler(request):
                raise ValueError("Unexpected value")

            await error_handler_middleware(mock_request, unexpected_handler)
            mock_logger.error.assert_called_once()
            assert mock_logger.error.call_args[0][0].startswith("Unexpected error")

    @pytest.mark.asyncio
    async def test_error_with_special_characters(self, mock_request):
        """Test error messages with special characters are handled correctly"""

        async def handler(request):
            raise NEDCAPIError(
                400, 'File name contains invalid characters: <>&"', "INVALID_FILENAME"
            )

        response = await error_handler_middleware(mock_request, handler)

        # Should properly escape special characters in JSON
        body = response.body.decode()
        assert "INVALID_FILENAME" in body
        # JSON should escape the characters properly
        assert "invalid characters" in body
