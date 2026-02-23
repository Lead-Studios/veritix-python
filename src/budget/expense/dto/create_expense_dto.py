from dataclasses import dataclass
from typing import Optional

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class CreateExpenseDto:
    description: str
    amount: float
    category: ExpenseCategory
    date: Optional[str] = None
    note: Optional[str] = None
