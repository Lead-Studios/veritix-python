from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any

from budget.common.enum.month_enum import Month
from budget.common.enum.status_enum import Status
from budget.dto.create_budget_category_dto import CreateBudgetCategoryDto
from budget.dto.create_budget_dto import CreateBudgetDto
from budget.dto.update_budget_category_dto import UpdateBudgetCategoryDto
from budget.entities.budget_category_entity import BudgetCategory
from budget.entities.budget_entity import Budget
from budget.helper.budget_helper import BudgetHelper
from budget.helper.budget_messages import BudgetMessages


class ServiceException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserMessages:
    USER_NOT_FOUND = "User not found"


class BudgetService:
    def __init__(
        self,
        budget_repository: Any,
        budget_category_repository: Any,
        user_repository: Any,
        expense_repository: Any,
        budget_helper: BudgetHelper,
    ) -> None:
        self.budget_repository = budget_repository
        self.budget_category_repository = budget_category_repository
        self.user_repository = user_repository
        self.expense_repository = expense_repository
        self.budget_helper = budget_helper

    async def create_budget(self, create_budget_dto: CreateBudgetDto, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        existing = await self.budget_repository.find_one(
            where={
                "month": create_budget_dto.month,
                "year": create_budget_dto.year,
                "user": {"id": getattr(user, "id", user_id)},
            }
        )
        if existing:
            raise ServiceException(BudgetMessages.BUDGET_ALREADY_EXISTS, 409)

        budget = await self.budget_repository.create(
            {**asdict(create_budget_dto), "user": user, "categories": []}
        )
        await self.budget_repository.save(budget)

        return {"message": BudgetMessages.BUDGET_CREATED, "data": budget}

    async def add_budget_category(self, budget_id: int, category_dto: CreateBudgetCategoryDto, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        budget = await self.budget_repository.find_one(
            where={"id": budget_id}, relations=["categories"]
        )
        if not budget:
            raise ServiceException(BudgetMessages.BUDGET_NOT_FOUND, 404)

        if budget.status == Status.DRAFT:
            raise ServiceException(BudgetMessages.BUDGET_NOT_ACTIVATED, 409)

        exists = next((cat for cat in budget.categories if cat.category == category_dto.category), None)
        if exists:
            raise ServiceException(BudgetMessages.CATEGORY_ALREADY_EXISTS, 409)

        new_category = await self.budget_category_repository.create({**asdict(category_dto), "budget": budget})
        await self.budget_category_repository.save(new_category)
        return {"message": BudgetMessages.CATEGORY_ADDED}

    async def retrieve_budget_details(self, user: Any) -> dict | list:
        now = datetime.utcnow()
        current_month_name = now.strftime("%B")
        current_month = Month[current_month_name.upper()]
        current_year = now.year

        budget = await self.budget_repository.find_one(
            where={"user": {"id": user.id}, "month": current_month, "year": current_year},
            relations=["categories"],
        )
        if not budget:
            return []

        month_date = datetime.strptime(f"01 {budget.month.value} {budget.year}", "%d %B %Y")
        start_date = month_date.strftime("%Y-%m-%d")
        next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")

        total_budget = sum(cat.amount for cat in budget.categories)
        total_spent = 0.0
        category_breakdown = []

        for category in budget.categories:
            expenses = await self.expense_repository.find(
                where={
                    "user": {"id": user.id},
                    "category": category.category,
                    "date": {"between": (start_date, end_date)},
                }
            )
            spent = sum(float(exp.amount) for exp in expenses)
            total_spent += spent

            percentage_used = round((spent / category.amount) * 100, 1) if category.amount > 0 else 0.0
            category_breakdown.append(
                {
                    "budgetCategoryId": category.id,
                    "category": category.category,
                    "budgetedAmount": self.budget_helper.format_to_naira(category.amount),
                    "spent": self.budget_helper.format_to_naira(spent),
                    "remaining": self.budget_helper.format_to_naira(category.amount - spent),
                    "percentageUsed": f"{percentage_used}%",
                }
            )

        utilization = f"{((total_spent / total_budget) * 100):.1f}%" if total_budget > 0 else "0.0%"
        return {
            "success": True,
            "data": [
                {
                    "id": budget.id,
                    "status": budget.status,
                    "month": budget.month,
                    "year": budget.year,
                    "createdAt": self.budget_helper.format_created_at(budget.created_at),
                    "totalBudget": self.budget_helper.format_to_naira(total_budget),
                    "totalSpent": self.budget_helper.format_to_naira(total_spent),
                    "remaining": self.budget_helper.format_to_naira(total_budget - total_spent),
                    "utilization": utilization,
                    "isActive": budget.status == Status.ACTIVE,
                    "categories": category_breakdown,
                }
            ],
        }

    async def update_budget_category(self, category_id: int, update_dto: UpdateBudgetCategoryDto, user: Any) -> dict:
        budget_category = await self.budget_category_repository.find_one(
            where={"id": category_id}, relations=["budget", "budget.user"]
        )
        if not budget_category:
            raise ServiceException(BudgetMessages.CATEGORY_NOT_FOUND, 404)

        if budget_category.budget.user.id != user.id:
            raise ServiceException(BudgetMessages.UNAUTHORIZED_ACCESS, 403)

        if update_dto.amount is not None:
            budget_category.amount = update_dto.amount
        if update_dto.category is not None:
            budget_category.category = update_dto.category

        await self.budget_category_repository.save(budget_category)
        return {"message": BudgetMessages.CATEGORY_UPDATED, "category": budget_category}

    async def delete_budget_category(self, category_id: int) -> dict:
        budget_category = await self.budget_category_repository.find_one(where={"id": category_id})
        if not budget_category:
            raise ServiceException(BudgetMessages.CATEGORY_NOT_FOUND, 404)

        await self.budget_category_repository.remove(budget_category)
        return {"message": BudgetMessages.CATEGORY_DELETED}

    async def retrieve_budget_category_by_id(self, category_id: int, user_id: int) -> dict:
        user = await self.user_repository.find_one(where={"id": user_id})
        if not user:
            raise ServiceException(UserMessages.USER_NOT_FOUND, 404)

        category = await self.budget_category_repository.find_one(where={"id": category_id})
        if not category:
            raise ServiceException(BudgetMessages.CATEGORY_NOT_FOUND, 404)

        return {"category": category.category, "amount": self.budget_helper.format_to_naira(category.amount)}

    async def activate_budget(self, budget_id: int, user_id: int) -> dict:
        budget = await self.budget_repository.find_one(where={"id": budget_id}, relations=["user"])
        if not budget:
            raise ServiceException(BudgetMessages.BUDGET_NOT_FOUND, 404)

        if budget.user.id != user_id:
            raise ServiceException(BudgetMessages.UNAUTHORIZED_ACCESS, 403)

        if budget.status == Status.ACTIVE:
            raise ServiceException(BudgetMessages.BUDGET_ALREADY_ACTIVATED, 400)

        budget.status = Status.ACTIVE
        await self.budget_repository.save(budget)
        return {"message": BudgetMessages.BUDGET_ACTIVATED}


from datetime import timedelta  # noqa: E402
