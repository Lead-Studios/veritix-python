from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class BudgetCategory:
    id: Optional[int] = None
    category: ExpenseCategory = ExpenseCategory.OTHER
    amount: float = 0.0
    budget: "Budget | None" = None
    created_at: datetime = field(default_factory=datetime.utcnow)


from budget.entities.budget_entity import Budget  # noqa: E402
