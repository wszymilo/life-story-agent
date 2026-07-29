import pytest
from api.utils import require_data
from fastapi import HTTPException


class TestRequireData:
    def test_valid_data_returns_first_item(self):
        result = require_data([{"id": "123", "name": "test"}], "Not found")
        assert result == {"id": "123", "name": "test"}

    def test_empty_list_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            require_data([], "Not found")
        assert exc_info.value.status_code == 404

    def test_none_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            require_data(None, "Not found")
        assert exc_info.value.status_code == 404

    def test_custom_error_message(self):
        with pytest.raises(HTTPException) as exc_info:
            require_data(None, "Custom error message")
        assert exc_info.value.detail == "Custom error message"

    def test_single_item_list(self):
        result = require_data([{"id": "1"}])
        assert result == {"id": "1"}

    def test_multiple_items_returns_first(self):
        result = require_data([{"id": "1"}, {"id": "2"}, {"id": "3"}])
        assert result == {"id": "1"}
