from dataclasses import dataclass
from typing import Optional

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class UpdateBudgetCategoryDto:
    category: Optional[ExpenseCategory] = None
    amount: Optional[float] = None
