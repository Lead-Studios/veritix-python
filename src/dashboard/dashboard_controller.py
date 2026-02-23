from typing import Any

from budget.common.enum.month_enum import Month
from dashboard.dashboard_service import DashboardService


class DashboardController:
    def __init__(self, dashboard_service: DashboardService) -> None:
        self.dashboard_service = dashboard_service

    async def retrieve_dashboard_overview(self, user: Any, month: Month | None = None) -> dict:
        return await self.dashboard_service.retrieve_dashboard_overview(user, month)
