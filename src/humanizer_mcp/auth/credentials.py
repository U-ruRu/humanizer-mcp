import hmac
from datetime import UTC, datetime


class CredentialManager:
    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def _active(item: dict) -> bool:
        value = item.get("expires_at", "")
        if not value:
            return True
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed > datetime.now(UTC)
        except ValueError:
            return False

    def bearer_valid(self, token: str) -> bool:
        legacy = [x.strip() for x in self.settings.bearer_tokens.split(",") if x.strip()]
        items = self.settings.parse_json_list(self.settings.bearer_credentials_json)
        values = legacy + [x.get("token", "") for x in items if self._active(x)]
        return any(hmac.compare_digest(token, value) for value in values if value)

    def oauth_user_valid(self, username: str, password: str) -> bool:
        users = self.settings.parse_json_list(self.settings.oauth_users_json)
        if not users:
            return hmac.compare_digest(
                username, self.settings.oauth_admin_username
            ) and hmac.compare_digest(password, self.settings.oauth_admin_password)
        return any(
            self._active(item)
            and hmac.compare_digest(username, item.get("username", ""))
            and hmac.compare_digest(password, item.get("password", ""))
            for item in users
        )
