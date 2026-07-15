"""管理员签到统计与明细接口结构。"""

from datetime import datetime

from pydantic import BaseModel


class AdminCheckInItem(BaseModel):
    """管理员查看的单条签到明细。"""

    guest_id: int
    guest_name: str
    phone: str
    checked_in_at: datetime
    method: str
    staff_name: str | None


class AdminCheckInSummary(BaseModel):
    """会议签到统计与明细响应。"""

    total_guests: int
    checked_in_count: int
    unchecked_count: int
    records: list[AdminCheckInItem]
