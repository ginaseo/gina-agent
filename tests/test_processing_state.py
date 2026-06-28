"""Tests for ProcessingState incremental logic."""
from pathlib import Path

import pytest

import processor.processing_state as ps_module
from processor.processing_state import ProcessingState


@pytest.fixture(autouse=True)
def patch_state_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ps_module, "STATE_DIR", tmp_path / "index")


def _make_file(tmp_path: Path, name: str = "test.md") -> Path:
    f = tmp_path / name
    f.write_text("content", encoding="utf-8")
    return f


def test_new_file_is_modified(tmp_path):
    f = _make_file(tmp_path)
    state = ProcessingState("test")
    assert state.is_modified(f) is True


def test_unchanged_file_not_modified(tmp_path):
    f = _make_file(tmp_path)
    state = ProcessingState("test")
    state.update(f)
    state.save()

    state2 = ProcessingState("test")
    assert state2.is_modified(f) is False


def test_modified_file_detected(tmp_path):
    import os
    f = _make_file(tmp_path)
    state = ProcessingState("test")
    state.update(f)
    state.save()

    # Explicitly advance mtime — avoids sub-second filesystem resolution issues
    new_mtime = f.stat().st_mtime + 2.0
    os.utime(f, (new_mtime, new_mtime))

    state2 = ProcessingState("test")
    assert state2.is_modified(f) is True


def test_force_always_modified(tmp_path):
    f = _make_file(tmp_path)
    state = ProcessingState("test", force=True)
    state.update(f)
    state.save()

    state2 = ProcessingState("test", force=True)
    assert state2.is_modified(f) is True



def test_save_load_roundtrip(tmp_path):
    f = _make_file(tmp_path)
    state = ProcessingState("test")
    state.update(f)
    state.save()

    state2 = ProcessingState("test")
    assert str(f.resolve()) in state2.state
