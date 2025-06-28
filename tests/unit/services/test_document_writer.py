"""Unit tests for DocumentWriter service.

These tests do *not* require any external infrastructure and therefore live in
`tests/unit`. They validate the core contract: given a payload describing files
and directories, the writer must persist them safely, detect traversal
attempts, and report per-file status.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

from src.services.document_writer import DocumentWriter, FileWriteStatus


@pytest.fixture()
def sample_payload() -> dict:  # noqa: D401
    """Return a minimal payload with text and binary files."""
    png_bytes = b"\x89PNG\r\n\x1a\n"  # minimal PNG header
    return {
        "directories": [
            "src/utils",
            "assets/images",
        ],
        "files": [
            {"path": "src/utils/hello.txt", "content": "hello", "binary": False},
            {
                "path": "assets/images/logo.png",
                "content": base64.b64encode(png_bytes).decode(),
                "binary": True,
            },
        ],
    }


def test_persist_creates_structure(tmp_path: Path, sample_payload: dict) -> None:
    """Writer should materialise all files & dirs under base directory."""
    writer = DocumentWriter(tmp_path)
    result = writer.persist(sample_payload)

    # Overall success
    assert result.success is True

    # Check per-file status objects
    for status in result.file_results:
        assert isinstance(status, FileWriteStatus)
        assert status.success is True, f"Failed to write {status.path}: {status.error}"

    # Ensure directories were created
    for d in sample_payload["directories"]:
        assert (tmp_path / d).is_dir(), f"Directory {d} not created"

    # Ensure files exist with expected content/size
    text_file = tmp_path / "src/utils/hello.txt"
    assert text_file.read_text() == "hello"

    png_file = tmp_path / "assets/images/logo.png"
    assert png_file.stat().st_size == 8  # minimal PNG header length


def test_traversal_is_blocked(tmp_path: Path) -> None:
    """Attempting to write outside base_dir must raise an error and be reported."""
    writer = DocumentWriter(tmp_path)
    payload = {
        "files": [
            {"path": "../evil.txt", "content": "malicious", "binary": False},
        ]
    }
    result = writer.persist(payload)

    assert result.success is False
    assert result.file_results[0].success is False
    assert "Attempted path traversal" in (result.file_results[0].error or "")

    # The malicious file should NOT exist outside the base directory
    assert not (tmp_path.parent / "evil.txt").exists()
