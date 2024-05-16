# Decisions

Choices made while building this, with the reasoning.

## Tasks

- **One directory per task** with `prompt.md`, `test_solution.py`,
  `candidate_a.py`, `candidate_b.py`. Tests import from `solution`; the runner
  copies the candidate under test to `solution.py`. No metadata file: the task
  id is the directory name, and which candidate is "better" is derived from
  the tests rather than declared.
- **The better candidate is not always A.** Tests favour A in four tasks and
  B in four, so a judge that always answers "A" scores 50%.
- **Two intentional ties** (`01_two_sum`, `04_roman_to_int`): both candidates
  pass every test and differ only in readability and efficiency. They show
  what the judge prefers when correctness does not separate the candidates,
  and they are excluded from the agreement rate.
- **One trap** (`09_chunk`): terse but correct versus polished but buggy.
- **Root pytest only collects `tests/`** (`testpaths` in `pyproject.toml`).
  The task test files cannot be collected directly because `solution` only
  exists inside the runner's temp directory.

## Runner

- **One container per candidate** via the `docker` CLI rather than the Docker
  SDK, to avoid an extra dependency. Flags: `--network none`, `--read-only`,
  `--tmpfs /tmp`, `--memory 256m`, `--cpus 1`, `--pids-limit 128`, code
  mounted read-only, non-root user in the image.
- **Image is built on first use** from `docker/Dockerfile` (python:3.12-slim
  plus a pinned pytest) and reused afterwards. `--rebuild` forces a rebuild.
- **Results are parsed from pytest's terminal summary** (`-q -rfE --tb=line`)
  instead of a JUnit file, because the mount is read-only and the summary
  already has the counts, the duration and one line per failure.
- **Two timings are stored.** `runtime_s` is pytest's own reported duration;
  `wall_time_s` includes container start-up. Compare candidates on
  `runtime_s`.
- **Timeout is 60 s per candidate**, enforced by the host, which then kills
  the container. A timeout is recorded as `status: "timeout"` and a fail.
- **Zero collected tests is never a pass**, even with exit code 0.
- **Docker's own exit codes (125-127) abort the run** instead of being
  recorded as a candidate failure, so infrastructure problems cannot be
  mistaken for bad code.
- **A `local` backend exists** (pytest in a subprocess). It lets the unit
  tests exercise the real runner logic without Docker. It is never chosen
  automatically; if Docker is missing the default run fails with a message.

## Rubric and judge

- **"Test quality" is scored on doctests.** The reference tests belong to the
  task, not to a candidate, so there would otherwise be nothing to score.
  Candidates therefore carry their own tests as doctests.
- **The judge does not see test results.** Otherwise agreement with the tests
  would be circular.
- **The judge must pick A or B.** No "tie" verdict, so every row is a usable
  preference. The objective side can still be a tie.
- **The judge is static analysis, not a lookup table.** It scores from
  docstrings, identifier length, line length, nesting, guard clauses and
  doctest count, with correctness weighted double. It can be wrong, and is on
  `09_chunk`. A judge that secretly read the test results would make the
  agreement number meaningless.
- **Tie-break**: equal totals go to the shorter file, then to A.
- **Verdicts are validated before they are written**: scores must be integers
  from 1 to 5 on all four criteria and the winner must be A or B.

## Analysis

- **Objective winner = more tests passed**, not all-or-nothing pass/fail, so a
  candidate failing one test beats one failing five.
- **Agreement rate is computed over decisive tasks only.** Ties are reported
  separately.
- **A Wilson interval is reported** next to the rate because the sample is
  tiny and a bare percentage would overstate what is known.
- **A second, stricter number is reported**: whether the judge's correctness
  scores order the candidates the same way the tests do, ties included.

## Repository

- **Generated outputs from one run are committed** (`preferences.jsonl`,
  `report.md`, `results/test_results.json`) so the README numbers can be
  checked without running anything. Timings in the results file will differ
  between machines.
- **CI has two jobs**: unit tests on Python 3.10 and 3.12, and the full
  pipeline in Docker.
