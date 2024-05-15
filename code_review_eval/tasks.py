"""Loading of task directories."""

from dataclasses import dataclass
from pathlib import Path

CANDIDATES = ("A", "B")
REQUIRED_FILES = ("prompt.md", "test_solution.py", "candidate_a.py", "candidate_b.py")


@dataclass(frozen=True)
class Task:
    """One coding task: a prompt, its tests and two candidate solutions."""

    task_id: str
    path: Path
    prompt: str
    tests: str
    candidates: dict

    def candidate_path(self, label):
        return self.path / f"candidate_{label.lower()}.py"


def load_task(path):
    """Load a single task directory, failing loudly if a file is missing."""
    path = Path(path)
    missing = [name for name in REQUIRED_FILES if not (path / name).is_file()]
    if missing:
        raise FileNotFoundError(f"task {path.name} is missing: {', '.join(missing)}")
    return Task(
        task_id=path.name,
        path=path,
        prompt=(path / "prompt.md").read_text(),
        tests=(path / "test_solution.py").read_text(),
        candidates={
            label: (path / f"candidate_{label.lower()}.py").read_text()
            for label in CANDIDATES
        },
    )


def load_tasks(tasks_dir):
    """Load every task under ``tasks_dir``, sorted by directory name."""
    tasks_dir = Path(tasks_dir)
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"tasks directory not found: {tasks_dir}")
    task_dirs = sorted(p for p in tasks_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    return [load_task(path) for path in task_dirs]
