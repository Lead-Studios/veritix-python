from __future__ import annotations

from calendar import monthrange
from datetime import datetime
from typing import Any

from budget.common.enum.month_enum import Month
from budget.common.enum.status_enum import Status
from expense.common.enum.expense_category_enum import ExpenseCategory
from dashboard.helper.dashboard_helper import DashboardHelper
from dashboard.helper.dashboard_message import DashboardMessages


class DashboardService:
    def __init__(self, budget_repository: Any, dashboard_helper: DashboardHelper, expense_repository: Any) -> None:
        self.budget_repository = budget_repository
        self.dashboard_helper = dashboard_helper
        self.expense_repository = expense_repository

    async def retrieve_dashboard_overview(self, user: Any, month: Month | None = None) -> dict:
        current_date = datetime.utcnow()
        selected_month = month or Month[current_date.strftime("%B").upper()]
        current_year = current_date.year

        budget = await self.budget_repository.find_one(
            where={
                "user": {"id": user.id},
                "month": selected_month,
                "year": current_year,
                "status": Status.ACTIVE,
            },
            relations=["categories"],
        )

        month_values = [item.value for item in Month]
        month_index = month_values.index(selected_month.value) + 1
        first_day = f"{current_year}-{month_index:02d}-01"
        last_day = f"{current_year}-{month_index:02d}-{monthrange(current_year, month_index)[1]:02d}"

        expenses = await self.expense_repository.find(
            where={"user": {"id": user.id}, "date": {"between": (first_day, last_day)}}
        )

        recent_transactions_raw = await self.expense_repository.find(
            where={"user": {"id": user.id}, "date": {"between": (first_day, last_day)}},
            order={"created_at": "DESC"},
            take=5,
        )

        recent_transactions = [
            {
                "description": exp.description,
                "amount": self.dashboard_helper.format_to_naira(float(exp.amount)),
                "category": exp.category,
                "date": exp.date,
            }
            for exp in recent_transactions_raw
        ]

        if not budget:
            return {
                "message": DashboardMessages.DASHBOARD_OVERVIEW_FETCHED,
                "dashBoardOverview": {
                    "totalBudget": self.dashboard_helper.format_to_naira(0),
                    "totalExpense": self.dashboard_helper.format_to_naira(0),
                    "totalRemaining": self.dashboard_helper.format_to_naira(0),
                    "totalSavings": self.dashboard_helper.format_to_naira(0),
                },
                "budgetOverview": [],
                "recentTransactions": recent_transactions,
            }

        total_budget = sum(cat.amount for cat in budget.categories)
        total_expense = sum(float(exp.amount) for exp in expenses)

        total_savings = sum(
            float(exp.amount)
            for exp in expenses
            if (exp.category.value if hasattr(exp.category, "value") else exp.category)
            == ExpenseCategory.SAVINGS_INVESTMENT.value
        )

        total_remaining = total_budget - total_expense

        raw_category_breakdown = []
        for category in budget.categories:
            category_expenses = [exp for exp in expenses if exp.category == category.category]
            spent = sum(float(exp.amount) for exp in category_expenses)
            percentage_used = f"{((spent / category.amount) * 100):.1f}%" if category.amount > 0 else "0.0%"

            raw_category_breakdown.append(
                {
                    "data": {
                        "category": category.category,
                        "budgetedAmount": self.dashboard_helper.format_to_naira(category.amount),
                        "spent": self.dashboard_helper.format_to_naira(spent),
                        "remaining": self.dashboard_helper.format_to_naira(category.amount - spent),
                        "percentageUsed": percentage_used,
                    },
                    "createdAt": category.created_at,
                }
            )

        top_category_breakdown = [
            entry["data"]
            for entry in sorted(
                raw_category_breakdown,
                key=lambda row: row["createdAt"],
                reverse=True,
            )[:5]
        ]

        return {
            "message": DashboardMessages.DASHBOARD_OVERVIEW_FETCHED,
            "dashBoardOverview": {
                "totalBudget": self.dashboard_helper.format_to_naira(total_budget),
                "totalExpense": self.dashboard_helper.format_to_naira(total_expense),
                "totalRemaining": self.dashboard_helper.format_to_naira(total_remaining),
                "totalSavings": self.dashboard_helper.format_to_naira(total_savings),
            },
            "budgetOverview": top_category_breakdown,
            "recentTransactions": recent_transactions,
        }
