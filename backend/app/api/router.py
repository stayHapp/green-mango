"""统一 API 路由汇总入口。"""

from fastapi import APIRouter

from app.api.routes import (
    admin_check_ins,
    admin_excel,
    admin_guests,
    admin_meetings,
    admin_resources,
    check_ins,
    guest_applications,
    guest_sessions,
    health,
    sessions,
    staff,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(admin_meetings.router, tags=["admin-meetings"])
api_router.include_router(admin_guests.router, tags=["admin-guests"])
api_router.include_router(admin_check_ins.router, tags=["admin-check-ins"])
api_router.include_router(admin_excel.router, tags=["admin-excel"])
api_router.include_router(admin_resources.router, tags=["admin-resources"])
api_router.include_router(staff.admin_router, tags=["admin-staff"])
api_router.include_router(staff.staff_router, tags=["staff-meetings"])
api_router.include_router(check_ins.router, tags=["staff-check-ins"])
api_router.include_router(guest_sessions.router, tags=["guest-sessions"])
api_router.include_router(guest_applications.public_router, tags=["guest-applications"])
api_router.include_router(guest_applications.admin_router, tags=["admin-guest-applications"])
