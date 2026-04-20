import pytest
from api.utils import require_data
from fastapi import HTTPException


class MockResponse:
    """Mock Supabase response object."""
    def __init__(self, data):
        self.data = data


class TestRequireData:
    """Tests for require_data utility function."""

    def test_valid_data_returns_first_item(self):
        """Test that valid list data returns first item."""
        response = MockResponse([{"id": "123", "name": "test"}])
        result = require_data(response, "Not found")
        assert result == {"id": "123", "name": "test"}

    def test_empty_list_raises_404(self):
        """Test that empty list raises 404."""
        response = MockResponse([])
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404

    def test_none_raises_404(self):
        """Test that None data raises 404."""
        response = MockResponse(None)
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404

    def test_dict_raises_404(self):
        """Test that dict (error response) raises 404."""
        response = MockResponse({"error": "Something went wrong"})
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404

    def test_missing_data_attribute_raises_500(self):
        """Test that missing .data attribute raises 500."""
        response = object()  # No .data attribute
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 500

    def test_custom_error_message(self):
        """Test that custom error message is used."""
        response = MockResponse(None)
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Custom error message")
        assert exc_info.value.detail == "Custom error message"

    def test_single_item_list(self):
        """Test list with single item returns that item."""
        response = MockResponse([{"id": "1"}])
        result = require_data(response)
        assert result == {"id": "1"}

    def test_multiple_items_returns_first(self):
        """Test that list with multiple items returns first."""
        response = MockResponse([{"id": "1"}, {"id": "2"}, {"id": "3"}])
        result = require_data(response)
        assert result == {"id": "1"}
