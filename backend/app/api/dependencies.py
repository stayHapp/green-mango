"""API 路由共用依赖。"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.guest import Guest

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_admin(
    db: DatabaseSession,
    admin_id: Annotated[int, Header(alias="X-Admin-Id")],
) -> User:
    """读取开发期管理员请求头并验证管理员账号。

    入参：
        db：当前请求数据库会话，由 FastAPI 依赖注入，必填。
        admin_id：`X-Admin-Id` 请求头中的管理员用户 ID，必填。

    返回值：
        User：已启用且角色为 admin 的管理员账号。

    异常：
        缺少、无效或禁用账号时抛出 401；账号不是管理员时抛出 403。

    使用示例：
        `GET /api/admin/meetings` 携带 `X-Admin-Id: 1`。
    """
    user = db.get(User, admin_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员身份无效或已停用。")
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号没有管理员权限。")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


def get_current_staff(
    db: DatabaseSession,
    staff_id: Annotated[int, Header(alias="X-Staff-Id")],
) -> User:
    """读取开发期工作人员请求头并验证工作人员账号。

    入参：db 为当前请求数据库会话；staff_id 为 `X-Staff-Id` 请求头中的用户 ID，均必填。
    返回值：User：已启用且角色为 staff 的工作人员账号。
    异常：缺少、无效或禁用账号时抛出 401；账号不是工作人员时抛出 403。
    """
    user = db.get(User, staff_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="工作人员身份无效或已停用。")
    if user.role != "staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号没有工作人员权限。")
    return user


CurrentStaff = Annotated[User, Depends(get_current_staff)]


def get_current_guest(db: DatabaseSession, guest_id: Annotated[int, Header(alias="X-Guest-Id")]) -> Guest:
    """读取开发期嘉宾请求头并验证嘉宾启用状态。

    入参：db 为数据库会话；guest_id 为 `X-Guest-Id` 请求头中的嘉宾 ID，均必填。
    返回值：Guest：已启用的嘉宾对象。
    异常：嘉宾不存在或已停用时抛出 401 HTTPException。
    """
    guest = db.get(Guest, guest_id)
    if guest is None or not guest.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="嘉宾身份无效或已停用。")
    return guest


CurrentGuest = Annotated[Guest, Depends(get_current_guest)]
