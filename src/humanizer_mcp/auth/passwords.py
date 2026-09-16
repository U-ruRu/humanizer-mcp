import base64
import hashlib
import hmac
import secrets

_N = 1 << 15
_R = 8
_P = 1
_DKLEN = 32
_SALT_BYTES = 16
_MAXMEM = 64 * 1024 * 1024
_PREFIX = "scrypt"


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(value: str) -> str:
    if not value:
        raise ValueError("credential value must be non-empty")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        value.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN, maxmem=_MAXMEM
    )
    return f"{_PREFIX}${_N}${_R}${_P}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(value: str, encoded: str) -> bool:
    if not value or not encoded:
        return False
    if not encoded.startswith(f"{_PREFIX}$"):
        return hmac.compare_digest(value, encoded)
    try:
        prefix, raw_n, raw_r, raw_p, raw_salt, raw_digest = encoded.split("$", 5)
        if prefix != _PREFIX:
            return False
        n, r, p = int(raw_n), int(raw_r), int(raw_p)
        if (n, r, p) != (_N, _R, _P):
            return False
        salt = _b64decode(raw_salt)
        expected = _b64decode(raw_digest)
        actual = hashlib.scrypt(
            value.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=len(expected), maxmem=_MAXMEM
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
