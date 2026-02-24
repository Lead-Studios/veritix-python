from datetime import datetime


class BudgetHelper:
    def format_created_at(self, date: datetime) -> str:
        return f"Created on {date.strftime('%b %d, %Y')}"

    def format_to_naira(self, amount: float) -> str:
        return f"NGN {amount:,.2f}"
