from enum import Enum


class ExpenseCategory(str, Enum):
    FOOD = "Food"
    HOUSING = "Housing"
    TRANSPORTATION = "Transportation"
    UTILITIES = "Utilities"
    CLOTHING = "Clothing"
    DRY_CLEANING = "Dry Cleaning"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    TRAVEL = "Travel"
    SAVINGS_INVESTMENT = "Savings & Investment"
    INSURANCE = "Insurance"
    PERSONAL_CARE = "Personal Care"
    GIFTS_DONATIONS = "Gifts & Donations"
    TAXES = "Taxes"
    DEBT_PAYMENTS = "Debt Payments"
    MISCELLANEOUS = "Miscellaneous"
    PET_CARE = "Pet Care"
    OTHER = "Other"
