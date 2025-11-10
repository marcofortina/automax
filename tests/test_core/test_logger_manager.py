"""
Tests for LoggerManager in Automax.
"""


def test_logger_creation(logger, tmp_path):
    logger.info("Test message")
    # Force write by shutdown
    logger.shutdown()
    log_file_path = logger.log_file
    assert log_file_path.exists()
    with open(log_file_path, "r") as f:
        content = f.read()
        assert "INFO" in content
        assert "Test message" in content


def test_logger_error_file(logger, tmp_path):
    logger.error("Error message")
    # Force write by shutdown
    logger.shutdown()
    err_file_path = logger.error_file
    assert err_file_path.exists()
    with open(err_file_path, "r") as f:
        content = f.read()
        assert "ERROR" in content
        assert "Error message" in content


def test_logger_fatal(logger, tmp_path):
    logger.fatal("Fatal message")
    # Force write by shutdown
    logger.shutdown()
    err_file_path = logger.error_file
    assert err_file_path.exists()
    with open(err_file_path, "r") as f:
        content = f.read()
        assert "FATAL" in content
        assert "Fatal message" in content


def test_logger_json_log(logger_with_json, tmp_path):
    logger_with_json.info("JSON test")
    # Force write by shutdown
    logger_with_json.shutdown()
    json_file_path = logger_with_json.json_file
    assert json_file_path.exists()
    with open(json_file_path, "r") as f:
        content = f.read()
        assert '"level": "INFO"' in content
        assert '"message": "JSON test"' in content
