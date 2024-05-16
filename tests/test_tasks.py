import ast

import pytest

from code_review_eval.tasks import REQUIRED_FILES, load_task, load_tasks

from .conftest import TASKS_DIR


def test_repository_has_ten_tasks():
    tasks = load_tasks(TASKS_DIR)
    assert len(tasks) == 10
    assert [t.task_id for t in tasks] == sorted(t.task_id for t in tasks)


@pytest.mark.parametrize("path", sorted(TASKS_DIR.iterdir()), ids=lambda p: p.name)
def test_task_is_well_formed(path):
    task = load_task(path)
    assert task.prompt.startswith("# ")
    assert "from solution import" in task.tests
    assert task.candidates["A"] != task.candidates["B"]
    for source in (task.tests, *task.candidates.values()):
        ast.parse(source)


def test_load_task_reads_files(task):
    assert task.task_id == "t01_add"
    assert set(task.candidates) == {"A", "B"}
    assert task.candidate_path("A").name == "candidate_a.py"


@pytest.mark.parametrize("missing", REQUIRED_FILES)
def test_missing_file_is_reported(tasks_dir, missing):
    (tasks_dir / "t01_add" / missing).unlink()
    with pytest.raises(FileNotFoundError, match=missing):
        load_tasks(tasks_dir)


def test_missing_tasks_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tasks(tmp_path / "nope")
