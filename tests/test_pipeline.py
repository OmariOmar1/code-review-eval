import json

from code_review_eval.cli import main
from code_review_eval.judge import MockJudge, validate_verdict
from code_review_eval.pipeline import read_jsonl, run_judge, run_tests, write_jsonl

from .conftest import TASKS_DIR, make_task


def test_jsonl_round_trip(tmp_path):
    rows = [{"a": 1}, {"b": [1, 2]}]
    path = tmp_path / "nested" / "rows.jsonl"
    write_jsonl(path, rows)
    assert read_jsonl(path) == rows
    assert len(path.read_text().splitlines()) == 2


def test_run_tests_writes_results(tasks_dir, tmp_path):
    out = tmp_path / "out" / "results.json"
    results = run_tests(tasks_dir, out, backend="local")
    payload = json.loads(out.read_text())
    assert payload["backend"] == "local"
    assert payload["results"] == results
    assert {r["candidate"] for r in results} == {"A", "B"}
    for key in ("passed", "runtime_s", "errors", "tests_passed", "tests_total"):
        assert key in results[0]


def test_run_judge_writes_preferences(tasks_dir, tmp_path):
    out = tmp_path / "preferences.jsonl"
    rows = run_judge(tasks_dir, out, MockJudge())
    assert read_jsonl(out) == rows
    assert set(rows[0]) >= {"task_id", "scores", "winner", "reason"}
    validate_verdict(rows[0])


def cli_args(tmp_path, tasks):
    return [
        "--tasks", str(tasks),
        "--results", str(tmp_path / "results.json"),
        "--preferences", str(tmp_path / "preferences.jsonl"),
        "--report", str(tmp_path / "report.md"),
    ]


def test_cli_all_end_to_end(tasks_dir, tmp_path, capsys):
    make_task(tasks_dir, name="t02_add_again")
    code = main([*cli_args(tmp_path, tasks_dir), "all", "--backend", "local", "--judge", "mock"])
    assert code == 0
    assert len(read_jsonl(tmp_path / "preferences.jsonl")) == 2
    assert "**2 of 2**" in (tmp_path / "report.md").read_text()
    assert "agreement 2/2 (100%)" in capsys.readouterr().out


def test_cli_analyze_without_inputs_fails(tasks_dir, tmp_path, capsys):
    assert main([*cli_args(tmp_path, tasks_dir), "analyze"]) == 1
    assert "not found" in capsys.readouterr().err


def test_cli_reports_missing_tasks_dir(tmp_path, capsys):
    code = main([*cli_args(tmp_path, tmp_path / "missing"), "judge", "--judge", "mock"])
    assert code == 1
    assert "tasks directory not found" in capsys.readouterr().err


def test_full_pipeline_on_real_tasks_local(tmp_path):
    code = main([*cli_args(tmp_path, TASKS_DIR), "all", "--backend", "local", "--judge", "mock"])
    assert code == 0
    results = json.loads((tmp_path / "results.json").read_text())["results"]
    assert len(results) == 20
    assert all(r["status"] == "ok" for r in results)
    by_task = {}
    for r in results:
        by_task.setdefault(r["task_id"], []).append(r["passed"])
    # Every task has at least one candidate that passes its whole test file.
    assert all(any(passed) for passed in by_task.values())
    assert len(read_jsonl(tmp_path / "preferences.jsonl")) == 10
