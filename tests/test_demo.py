"""Automated test verifying demo.py execution."""
import unittest
from demo import run_demonstration


class TestDemoExecution(unittest.TestCase):
    """Test suite ensuring demo script executes completely without errors."""

    def test_run_demonstration_executes_cleanly(self):
        """Verify the full 5-scenario demonstration executes without exceptions."""
        try:
            run_demonstration()
        except Exception as e:
            self.fail(f"demo.py raised an unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()
