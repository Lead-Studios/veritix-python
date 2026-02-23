
class BudgetModule:
    imports = ["Budget", "BudgetCategory", "Expense", "User", "JwtModule", "PassportModule"]
    controllers = ["BudgetController"]
    providers = ["BudgetService", "BudgetHelper"]
