"""
Tests for the write_file_content utility.
"""


def test_write_file_content_success(tmp_path, logger, plugin_manager):
    """
    Verify that writing file content works correctly.
    """
    file = tmp_path / "test.txt"
    write_file_content = plugin_manager.get_plugin("write_file_content")
    write_file_content(str(file), "content", logger=logger, dry_run=False)
    assert file.read_text() == "content"


def test_write_file_content_dry_run(tmp_path, logger, plugin_manager):
    """
    Verify that dry-run mode skips actual file writing.
    """
    file = tmp_path / "test.txt"
    write_file_content = plugin_manager.get_plugin("write_file_content")
    write_file_content(str(file), "content", dry_run=True, logger=logger)
    assert not file.exists()


def test_schema_loaded(plugin_manager):
    """
    Verify SCHEMA is loaded.
    """
    schema = plugin_manager.get_schema("write_file_content")
    assert "file_path" in schema
