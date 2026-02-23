
class ExpenseModule:
    imports = ["Expense", "User", "Budget", "JwtModule", "PassportModule"]
    controllers = ["ExpenseController"]
    providers = ["ExpenseService", "ExpenseHelper"]
