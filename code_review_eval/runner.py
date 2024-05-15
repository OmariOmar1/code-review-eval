"""Run candidate solutions against their task tests.

The default backend runs every candidate in a throwaway Docker container with
no network and a read-only copy of the code. A ``local`` backend runs pytest
in a subprocess instead; it exists for development and for testing the
pipeline itself and gives no isolation.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .tasks import CANDIDATES

IMAGE = "code-review-eval-runner:latest"
DOCKERFILE_DIR = Path(__file__).resolve().parent.parent / "docker"
DEFAULT_TIMEOUT = 60
PYTEST_ARGS = ["-q", "-rfE", "--tb=line", "-p", "no:cacheprovider", "test_solution.py"]
MAX_ERRORS = 10

_COUNT = re.compile(r"(\d+) (passed|failed|errors?)\b")
_DURATION = re.compile(r"\bin (\d+(?:\.\d+)?)s\b")
_FAILURE = re.compile(r"^(?:FAILED|ERROR) (.+)$", re.MULTILINE)


class RunnerError(RuntimeError):
    """The execution backend itself is unavailable or misbehaving."""


@dataclass
class RunResult:
    """Outcome of running one candidate against its task's tests."""

    task_id: str
    candidate: str
    status: str  # "ok", "timeout" or "error" (tests could not be run at all)
    passed: bool
    tests_passed: int = 0
    tests_failed: int = 0
    tests_total: int = 0
    runtime_s: float = 0.0
    wall_time_s: float = 0.0
    exit_code: int = -1
    errors: list = field(default_factory=list)

    @property
    def pass_rate(self):
        return self.tests_passed / self.tests_total if self.tests_total else 0.0

    def to_dict(self):
        data = asdict(self)
        data["pass_rate"] = round(self.pass_rate, 4)
        return data


def parse_pytest_output(output):
    """Pull counts, pytest's own duration and failure lines out of ``-q`` output."""
    summary = ""
    for line in reversed(output.strip().splitlines()):
        if _DURATION.search(line) and _COUNT.search(line):
            summary = line
            break
    counts = {"passed": 0, "failed": 0, "error": 0}
    for number, kind in _COUNT.findall(summary):
        counts[kind.rstrip("s") if kind.startswith("error") else kind] += int(number)
    duration = _DURATION.search(summary)
    return {
        "passed": counts["passed"],
        "failed": counts["failed"] + counts["error"],
        "runtime_s": float(duration.group(1)) if duration else 0.0,
        "errors": [m.strip() for m in _FAILURE.findall(output)][:MAX_ERRORS],
    }


def build_result(task_id, candidate, exit_code, output, wall_time):
    """Turn a finished pytest process into a ``RunResult``."""
    parsed = parse_pytest_output(output)
    total = parsed["passed"] + parsed["failed"]
    errors = parsed["errors"]
    if exit_code != 0 and not errors:
        tail = output.strip().splitlines()[-3:]
        errors = [" | ".join(tail)] if tail else [f"pytest exited with code {exit_code}"]
    return RunResult(
        task_id=task_id,
        candidate=candidate,
        status="ok" if total else "error",
        passed=exit_code == 0 and total > 0 and parsed["failed"] == 0,
        tests_passed=parsed["passed"],
        tests_failed=parsed["failed"],
        tests_total=total,
        runtime_s=parsed["runtime_s"],
        wall_time_s=round(wall_time, 3),
        exit_code=exit_code,
        errors=errors,
    )


def docker_available():
    """True when a Docker daemon can be reached."""
    if shutil.which("docker") is None:
        return False
    try:
        probe = subprocess.run(["docker", "info"], capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return probe.returncode == 0


def ensure_image(image=IMAGE, rebuild=False):
    """Build the runner image unless it already exists."""
    if not rebuild:
        inspect = subprocess.run(["docker", "image", "inspect", image], capture_output=True)
        if inspect.returncode == 0:
            return
    build = subprocess.run(
        ["docker", "build", "-t", image, str(DOCKERFILE_DIR)],
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        raise RunnerError(f"docker build failed:\n{build.stderr[-2000:]}")


def docker_command(workdir, name, image=IMAGE):
    """The ``docker run`` invocation used for one candidate."""
    return [
        "docker", "run", "--rm",
        "--name", name,
        "--network", "none",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "128",
        "--read-only",
        "--tmpfs", "/tmp",
        "--volume", f"{workdir}:/work:ro",
        "--workdir", "/work",
        image,
        "python", "-m", "pytest", *PYTEST_ARGS,
    ]


def _prepare_workdir(task, candidate):
    """Copy one candidate and the task tests into a fresh temp directory."""
    workdir = Path(tempfile.mkdtemp(prefix="cre-"))
    workdir.chmod(0o755)
    for name, content in (
        ("solution.py", task.candidates[candidate]),
        ("test_solution.py", task.tests),
    ):
        target = workdir / name
        target.write_text(content)
        target.chmod(0o644)
    return workdir


def run_candidate(task, candidate, backend="docker", timeout=DEFAULT_TIMEOUT):
    """Run one candidate of ``task`` and return its ``RunResult``."""
    if candidate not in CANDIDATES:
        raise ValueError(f"unknown candidate: {candidate!r}")
    workdir = _prepare_workdir(task, candidate)
    name = f"cre-{uuid.uuid4().hex[:12]}"
    if backend == "docker":
        command, cwd = docker_command(workdir, name), None
    elif backend == "local":
        command, cwd = [sys.executable, "-m", "pytest", *PYTEST_ARGS], workdir
    else:
        raise ValueError(f"unknown backend: {backend!r}")

    started = time.perf_counter()
    try:
        process = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        if backend == "docker":
            subprocess.run(["docker", "kill", name], capture_output=True)
        return RunResult(
            task_id=task.task_id,
            candidate=candidate,
            status="timeout",
            passed=False,
            wall_time_s=round(time.perf_counter() - started, 3),
            errors=[f"timed out after {timeout}s"],
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    wall_time = time.perf_counter() - started
    # 125-127 are docker's own failure codes (daemon error, bad command).
    if backend == "docker" and process.returncode in (125, 126, 127):
        raise RunnerError(f"docker run failed: {process.stderr.strip()[-500:]}")
    return build_result(
        task.task_id, candidate, process.returncode, process.stdout + process.stderr, wall_time
    )


def run_all(tasks, backend="docker", timeout=DEFAULT_TIMEOUT, rebuild=False):
    """Run both candidates of every task. Returns a list of ``RunResult``."""
    if backend == "docker":
        if not docker_available():
            raise RunnerError(
                "Docker is not available. Start the daemon or pass --backend local."
            )
        ensure_image(rebuild=rebuild)
    results = []
    for task in tasks:
        for candidate in CANDIDATES:
            results.append(run_candidate(task, candidate, backend=backend, timeout=timeout))
    return results
