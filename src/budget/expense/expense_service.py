from __future__ import annotations

from dataclasses import asdict
from datetime import date
from math import ceil
from typing import Any

from budget.common.enum.status_enum import Status
from budget.helper.budget_messages import BudgetMessages
from expense.common.enum.expense_category_enum import ExpenseCategory
from expense.dto.create_expense_dto import CreateExpenseDto
from expense.dto.update_expense_dto import UpdateExpenseDto
from expense.helper.expense_helper import ExpenseHelper
from expense.helper.expense_messages import ExpenseMessages


class ServiceException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserMessages:
    USER_NOT_FOUND = "User not found"


class ExpenseService:
    def __init__(
        self,
        expense_repository: Any,
        user_repository: Any,
        budget_repository: Any,
        expense_helper: ExpenseHelper,
    ) -> None:
        self.expense_repository = expense_repository
        self.user_repository = user_repository
        self.budget_repository = budget_repository
        self.expense_helper = expense_helper

    async def create_expense(self, create_expense_dto: CreateExpenseDto, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        active_budget = await self.budget_repository.find_one(
            where={"user": {"id": user_id}, "status": Status.ACTIVE}, relations=["categories"]
        )
        if not active_budget:
            active_budget = await self.budget_repository.find_one(
                where={"user": {"id": user_id}, "status": Status.DRAFT}, relations=["categories"]
            )
            if active_budget:
                active_budget.status = Status.ACTIVE
                await self.budget_repository.save(active_budget)

        if not active_budget:
            raise ServiceException(BudgetMessages.NO_ACTIVE_NOT_FOUND, 400)

        budget_category = next(
            (cat for cat in active_budget.categories if cat.category == create_expense_dto.category), None
        )
        if not budget_category:
            raise ServiceException(
                f"The category '{create_expense_dto.category}' is not part of your budget. "
                "Please add this category to your budget first.",
                400,
            )

        payload = asdict(create_expense_dto)
        payload["user"] = user
        payload["date"] = payload.get("date") or date.today().isoformat()

        expense = await self.expense_repository.create(payload)
        await self.expense_repository.save(expense)
        return {"success": True, "message": ExpenseMessages.EXPENSE_CREATED}

    async def retrieve_user_expenses(self, user_id: int, query: dict[str, Any]) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        category = query.get("category")
        search = query.get("search")
        page = int(query.get("page", 1))
        per_page = int(query.get("perPage", 10))

        valid_categories = {item.value for item in ExpenseCategory}
        category_value = category.value if isinstance(category, ExpenseCategory) else category
        if category and category_value not in valid_categories:
            raise ServiceException(ExpenseMessages.INVALID_CATEGORY, 400)

        expenses = await self.expense_repository.find(where={"user": {"id": user_id}})
        expenses.sort(key=lambda item: item.date, reverse=True)

        if category:
            expenses = [e for e in expenses if (e.category.value if hasattr(e.category, "value") else e.category) == category_value]

        if search:
            search_lower = str(search).lower()
            filtered = []
            for expense in expenses:
                category_text = expense.category.value if hasattr(expense.category, "value") else str(expense.category)
                if (
                    search_lower in expense.description.lower()
                    or search_lower in category_text.lower()
                    or search_lower in str(expense.amount)
                ):
                    filtered.append(expense)
            expenses = filtered

        total_items = len(expenses)
        start = max(page - 1, 0) * per_page
        end = start + per_page
        paged_expenses = expenses[start:end]

        formatted_expenses = self.expense_helper.format_expenses_response(paged_expenses)
        total_pages = ceil(total_items / per_page) if per_page else 0

        meta = {
            "currentPage": page,
            "itemsPerPage": per_page,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasPreviousPage": page > 1,
            "hasNextPage": page < total_pages,
        }

        return {
            "message": ExpenseMessages.EXPENSE_LIST_FETCHED,
            "totalAmount": formatted_expenses["totalAmount"],
            "items": formatted_expenses["expenses"],
            "meta": meta,
        }

    async def update_expense(self, expense_id: int, update_expense_dto: UpdateExpenseDto, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        expense = await self.expense_repository.find_one(where={"id": expense_id, "user": {"id": user.id}})
        if not expense:
            raise ServiceException(ExpenseMessages.EXPENSE_NOT_FOUND, 404)

        for field, value in asdict(update_expense_dto).items():
            if value is not None:
                setattr(expense, field, value)

        await self.expense_repository.save(expense)
        return {"message": ExpenseMessages.EXPENSE_UPDATED}

    async def remove_expense(self, expense_id: int, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        expense = await self.expense_repository.find_one(where={"id": expense_id, "user": {"id": user.id}})
        if not expense:
            raise ServiceException(ExpenseMessages.EXPENSE_NOT_FOUND, 404)

        await self.expense_repository.remove(expense)
        return {"message": ExpenseMessages.EXPENSE_DELETED}
