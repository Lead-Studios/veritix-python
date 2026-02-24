from dataclasses import dataclass

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class CreateBudgetCategoryDto:
    category: ExpenseCategory
    amount: float
