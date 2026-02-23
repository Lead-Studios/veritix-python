from dataclasses import dataclass

from budget.common.enum.month_enum import Month


@dataclass
class CreateBudgetDto:
    month: Month
    year: int
