import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUMANIZER_MCP_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8090
    public_base_url: str = "http://127.0.0.1:8090"
    humanizer_root: Path = Path("/opt/humanizer-ru")
    database_path: Path = Path("./data/humanizer-mcp.sqlite3")
    max_text_chars: int = 200_000
    scanner_timeout_sec: float = 20.0

    auth_mode: str = "oauth"
    mcp_auth_mode: str = ""
    bearer_tokens: str = ""
    bearer_credentials_json: str = "[]"
    oauth_users_json: str = "[]"
    oauth_issuer: str = ""
    oauth_audience: str = ""
    oauth_jwks_url: str = ""
    oauth_signing_secret: str = "change-me"
    oauth_required_scopes: str = "humanizer:use"
    oauth_admin_username: str = "admin"
    oauth_admin_password: str = "change-me"
    oauth_access_ttl_sec: int = 900
    oauth_refresh_ttl_sec: int = 2_592_000
    oauth_code_ttl_sec: int = 300

    def mode_for(self, interface: str) -> str:
        if interface == "mcp" and self.mcp_auth_mode:
            return self.mcp_auth_mode
        return self.auth_mode

    @staticmethod
    def parse_json_list(value: str) -> list[dict]:
        try:
            parsed = json.loads(value or "[]")
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
