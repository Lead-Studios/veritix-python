from expense.entities.expense_entity import Expense


class ExpenseHelper:
    def format_expense_response(self, expense: Expense) -> dict:
        return {
            "id": expense.id,
            "description": expense.description,
            "amount": self.format_to_naira(float(expense.amount)),
            "category": expense.category,
            "date": expense.date,
        }

    def format_to_naira(self, amount: float) -> str:
        return f"NGN {amount:,.2f}"

    def format_expenses_response(self, expenses: list[Expense]) -> dict:
        formatted = [self.format_expense_response(expense) for expense in expenses]
        total_amount = sum(float(expense.amount) for expense in expenses)
        return {"totalAmount": self.format_to_naira(total_amount), "expenses": formatted}
