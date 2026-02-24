import unittest

from expense.expense_controller import ExpenseController


class DummyExpenseService:
    pass


class ExpenseControllerSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        controller = ExpenseController(DummyExpenseService())
        self.assertIsNotNone(controller)


if __name__ == "__main__":
    unittest.main()
