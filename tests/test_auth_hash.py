import json

from humanizer_mcp.auth.credentials import CredentialManager
from humanizer_mcp.auth.passwords import hash_password, verify_password


class Settings:
    oauth_admin_username = "account"
    oauth_users_json = "[]"

    def __init__(self, stored: str):
        self.stored = stored

    def oauth_admin_password_value(self) -> str:
        return self.stored

    @staticmethod
    def parse_json_list(value: str) -> list[dict]:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []


def test_scrypt_roundtrip():
    raw = "sample-value"
    stored = hash_password(raw)
    assert stored.startswith("scrypt$")
    assert verify_password(raw, stored)
    assert not verify_password("other-value", stored)


def test_admin_credential_uses_hash():
    raw = "sample-value"
    credentials = CredentialManager(Settings(hash_password(raw)))
    assert credentials.oauth_user_valid("account", raw)
    assert not credentials.oauth_user_valid("account", "other-value")


def test_user_credential_uses_hash():
    raw = "sample-value"
    settings = Settings("unused")
    settings.oauth_users_json = json.dumps(
        [{"username": "member", "password_hash": hash_password(raw)}]
    )
    credentials = CredentialManager(settings)
    assert credentials.oauth_user_valid("member", raw)
    assert not credentials.oauth_user_valid("member", "other-value")
