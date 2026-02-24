
class DashboardModule:
    imports = ["Expense", "Budget", "JwtModule", "PassportModule"]
    controllers = ["DashboardController"]
    providers = ["DashboardService", "DashboardHelper"]
