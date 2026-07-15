"""管理员签到统计与明细路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.schemas.admin_check_in import AdminCheckInSummary
from app.services.admin_check_ins import get_check_in_summary
from app.services.admin_meetings import get_authorized_meeting

router = APIRouter(prefix="/admin/meetings")


@router.get("/{meeting_id}/check-ins", response_model=AdminCheckInSummary)
def get_admin_check_ins(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> AdminCheckInSummary:
    """获取管理员有权限查看的会议签到统计与明细。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSummary：会议签到统计和明细。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return get_check_in_summary(db, meeting)
