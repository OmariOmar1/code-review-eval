from pathlib import Path

import pytest

from code_review_eval.tasks import load_task

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"

GOOD = '''def add(a, b):
    """Add two numbers.

    >>> add(1, 2)
    3
    """
    return a + b
'''
BAD = "def add(a, b):\n    return a - b\n"
TESTS = '''from solution import add


def test_add():
    assert add(1, 2) == 3


def test_add_zero():
    assert add(0, 0) == 0
'''


def make_task(root, name="t01_add", a=GOOD, b=BAD, tests=TESTS):
    path = root / name
    path.mkdir(parents=True)
    (path / "prompt.md").write_text("# Add\n\nWrite `add(a, b)`.\n")
    (path / "test_solution.py").write_text(tests)
    (path / "candidate_a.py").write_text(a)
    (path / "candidate_b.py").write_text(b)
    return path


@pytest.fixture
def tasks_dir(tmp_path):
    root = tmp_path / "tasks"
    make_task(root)
    return root


@pytest.fixture
def task(tasks_dir):
    return load_task(tasks_dir / "t01_add")
