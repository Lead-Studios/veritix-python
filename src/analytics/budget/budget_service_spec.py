import unittest

from budget.helper.budget_helper import BudgetHelper
from budget.budget_service import BudgetService


class DummyRepo:
    async def find_one(self, **kwargs):
        return None


class BudgetServiceSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        service = BudgetService(DummyRepo(), DummyRepo(), DummyRepo(), DummyRepo(), BudgetHelper())
        self.assertIsNotNone(service)


if __name__ == "__main__":
    unittest.main()
