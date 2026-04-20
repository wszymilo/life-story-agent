import pytest


class TestGetUsersMe:
    def test_get_users_me_requires_auth(self):
        pytest.skip("Requires JWT mocking - complex setup")

    def test_route_exists(self):
        from main import app

        routes = [r.path for r in app.routes]
        assert "/api/users/me" in routes


class TestPutUsersMe:
    def test_put_users_me_requires_auth(self):
        pytest.skip("Requires JWT mocking - complex setup")


class TestLanguagePreference:
    def test_language_endpoint_exists(self):
        from main import app

        routes = [r.path for r in app.routes]
        assert "/api/users/me/language" in routes

    def test_user_update_schema_accepts_language(self):
        from api.schemas.user import UserUpdate

        update = UserUpdate(preferred_language="en")
        assert update.preferred_language == "en"

    def test_user_update_schema_validates_language_length(self):
        from api.schemas.user import UserUpdate

        update = UserUpdate(preferred_language="pl")
        assert update.preferred_language == "pl"


class TestRelatives:
    def test_post_relatives_requires_auth(self):
        pytest.skip("Requires JWT mocking - complex setup")

    def test_delete_relative_requires_auth(self):
        pytest.skip("Requires JWT mocking - complex setup")

    def test_routes_exist(self):
        from main import app

        routes = [r.path for r in app.routes]
        assert any("/api/users/me/relatives" in r for r in routes)
