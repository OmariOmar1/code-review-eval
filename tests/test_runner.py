import subprocess

import pytest

from code_review_eval import runner
from code_review_eval.runner import (
    RunnerError,
    build_result,
    docker_available,
    docker_command,
    parse_pytest_output,
    run_all,
    run_candidate,
)
from code_review_eval.tasks import load_task

from .conftest import make_task

FAILING_OUTPUT = """.F..                                                                     [100%]
=========================== short test summary info ============================
FAILED test_solution.py::test_b - assert 1 == 2
1 failed, 3 passed in 0.05s
"""


def test_parse_all_passed():
    parsed = parse_pytest_output("....  [100%]\n4 passed in 0.02s\n")
    assert parsed == {"passed": 4, "failed": 0, "runtime_s": 0.02, "errors": []}


def test_parse_failures():
    parsed = parse_pytest_output(FAILING_OUTPUT)
    assert parsed["passed"] == 3
    assert parsed["failed"] == 1
    assert parsed["runtime_s"] == 0.05
    assert parsed["errors"] == ["test_solution.py::test_b - assert 1 == 2"]


def test_parse_collection_error_counts_as_failure():
    output = "ERROR test_solution.py - SyntaxError: invalid syntax\n1 error in 0.10s\n"
    parsed = parse_pytest_output(output)
    assert parsed["passed"] == 0
    assert parsed["failed"] == 1
    assert parsed["errors"] == ["test_solution.py - SyntaxError: invalid syntax"]


def test_parse_garbage():
    assert parse_pytest_output("no summary here")["passed"] == 0


def test_build_result_pass_and_fail():
    ok = build_result("t", "A", 0, "2 passed in 0.01s", 0.5)
    assert ok.passed and ok.status == "ok" and ok.pass_rate == 1.0
    bad = build_result("t", "B", 1, FAILING_OUTPUT, 0.5)
    assert not bad.passed
    assert (bad.tests_passed, bad.tests_failed, bad.tests_total) == (3, 1, 4)
    assert bad.to_dict()["pass_rate"] == 0.75


def test_build_result_without_any_tests_is_error():
    result = build_result("t", "A", 2, "something exploded", 0.1)
    assert result.status == "error"
    assert not result.passed
    assert result.errors == ["something exploded"]


def test_zero_tests_never_counts_as_pass():
    assert not build_result("t", "A", 0, "no tests ran in 0.01s", 0.1).passed


def test_docker_command_is_sandboxed():
    command = docker_command("/tmp/x", "cre-test")
    assert command[:3] == ["docker", "run", "--rm"]
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "/tmp/x:/work:ro" in command
    assert command[command.index("--memory") + 1] == "256m"


def test_local_backend_runs_both_candidates(task):
    good = run_candidate(task, "A", backend="local")
    bad = run_candidate(task, "B", backend="local")
    assert good.passed and good.tests_total == 2
    assert not bad.passed
    assert (bad.tests_passed, bad.tests_failed) == (1, 1)
    assert any("test_add" in error for error in bad.errors)


def test_syntax_error_candidate_fails_cleanly(tmp_path):
    path = make_task(tmp_path, a="def add(a, b:\n")
    result = run_candidate(load_task(path), "A", backend="local")
    assert not result.passed
    assert result.tests_passed == 0
    assert result.errors


def test_timeout_is_recorded(tmp_path):
    path = make_task(tmp_path, a="import time\ntime.sleep(30)\n")
    result = run_candidate(load_task(path), "A", backend="local", timeout=1)
    assert result.status == "timeout"
    assert not result.passed
    assert "timed out" in result.errors[0]


def test_unknown_backend_and_candidate(task):
    with pytest.raises(ValueError):
        run_candidate(task, "A", backend="vm")
    with pytest.raises(ValueError):
        run_candidate(task, "C", backend="local")


def test_run_all_local(task):
    results = run_all([task], backend="local")
    assert [(r.candidate, r.passed) for r in results] == [("A", True), ("B", False)]


def test_run_all_requires_docker(task, monkeypatch):
    monkeypatch.setattr(runner, "docker_available", lambda: False)
    with pytest.raises(RunnerError, match="Docker is not available"):
        run_all([task], backend="docker")


def test_docker_infrastructure_failure_raises(task, monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 125, stdout="", stderr="daemon gone")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    with pytest.raises(RunnerError, match="daemon gone"):
        run_candidate(task, "A", backend="docker")


@pytest.mark.docker
@pytest.mark.skipif(not docker_available(), reason="Docker daemon not available")
def test_docker_backend_end_to_end(task):
    results = run_all([task], backend="docker")
    assert [(r.candidate, r.passed) for r in results] == [("A", True), ("B", False)]
    assert results[0].tests_total == 2
