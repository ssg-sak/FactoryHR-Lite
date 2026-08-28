from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.services.password_service import hash_password


def _upsert_user(
    session: Session, *, username: str, password: str, role: str
) -> User:
    user = session.scalar(select(User).where(User.username == username))
    password_hash = hash_password(password)
    if user is None:
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        session.add(user)
        return user
    user.password_hash = password_hash
    user.role = role
    user.is_active = True
    return user


def bootstrap_managed_accounts(session: Session) -> list[str]:
    created: list[str] = []
    admin_username = settings.bootstrap_admin_username.strip()
    admin_password = settings.bootstrap_admin_password
    if admin_username and admin_password:
        _upsert_user(
            session,
            username=admin_username,
            password=admin_password,
            role=UserRole.ADMIN.value,
        )
        created.append(f"admin:{admin_username}")
    else:
        print("Admin account skipped: BOOTSTRAP_ADMIN_PASSWORD is not set.")

    viewer_username = settings.demo_viewer_username.strip()
    viewer_password = settings.demo_viewer_password
    if viewer_username and viewer_password:
        _upsert_user(
            session,
            username=viewer_username,
            password=viewer_password,
            role=UserRole.VIEWER.value,
        )
        created.append(f"viewer:{viewer_username}")
    else:
        print("Demo viewer skipped: DEMO_VIEWER_PASSWORD is not set.")
    return created
