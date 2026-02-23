
class BudgetMessages:
    BUDGET_CREATED = "Budget created successfully"
    BUDGET_ALREADY_EXISTS = "Budget already exists for this month and year"
    BUDGET_UPDATED = "Budget updated successfully"
    BUDGET_DELETED = "Budget deleted successfully"
    BUDGET_NOT_FOUND = "Budget not found"
    BUDGET_NOT_ACTIVATED = "Cannot add category to a draft budget. Please activate the budget first."
    BUDGET_ALREADY_ACTIVATED = "Budget is already active"
    BUDGET_ACTIVATED = "Budget activated successfully"
    CATEGORY_ADDED = "Category added to budget successfully"
    CATEGORY_ALREADY_EXISTS = "Category already exists in this budget"
    CATEGORY_UPDATED = "Category updated successfully"
    CATEGORY_DELETED = "Category deleted successfully"
    CATEGORY_NOT_FOUND = "Category not found in budget"
    INSUFFICIENT_FUNDS = "Insufficient funds for this expense"
    NO_ACTIVE_NOT_FOUND = "No active budget exists. Please create a budget before adding expenses."
    UNAUTHORIZED_ACCESS = "You do not have permission to access this budget"

    @staticmethod
    def no_active_budget(month: str, year: int) -> str:
        return f"You do not have an active budget for {month} {year}."

    @staticmethod
    def category_not_in_budget(category: str) -> str:
        return f"Category {category} is not included in your active budget."
