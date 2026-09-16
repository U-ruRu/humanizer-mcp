from pathlib import Path

from fastapi.testclient import TestClient

from humanizer_mcp.app import create_app
from humanizer_mcp.config import Settings


def test_live_health_is_public(tmp_path: Path):
    settings = Settings(
        auth_mode="none",
        humanizer_root=tmp_path / "missing-humanizer",
        database_path=tmp_path / "oauth.sqlite3",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["application"] == "humanizer-mcp"


def test_oauth_metadata_advertises_humanizer_scope(tmp_path: Path):
    settings = Settings(
        auth_mode="oauth",
        public_base_url="https://humanizer.example.test",
        humanizer_root=tmp_path / "missing-humanizer",
        database_path=tmp_path / "oauth.sqlite3",
        oauth_signing_secret="test-signing-secret",
        oauth_admin_username="tester",
        oauth_admin_password="secret",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    assert response.json()["scopes_supported"] == ["humanizer:use"]
