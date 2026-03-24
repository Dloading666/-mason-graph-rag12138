"""Local JWT-based authentication service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config.settings import settings
from backend.core.contracts import LoginResponse, UserProfile


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


SEEDED_USERS = {
    "admin": {
        "display_name": "系统管理员",
        "role": "admin",
        "password_hash": pwd_context.hash("Admin@123"),
    },
    "buyer": {
        "display_name": "采购专员",
        "role": "purchase",
        "password_hash": pwd_context.hash("Buyer@123"),
    },
    "staff": {
        "display_name": "建材顾问",
        "role": "normal",
        "password_hash": pwd_context.hash("Staff@123"),
    },
}


class AuthService:
    """Authenticate seeded internal users and issue JWT tokens."""

    def login(self, username: str, password: str) -> LoginResponse:
        user = SEEDED_USERS.get(username)
        if user is None or not pwd_context.verify(password, user["password_hash"]):
            raise ValueError("用户名或密码错误")

        profile = UserProfile(
            username=username,
            display_name=user["display_name"],
            role=user["role"],
        )
        token = self._create_access_token(profile)
        return LoginResponse(access_token=token, user=profile)

    def parse_token(self, token: str) -> UserProfile:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError as exc:
            raise ValueError("登录状态无效，请重新登录") from exc

        return UserProfile(
            username=payload["sub"],
            display_name=payload["display_name"],
            role=payload["role"],
        )

    def _create_access_token(self, profile: UserProfile) -> str:
        expire_at = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": profile.username,
            "display_name": profile.display_name,
            "role": profile.role,
            "exp": expire_at,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
