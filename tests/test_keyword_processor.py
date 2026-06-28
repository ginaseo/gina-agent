"""Tests for KeywordProcessor."""

from unittest.mock import MagicMock, patch

import pytest

import processor.keyword_processor as kp_module
import processor.processing_state as ps_module
from processor.keyword_processor import KeywordProcessor


@pytest.fixture(autouse=True)
def patch_paths(vault, monkeypatch):
    monkeypatch.setattr(kp_module, "SUMMARY", vault / "knowledge" / "summary")
    monkeypatch.setattr(kp_module, "KEYWORD", vault / "knowledge" / "keywords")
    monkeypatch.setattr(ps_module, "STATE_DIR", vault / "index")


def _mock_client(answer: str = "- keyword1\n- keyword2"):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.ask.return_value = answer
    return mock


def test_no_files(caplog):
    KeywordProcessor().process()
    assert "No summary files" in caplog.text


def test_all_skip_no_llm(vault):
    src = vault / "knowledge" / "summary" / "a-summary.md"
    src.write_text("body", encoding="utf-8")

    with patch("processor.keyword_processor.LLMClient", return_value=_mock_client()):
        KeywordProcessor().process()

    with patch("processor.keyword_processor.LLMClient") as MockCls:
        KeywordProcessor().process()
        MockCls.assert_not_called()


def test_creates_keyword_file(vault):
    src = vault / "knowledge" / "summary" / "x-summary.md"
    src.write_text("summary content", encoding="utf-8")

    with patch(
        "processor.keyword_processor.LLMClient",
        return_value=_mock_client("- AI\n- Hermes"),
    ):
        KeywordProcessor().process()

    output = vault / "knowledge" / "keywords" / "x-keywords.md"
    assert output.exists()
    assert "AI" in output.read_text(encoding="utf-8")


def test_llm_failure_continues(vault, caplog):
    src = vault / "knowledge" / "summary" / "bad-summary.md"
    src.write_text("data", encoding="utf-8")

    mock = _mock_client()
    mock.ask.side_effect = RuntimeError("LLM error")

    with patch("processor.keyword_processor.LLMClient", return_value=mock):
        KeywordProcessor().process()  # Must not raise

    assert "[FAIL]" in caplog.text


def test_force_reprocesses(vault, caplog):
    src = vault / "knowledge" / "summary" / "y-summary.md"
    src.write_text("data", encoding="utf-8")

    with patch("processor.keyword_processor.LLMClient", return_value=_mock_client()):
        KeywordProcessor().process()
    caplog.clear()

    proc = KeywordProcessor()
    proc.force = True
    with patch("processor.keyword_processor.LLMClient", return_value=_mock_client()):
        proc.process()

    assert "[KEYWORD]" in caplog.text
