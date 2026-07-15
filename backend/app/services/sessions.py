"""管理员、工作人员与嘉宾统一登录会话业务服务。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_access_token, hash_access_token, verify_password
from app.models.auth import AuthSession
from app.models.guest import Guest
from app.models.user import User


def normalize_datetime(value: datetime) -> datetime:
    """将数据库返回的时间统一为带 UTC 时区的 datetime。

    入参：value 为数据库时间，必填。
    返回值：datetime：带时区时间；SQLite 返回无时区值时按 UTC 解释。
    异常：当前函数不主动抛出业务异常。
    """
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def authenticate_user(db: Session, username: str, password: str, role: str) -> User | None:
    """按账号、密码、角色和启用状态认证管理员或工作人员。

    入参：db 为数据库会话；username、password 为登录凭据；role 为 admin 或 staff，均必填。
    返回值：User | None：认证成功时返回用户，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    user = db.scalar(select(User).where(User.username == username, User.role == role, User.is_active.is_(True)))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_user_session(db: Session, user: User) -> tuple[str, AuthSession]:
    """为管理员或工作人员创建可撤销会话。

    入参：db 为数据库会话；user 为已认证用户，均必填。
    返回值：tuple[str, AuthSession]：原始访问 token 与已持久化会话。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    token = generate_access_token()
    auth_session = AuthSession(
        token_hash=hash_access_token(token),
        subject_type=user.role,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours),
    )
    db.add(auth_session)
    db.commit()
    db.refresh(auth_session)
    return token, auth_session


def create_guest_session(db: Session, guest: Guest) -> tuple[str, AuthSession]:
    """为已完成姓名和手机号校验的嘉宾创建可撤销会话。

    入参：db 为数据库会话；guest 为已认证嘉宾，均必填。
    返回值：tuple[str, AuthSession]：原始访问 token 与已持久化会话。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    token = generate_access_token()
    auth_session = AuthSession(
        token_hash=hash_access_token(token),
        subject_type="guest",
        guest_id=guest.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours),
    )
    db.add(auth_session)
    db.commit()
    db.refresh(auth_session)
    return token, auth_session


def get_active_session(db: Session, token: str) -> AuthSession | None:
    """读取未撤销且未过期的访问会话。

    入参：db 为数据库会话；token 为客户端 Bearer token，均必填。
    返回值：AuthSession | None：有效会话存在时返回对象，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    auth_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_access_token(token)))
    if auth_session is None or auth_session.revoked_at is not None:
        return None
    if normalize_datetime(auth_session.expires_at) <= datetime.now(timezone.utc):
        return None
    return auth_session


def revoke_session(db: Session, auth_session: AuthSession) -> None:
    """立即撤销指定登录会话。

    入参：db 为数据库会话；auth_session 为当前有效会话，均必填。
    返回值：None：提交后该 token 不再可用。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    auth_session.revoked_at = datetime.now(timezone.utc)
    db.commit()
