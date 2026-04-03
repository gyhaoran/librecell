"""
Task 10: Tests for the logging system.
"""
import json
import logging
import pytest


@pytest.fixture(autouse=True)
def _restore_root_logger():
    """Save and restore root logger state around each test."""
    root = logging.getLogger()
    original_level = root.level
    original_handlers = root.handlers[:]
    yield
    root.setLevel(original_level)
    root.handlers = original_handlers


@pytest.mark.unit
class TestLoggingConfig:

    def test_setup_logging_import(self):
        from lccommon.logging_config import setup_logging
        assert callable(setup_logging)

    def test_json_formatter_import(self):
        from lccommon.logging_config import JsonFormatter
        assert issubclass(JsonFormatter, logging.Formatter)

    def test_setup_logging_sets_level(self):
        from lccommon.logging_config import setup_logging
        setup_logging(level=logging.WARNING)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_log_to_file(self, tmp_path):
        """Logging can be directed to a file."""
        from lccommon.logging_config import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(level=logging.DEBUG, log_file=str(log_file))

        test_logger = logging.getLogger("test_log_to_file")
        test_logger.info("Hello from test")

        # Flush handler
        for h in logging.getLogger().handlers:
            h.flush()

        content = log_file.read_text(encoding="utf-8")
        assert "Hello from test" in content

    def test_json_log_format(self, tmp_path):
        """JSON format produces valid JSON lines."""
        from lccommon.logging_config import setup_logging

        log_file = tmp_path / "test.json.log"
        setup_logging(level=logging.DEBUG, log_file=str(log_file), json_format=True)

        test_logger = logging.getLogger("test_json_format")
        test_logger.info("JSON test message")

        for h in logging.getLogger().handlers:
            h.flush()

        content = log_file.read_text(encoding="utf-8").strip()
        assert content, "Log file should not be empty"
        entry = json.loads(content)
        assert entry["level"] == "INFO"
        assert entry["message"] == "JSON test message"

    def test_log_levels_control_output(self, tmp_path):
        """Setting WARNING level suppresses INFO messages."""
        from lccommon.logging_config import setup_logging

        log_file = tmp_path / "level_test.log"
        setup_logging(level=logging.WARNING, log_file=str(log_file))

        test_logger = logging.getLogger("test_levels")
        test_logger.info("Should not appear")
        test_logger.warning("Should appear")

        for h in logging.getLogger().handlers:
            h.flush()

        content = log_file.read_text(encoding="utf-8")
        assert "Should not appear" not in content
        assert "Should appear" in content
