from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from expense.common.enum.expense_category_enum import ExpenseCategory


@dataclass
class Expense:
    id: Optional[int] = None
    description: str = ""
    amount: Decimal | float = 0
    category: ExpenseCategory = ExpenseCategory.OTHER
    date: str = ""
    note: Optional[str] = None
    user: Any = None
    created_at: datetime = field(default_factory=datetime.utcnow)
