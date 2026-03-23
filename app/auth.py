from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.persistence import SQLiteUserStore, UserRecord


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


@dataclass(frozen=True)
class AuthUser:
    username: str


class AuthService:
    def __init__(self, user_store: SQLiteUserStore, secret_key: str, token_ttl_hours: int = 24) -> None:
        self.user_store = user_store
        self.secret_key = secret_key.encode("utf-8")
        self.token_ttl_hours = token_ttl_hours

    def register_user(self, username: str, password: str) -> AuthUser:
        normalized = self._normalize_username(username)
        if self.user_store.get_user(normalized) is not None:
            raise ValueError("Username already exists.")
        password_hash = self._hash_password(password)
        self.user_store.create_user(normalized, password_hash)
        return AuthUser(username=normalized)

    def login_user(self, username: str, password: str) -> tuple[AuthUser, str]:
        normalized = self._normalize_username(username)
        user = self.user_store.get_user(normalized)
        if user is None or not self._verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password.")
        return AuthUser(username=user.username), self._issue_token(user)

    def authenticate_token(self, token: str) -> AuthUser:
        try:
            username, expiry, signature = token.split(".", 2)
            payload = f"{username}.{expiry}".encode("utf-8")
            expected = _b64encode(hmac.new(self.secret_key, payload, hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise ValueError
            if datetime.now(UTC) > datetime.fromtimestamp(int(expiry), tz=UTC):
                raise ValueError
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid or expired token.") from exc

        user = self.user_store.get_user(_b64decode(username).decode("utf-8"))
        if user is None:
            raise ValueError("Invalid or expired token.")
        return AuthUser(username=user.username)

    def _issue_token(self, user: UserRecord) -> str:
        expiry = int((datetime.now(UTC) + timedelta(hours=self.token_ttl_hours)).timestamp())
        username = _b64encode(user.username.encode("utf-8"))
        payload = f"{username}.{expiry}".encode("utf-8")
        signature = _b64encode(hmac.new(self.secret_key, payload, hashlib.sha256).digest())
        return f"{username}.{expiry}.{signature}"

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return f"{_b64encode(salt)}:{_b64encode(digest)}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt_value, digest_value = stored_hash.split(":", 1)
            salt = _b64decode(salt_value)
            expected = _b64decode(digest_value)
        except ValueError:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)

    def _normalize_username(self, username: str) -> str:
        normalized = username.strip()
        if len(normalized) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return normalized
