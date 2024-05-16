"""Glue between the runner, the judge and the output files."""

import json
from pathlib import Path

from .runner import run_all
from .tasks import load_tasks

RESULTS_FILE = "test_results.json"
PREFERENCES_FILE = "preferences.jsonl"


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def read_jsonl(path):
    lines = Path(path).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run_tests(tasks_dir, results_path, backend="docker", timeout=60, rebuild=False):
    """Run every candidate and write the raw test results."""
    tasks = load_tasks(tasks_dir)
    results = [r.to_dict() for r in run_all(tasks, backend=backend, timeout=timeout, rebuild=rebuild)]
    write_json(results_path, {"backend": backend, "results": results})
    return results


def run_judge(tasks_dir, preferences_path, judge):
    """Judge every task and write one preference row per task."""
    rows = [judge.judge(task).to_dict() for task in load_tasks(tasks_dir)]
    write_jsonl(preferences_path, rows)
    return rows
