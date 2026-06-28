"""Tests for ProcessorRunner — argument parsing, target selection, parallel, watch."""
import sys
from unittest.mock import patch

from processor.runner import ProcessorRunner


def _make_runner(args: list[str]) -> ProcessorRunner:
    with patch.object(sys, "argv", ["runner"] + args):
        return ProcessorRunner()


# ------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------

def test_no_args_defaults():
    runner = _make_runner([])
    assert runner.force is False
    assert runner.parallel is False
    assert runner.watch is False
    assert runner.watch_interval == 30
    assert runner.targets == set()


def test_force_flag():
    runner = _make_runner(["--force"])
    assert runner.force is True


def test_parallel_flag():
    runner = _make_runner(["--parallel"])
    assert runner.parallel is True


def test_watch_flag_default_interval():
    runner = _make_runner(["--watch"])
    assert runner.watch is True
    assert runner.watch_interval == 30


def test_watch_flag_custom_interval():
    runner = _make_runner(["--watch=60"])
    assert runner.watch is True
    assert runner.watch_interval == 60


def test_watch_flag_invalid_interval_falls_back():
    runner = _make_runner(["--watch=bad"])
    assert runner.watch is True
    assert runner.watch_interval == 30


def test_target_selection():
    runner = _make_runner(["summary", "entity"])
    assert "summary" in runner.targets
    assert "entity" in runner.targets


def test_mixed_flags_and_targets():
    runner = _make_runner(["--force", "markdown", "--parallel"])
    assert runner.force is True
    assert runner.parallel is True
    assert "markdown" in runner.targets


# ------------------------------------------------------------------
# Subcommand parsing
# ------------------------------------------------------------------

def test_subcommand_defaults_to_run():
    runner = _make_runner([])
    assert runner.subcommand == "run"
    assert runner.log_level == "INFO"
    assert runner.log_file_path is None


def test_subcommand_run_explicit():
    runner = _make_runner(["run"])
    assert runner.subcommand == "run"
    assert runner.targets == set()


def test_subcommand_watch():
    runner = _make_runner(["watch"])
    assert runner.subcommand == "watch"


def test_subcommand_validate():
    runner = _make_runner(["validate"])
    assert runner.subcommand == "validate"


def test_subcommand_clean():
    runner = _make_runner(["clean"])
    assert runner.subcommand == "clean"


def test_subcommand_benchmark():
    runner = _make_runner(["benchmark"])
    assert runner.subcommand == "benchmark"


def test_subcommand_does_not_eat_targets():
    """Non-subcommand words become targets, not subcommands."""
    runner = _make_runner(["summary"])
    assert runner.subcommand == "run"
    assert "summary" in runner.targets


def test_run_subcommand_with_flags_and_targets():
    runner = _make_runner(["run", "--force", "markdown"])
    assert runner.subcommand == "run"
    assert runner.force is True
    assert "markdown" in runner.targets


def test_log_level_flag():
    runner = _make_runner(["--log-level=debug"])
    assert runner.log_level == "debug"


def test_log_file_flag():
    runner = _make_runner(["--log-file=logs/hermes.log"])
    assert runner.log_file_path == "logs/hermes.log"


# ------------------------------------------------------------------
# Run behavior
# ------------------------------------------------------------------

class _TrackingProcessor:
    """Processor that records whether process() was called."""
    def __init__(self):
        self.called = False
        self.force = False

    def process(self):
        self.called = True


def test_runs_all_processors_by_default():
    runner = _make_runner([])
    p1, p2 = _TrackingProcessor(), _TrackingProcessor()
    runner.processors = [("a", p1), ("b", p2)]
    runner.run()
    assert p1.called and p2.called


def test_target_filters_processors():
    runner = _make_runner(["a"])
    p1, p2 = _TrackingProcessor(), _TrackingProcessor()
    runner.processors = [("a", p1), ("b", p2)]
    runner.run()
    assert p1.called
    assert not p2.called


def test_force_propagated_to_processors():
    runner = _make_runner(["--force"])
    p = _TrackingProcessor()
    runner.processors = [("a", p)]
    runner.run()
    assert p.force is True


def test_failed_processor_does_not_abort_others(caplog):
    class _FailProcessor:
        force = False
        def process(self):
            raise RuntimeError("intentional failure")

    runner = _make_runner([])
    p_fail = _FailProcessor()
    p_ok = _TrackingProcessor()
    runner.processors = [("fail", p_fail), ("ok", p_ok)]
    runner.run()

    assert p_ok.called
    assert "[FAIL]" in caplog.text


def test_parallel_runs_processors():
    runner = _make_runner(["--parallel"])
    p = _TrackingProcessor()
    runner.processors = [("entity", p)]  # entity is in the parallel group
    runner.run()
    assert p.called


def test_benchmark_runs_all_processors():
    runner = _make_runner(["benchmark"])
    p = _TrackingProcessor()
    runner.processors = [("a", p)]
    runner.run()
    assert p.called


def test_validate_subcommand(monkeypatch):
    called = []

    class _FakeValidator:
        def process(self):
            called.append(True)

    monkeypatch.setattr("processor.runner.Validator", _FakeValidator)
    runner = _make_runner(["validate"])
    runner.run()
    assert called


def test_clean_subcommand(monkeypatch):
    called = []

    class _FakeCleaner:
        def process(self):
            called.append(True)

    monkeypatch.setattr("processor.runner.Cleaner", _FakeCleaner)
    runner = _make_runner(["clean"])
    runner.run()
    assert called


# ------------------------------------------------------------------
# Watch mode parsing (does not actually run the loop)
# ------------------------------------------------------------------

def test_parse_watch_no_flag():
    enabled, interval = ProcessorRunner._parse_watch([])
    assert enabled is False


def test_parse_watch_with_flag():
    enabled, interval = ProcessorRunner._parse_watch(["--watch"])
    assert enabled is True
    assert interval == 30


def test_parse_watch_custom():
    enabled, interval = ProcessorRunner._parse_watch(["--watch=120"])
    assert enabled is True
    assert interval == 120


def test_parse_watch_minimum_interval():
    """Interval is clamped to at least 1."""
    enabled, interval = ProcessorRunner._parse_watch(["--watch=0"])
    assert interval == 1


# ------------------------------------------------------------------
# New v1.1 subcommands
# ------------------------------------------------------------------

def test_subcommand_daemon():
    runner = _make_runner(["daemon"])
    assert runner.subcommand == "daemon"


def test_subcommand_history():
    runner = _make_runner(["history"])
    assert runner.subcommand == "history"


def test_subcommand_evaluate():
    runner = _make_runner(["evaluate"])
    assert runner.subcommand == "evaluate"


def test_subcommand_benchmark_retrieval():
    runner = _make_runner(["benchmark-retrieval"])
    assert runner.subcommand == "benchmark-retrieval"


def test_last_flag_parsed():
    runner = _make_runner(["history", "--last=50"])
    assert runner.last_n == 50


def test_last_n_default():
    runner = _make_runner(["history"])
    assert runner.last_n == 20
