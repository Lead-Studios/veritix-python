import unittest

from dashboard.dashboard_controller import DashboardController


class DummyDashboardService:
    pass


class DashboardControllerSpec(unittest.TestCase):
    def test_should_be_defined(self) -> None:
        controller = DashboardController(DummyDashboardService())
        self.assertIsNotNone(controller)


if __name__ == "__main__":
    unittest.main()
