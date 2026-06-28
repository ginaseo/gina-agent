"""Tests for LLMCache — put/get/flush/merge behavior."""
import json

import pytest

import processor.llm.cache as cache_module
from processor.llm.cache import LLMCache


@pytest.fixture(autouse=True)
def patch_cache_paths(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_file = cache_dir / "llm_cache.json"
    monkeypatch.setattr(cache_module, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(cache_module, "CACHE_FILE", cache_file)
    return cache_file


def test_get_miss():
    cache = LLMCache()
    assert cache.get("unknown prompt") is None


def test_put_get_roundtrip():
    cache = LLMCache()
    cache.put("hello", "world")
    assert cache.get("hello") == "world"


def test_put_does_not_write_immediately(tmp_path):
    cache_file = tmp_path / "cache" / "llm_cache.json"
    cache = LLMCache()
    cache.put("p", "r")
    assert not cache_file.exists(), "put() must not write to disk immediately"


def test_flush_persists(tmp_path):
    cache_file = tmp_path / "cache" / "llm_cache.json"
    cache = LLMCache()
    cache.put("p", "r")
    cache.flush()

    assert cache_file.exists()
    cache2 = LLMCache()
    assert cache2.get("p") == "r"


def test_flush_idempotent_when_clean():
    cache_file = cache_module.CACHE_FILE
    cache = LLMCache()
    cache.flush()  # Nothing dirty — must not write
    assert not cache_file.exists()


def test_flush_merges_with_existing(tmp_path):
    cache_file = tmp_path / "cache" / "llm_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    # Pre-seed the cache file with an existing entry
    key = LLMCache()._key("existing")
    cache_file.write_text(json.dumps({key: "old_value"}), encoding="utf-8")

    cache = LLMCache()
    cache.put("new_prompt", "new_value")
    cache.flush()

    data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert data[key] == "old_value", "flush() must preserve pre-existing entries"
    assert cache.get("new_prompt") == "new_value"


def test_same_prompt_same_key():
    cache = LLMCache()
    key1 = cache._key("test prompt")
    key2 = cache._key("test prompt")
    assert key1 == key2


def test_different_prompts_different_keys():
    cache = LLMCache()
    assert cache._key("prompt A") != cache._key("prompt B")
