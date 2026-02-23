from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateBudgetDto:
    month: Optional[str] = None
    year: Optional[int] = None
