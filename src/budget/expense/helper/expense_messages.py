
class ExpenseMessages:
    EXPENSE_CREATED = "Expense added successfully"
    EXPENSE_UPDATED = "Expense updated successfully"
    EXPENSE_DELETED = "Expense deleted successfully"
    EXPENSE_NOT_FOUND = "Expense not found or does not belong to user"
    INVALID_EXPENSE_DATA = "Invalid expense data provided"
    UNAUTHORIZED_ACCESS = "You do not have permission to access this expense"
    EXPENSE_LIST_FETCHED = "Expenses fetched successfully"
    NO_EXPENSES_FOUND = "No expenses found for the given criteria"
    INVALID_CATEGORY = "Invalid category name"

    @staticmethod
    def exceeds_category_budget(category: str) -> str:
        return f"Cannot add expense - it exceeds your {category} budget"
