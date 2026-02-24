from typing import Any

from expense.dto.create_expense_dto import CreateExpenseDto
from expense.dto.update_expense_dto import UpdateExpenseDto
from expense.expense_service import ExpenseService


class ExpenseController:
    def __init__(self, expense_service: ExpenseService) -> None:
        self.expense_service = expense_service

    async def create(self, create_expense_dto: CreateExpenseDto, user: Any) -> dict:
        return await self.expense_service.create_expense(create_expense_dto, user.id)

    async def retrieve_user_expenses(
        self,
        user: Any,
        pagination_query: dict,
        category: str | None = None,
        search: str | None = None,
    ) -> dict:
        query = {**pagination_query, "category": category, "search": search}
        return await self.expense_service.retrieve_user_expenses(user.id, query)

    async def update(self, expense_id: int, update_expense_dto: UpdateExpenseDto, user: Any) -> dict:
        return await self.expense_service.update_expense(expense_id, update_expense_dto, user.id)

    async def remove(self, expense_id: int, user: Any) -> dict:
        return await self.expense_service.remove_expense(expense_id, user.id)
