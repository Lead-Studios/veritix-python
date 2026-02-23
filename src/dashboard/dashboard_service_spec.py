import unittest

from dashboard.dashboard_service import DashboardService
from dashboard.helper.dashboard_helper import DashboardHelper


class DummyRepo:
    async def find_one(self, **kwargs):
        return None


class DashboardServiceSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        service = DashboardService(DummyRepo(), DashboardHelper(), DummyRepo())
        self.assertIsNotNone(service)


if __name__ == "__main__":
    unittest.main()
