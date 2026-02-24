from typing import Any

from budget.budget_service import BudgetService
from budget.dto.create_budget_category_dto import CreateBudgetCategoryDto
from budget.dto.create_budget_dto import CreateBudgetDto
from budget.dto.update_budget_category_dto import UpdateBudgetCategoryDto


class BudgetController:
    def __init__(self, budget_service: BudgetService) -> None:
        self.budget_service = budget_service

    async def create_budget(self, create_budget_dto: CreateBudgetDto, user: Any) -> dict:
        return await self.budget_service.create_budget(create_budget_dto, user.id)

    async def add_budget_category(self, budget_id: int, create_budget_category_dto: CreateBudgetCategoryDto, user: Any) -> dict:
        return await self.budget_service.add_budget_category(budget_id, create_budget_category_dto, user.id)

    async def retrieve_budget(self, user: Any) -> dict | list:
        return await self.budget_service.retrieve_budget_details(user)

    async def retrieve_budget_category_by_id(self, user: Any, category_id: int) -> dict:
        return await self.budget_service.retrieve_budget_category_by_id(category_id, user.id)

    async def update_budget(self, category_id: int, update_budget_dto: UpdateBudgetCategoryDto, user: Any) -> dict:
        return await self.budget_service.update_budget_category(category_id, update_budget_dto, user)

    async def activate_budget(self, budget_id: int, user: Any) -> dict:
        return await self.budget_service.activate_budget(budget_id, user.id)

    async def delete_budget(self, category_id: int) -> dict:
        return await self.budget_service.delete_budget_category(category_id)
