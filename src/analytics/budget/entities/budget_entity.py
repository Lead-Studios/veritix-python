from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from budget.common.enum.month_enum import Month
from budget.common.enum.status_enum import Status


@dataclass
class Budget:
    id: Optional[int] = None
    month: Month = Month.JANUARY
    year: int = datetime.utcnow().year
    status: Status = Status.DRAFT
    user: Any = None
    categories: list[Any] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
