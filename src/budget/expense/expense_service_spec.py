import unittest

from expense.helper.expense_helper import ExpenseHelper
from expense.expense_service import ExpenseService


class DummyRepo:
    async def find_one(self, **kwargs):
        return None


class ExpenseServiceSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        service = ExpenseService(DummyRepo(), DummyRepo(), DummyRepo(), ExpenseHelper())
        self.assertIsNotNone(service)


if __name__ == "__main__":
    unittest.main()
