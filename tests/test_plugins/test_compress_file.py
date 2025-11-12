"""
Tests for the compress_file and uncompress_file utilities.
"""

import io
import tarfile
import zipfile


def test_compress_file_success(tmp_path, logger, plugin_manager):
    """
    Verify that file compression works for zip and tar.gz formats.
    """
    source = tmp_path / "source.txt"
    source.write_text("data")
    dest_zip = tmp_path / "archive.zip"
    dest_tar = tmp_path / "archive.tar.gz"
    compress_file = plugin_manager.get_plugin("compress_file")
    compress_file(str(source), str(dest_zip), "zip", logger=logger)
    assert dest_zip.exists()
    compress_file(str(source), str(dest_tar), "tar.gz", logger=logger)
    assert dest_tar.exists()


def test_compress_file_dry_run(tmp_path, logger, plugin_manager):
    """
    Verify that dry-run mode skips actual compression.
    """
    source = tmp_path / "source.txt"
    dest = tmp_path / "archive.zip"
    compress_file = plugin_manager.get_plugin("compress_file")
    compress_file(str(source), str(dest), "zip", dry_run=True, logger=logger)
    assert not dest.exists()


def test_uncompress_file_success(tmp_path, logger, plugin_manager):
    """
    Verify that compressed files are properly extracted.
    """
    # Create zip
    source_zip = tmp_path / "archive.zip"
    with zipfile.ZipFile(source_zip, "w") as zf:
        zf.writestr("file.txt", "data")
    dest = tmp_path / "extract"
    uncompress_file = plugin_manager.get_plugin("uncompress_file")
    uncompress_file(str(source_zip), str(dest), logger=logger)
    assert (dest / "file.txt").exists()

    # Create tar.gz
    source_tar = tmp_path / "archive.tar.gz"
    with tarfile.open(source_tar, "w:gz") as tf:
        tf.addfile(tarfile.TarInfo("file.txt"), io.BytesIO(b"data"))
    uncompress_file(str(source_tar), str(dest), logger=logger)
    assert (dest / "file.txt").exists()


def test_uncompress_file_dry_run(tmp_path, logger, plugin_manager):
    """
    Verify that dry-run mode skips extraction.
    """
    source = tmp_path / "archive.zip"
    dest = tmp_path / "extract"
    uncompress_file = plugin_manager.get_plugin("uncompress_file")
    uncompress_file(str(source), str(dest), dry_run=True, logger=logger)
    assert not dest.exists()


def test_schema_loaded(plugin_manager):
    """
    Verify SCHEMA is loaded for plugins.
    """
    assert "compress_file" in plugin_manager.schemas
    assert "uncompress_file" in plugin_manager.schemas
