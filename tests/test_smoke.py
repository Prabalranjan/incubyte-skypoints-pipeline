"""Smoke test to verify project structure and package imports."""
import unittest
from skypoints import __version__
from skypoints.config import PipelineConfig


class TestSmoke(unittest.TestCase):
    """Smoke test suite."""

    def test_package_version(self):
        """Verify package version is defined."""
        self.assertEqual(__version__, "0.1.0")

    def test_pipeline_config_defaults(self):
        """Verify default pipeline configuration values."""
        config = PipelineConfig()
        self.assertEqual(config.database_path, ":memory:")
        self.assertEqual(config.stale_member_days_threshold, 90)


if __name__ == "__main__":
    unittest.main()
