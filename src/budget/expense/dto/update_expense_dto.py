from dataclasses import dataclass
from typing import Optional

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class UpdateExpenseDto:
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    note: Optional[str] = None
    date: Optional[str] = None
