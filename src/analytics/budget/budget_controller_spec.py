import unittest

from budget.budget_controller import BudgetController


class DummyBudgetService:
    pass


class BudgetControllerSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        controller = BudgetController(DummyBudgetService())
        self.assertIsNotNone(controller)


if __name__ == "__main__":
    unittest.main()
