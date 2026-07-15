"""API 路由共用数据库与安全会话依赖。"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import AuthSession
from app.models.guest import Guest
from app.models.user import User
from app.services.sessions import get_active_session

DatabaseSession = Annotated[Session, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_auth_session(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthSession:
    """校验 Authorization Bearer token 并返回有效服务端会话。

    入参：db 为当前数据库会话；credentials 为 FastAPI 解析的 Bearer 凭证。
    返回值：AuthSession：存在、未撤销且未过期的服务端会话。
    异常：缺少凭证、凭证类型错误或会话无效时抛出 401。
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少有效的登录凭证。")
    auth_session = get_active_session(db, credentials.credentials)
    if auth_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录凭证无效或已过期。")
    return auth_session


CurrentAuthSession = Annotated[AuthSession, Depends(get_current_auth_session)]


def get_current_admin(db: DatabaseSession, auth_session: CurrentAuthSession) -> User:
    """从安全会话读取并验证管理员账号。

    入参：db 为数据库会话；auth_session 为已验证服务端会话。
    返回值：User：已启用且角色为 admin 的管理员。
    异常：会话主体不是有效管理员时抛出 403。
    """
    user = db.get(User, auth_session.user_id) if auth_session.subject_type == "admin" else None
    if user is None or not user.is_active or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前会话没有管理员权限。")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


def get_current_staff(db: DatabaseSession, auth_session: CurrentAuthSession) -> User:
    """从安全会话读取并验证工作人员账号。

    入参：db 为数据库会话；auth_session 为已验证服务端会话。
    返回值：User：已启用且角色为 staff 的工作人员。
    异常：会话主体不是有效工作人员时抛出 403。
    """
    user = db.get(User, auth_session.user_id) if auth_session.subject_type == "staff" else None
    if user is None or not user.is_active or user.role != "staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前会话没有工作人员权限。")
    return user


CurrentStaff = Annotated[User, Depends(get_current_staff)]


def get_current_guest(db: DatabaseSession, auth_session: CurrentAuthSession) -> Guest:
    """从安全会话读取并验证嘉宾。

    入参：db 为数据库会话；auth_session 为已验证服务端会话。
    返回值：Guest：已启用的嘉宾对象。
    异常：会话主体不是有效嘉宾时抛出 403。
    """
    guest = db.get(Guest, auth_session.guest_id) if auth_session.subject_type == "guest" else None
    if guest is None or not guest.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前会话没有嘉宾权限。")
    return guest


CurrentGuest = Annotated[Guest, Depends(get_current_guest)]
