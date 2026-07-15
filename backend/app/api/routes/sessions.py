"""管理员、工作人员账号登录与统一退出登录路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAuthSession, DatabaseSession
from app.schemas.session import LogoutResponse, SessionResponse, UserLoginRequest
from app.services.sessions import authenticate_user, create_user_session, revoke_session

router = APIRouter()


def login_user_by_role(payload: UserLoginRequest, db: DatabaseSession, role: str) -> SessionResponse:
    """认证指定角色账号并创建安全会话响应。

    入参：payload 为账号密码；db 为数据库会话；role 为 admin 或 staff。
    返回值：SessionResponse：只在本次响应出现的访问 token、过期时间和主体信息。
    异常：账号、密码、角色或启用状态不匹配时抛出 401。
    """
    user = authenticate_user(db, payload.username, payload.password, role)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误。")
    token, auth_session = create_user_session(db, user)
    return SessionResponse(
        access_token=token,
        expires_at=auth_session.expires_at,
        subject_id=user.id,
        subject_type=user.role,
    )


@router.post("/admin/sessions", response_model=SessionResponse)
def create_admin_session(payload: UserLoginRequest, db: DatabaseSession) -> SessionResponse:
    """使用管理员账号和密码登录。

    入参：payload 为管理员账号密码；db 为数据库会话。
    返回值：SessionResponse：管理员访问会话。
    异常：登录信息无效时返回 401。
    """
    return login_user_by_role(payload, db, "admin")


@router.post("/staff/sessions", response_model=SessionResponse)
def create_staff_session(payload: UserLoginRequest, db: DatabaseSession) -> SessionResponse:
    """使用工作人员账号和密码登录。

    入参：payload 为工作人员账号密码；db 为数据库会话。
    返回值：SessionResponse：工作人员访问会话。
    异常：登录信息无效时返回 401。
    """
    return login_user_by_role(payload, db, "staff")


@router.post("/sessions/logout", response_model=LogoutResponse)
def logout(db: DatabaseSession, auth_session: CurrentAuthSession) -> LogoutResponse:
    """撤销当前 Bearer token 对应的服务端会话。

    入参：db 为数据库会话；auth_session 为当前有效会话。
    返回值：LogoutResponse：`success=true` 表示会话已撤销。
    异常：登录凭证缺失或无效时返回 401。
    """
    revoke_session(db, auth_session)
    return LogoutResponse(success=True)
