"""Shared pytest fixtures for Hermes Agent tests."""

from pathlib import Path

import pytest

from processor.log import setup

setup()  # Ensure logging is configured for all tests


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Minimal vault directory structure."""
    (tmp_path / "slack").mkdir()
    (tmp_path / "knowledge" / "slack").mkdir(parents=True)
    (tmp_path / "knowledge" / "summary").mkdir(parents=True)
    (tmp_path / "knowledge" / "entity").mkdir(parents=True)
    (tmp_path / "knowledge" / "keywords").mkdir(parents=True)
    (tmp_path / "knowledge" / "related").mkdir(parents=True)
    (tmp_path / "projects").mkdir()
    (tmp_path / "people").mkdir()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "index").mkdir()
    (tmp_path / "cache").mkdir()
    return tmp_path
