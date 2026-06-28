"""Tests for RelatedProcessor."""

from unittest.mock import MagicMock, patch

import pytest

import processor.processing_state as ps_module
import processor.related_processor as rp_module
from processor.related_processor import RelatedProcessor


@pytest.fixture(autouse=True)
def patch_paths(vault, monkeypatch):
    monkeypatch.setattr(rp_module, "SUMMARY", vault / "knowledge" / "summary")
    monkeypatch.setattr(rp_module, "RELATED", vault / "knowledge" / "related")
    monkeypatch.setattr(ps_module, "STATE_DIR", vault / "index")


def _mock_client(answer: str = "[[Doc A]]\n[[Doc B]]"):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.ask.return_value = answer
    return mock


def test_no_files(caplog):
    RelatedProcessor().process()
    assert "No summary files" in caplog.text


def test_all_skip_no_llm(vault):
    src = vault / "knowledge" / "summary" / "a-summary.md"
    src.write_text("body", encoding="utf-8")

    with patch("processor.related_processor.LLMClient", return_value=_mock_client()):
        RelatedProcessor().process()

    with patch("processor.related_processor.LLMClient") as MockCls:
        RelatedProcessor().process()
        MockCls.assert_not_called()


def test_creates_related_file(vault):
    src = vault / "knowledge" / "summary" / "z-summary.md"
    src.write_text("summary", encoding="utf-8")

    with patch("processor.related_processor.LLMClient", return_value=_mock_client("[[Note A]]")):
        RelatedProcessor().process()

    output = vault / "knowledge" / "related" / "z-related.md"
    assert output.exists()
    assert "[[Note A]]" in output.read_text(encoding="utf-8")


def test_output_is_stripped(vault):
    src = vault / "knowledge" / "summary" / "s-summary.md"
    src.write_text("body", encoding="utf-8")

    with patch("processor.related_processor.LLMClient", return_value=_mock_client("  [[X]]  \n\n")):
        RelatedProcessor().process()

    content = (vault / "knowledge" / "related" / "s-related.md").read_text(encoding="utf-8")
    assert content == "[[X]]"


def test_force_reprocesses(vault, caplog):
    src = vault / "knowledge" / "summary" / "r-summary.md"
    src.write_text("data", encoding="utf-8")

    with patch("processor.related_processor.LLMClient", return_value=_mock_client()):
        RelatedProcessor().process()
    caplog.clear()

    proc = RelatedProcessor()
    proc.force = True
    with patch("processor.related_processor.LLMClient", return_value=_mock_client()):
        proc.process()

    assert "[RELATED]" in caplog.text
