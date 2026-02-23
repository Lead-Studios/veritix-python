from enum import Enum


class PaymentMethod(str, Enum):
    CASH = "Cash"
    BANK = "Bank"
    CARD = "Card"
    TRANSFER = "Transfer"
    OTHER = "Other"
