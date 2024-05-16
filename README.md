# code-review-eval

[![CI](https://github.com/OmariOmar1/code-review-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/OmariOmar1/code-review-eval/actions/workflows/ci.yml)

Compares two candidate solutions per coding task, records which one a judge
prefers and why, and checks those preferences against what the tests say.

## Problem

Code review is mostly reading. A reviewer forms a preference between two
solutions from how the code looks: names, structure, guard clauses, whether
there are tests. This project asks how far that gets you. If you score two
solutions on a review rubric without running them, how often do you end up
preferring the one that actually works?

## Approach

```
tasks/  ──►  runner (Docker)  ──►  results/test_results.json ─┐
   │                                                          ├─►  analysis  ──►  report.md
   └─────►  judge (heuristics) ──►  preferences.jsonl ────────┘
```

1. **Tasks** (`tasks/`). Ten small Python problems. Each directory holds a
   `prompt.md`, a pytest file, and two candidates of differing quality. The
   stronger candidate is A in some tasks and B in others. Two tasks are
   deliberate ties on the tests (the candidates differ only in quality), and
   one (`09_chunk`) pairs ugly-but-correct code against polished-but-buggy
   code to see whether the judge is swayed by presentation.
2. **Runner** (`code_review_eval/runner.py`). Copies one candidate and the
   task's tests into a temp directory and runs pytest in a throwaway
   container: no network, read-only mount, 256 MB memory, one CPU, 60 s
   timeout. It records pass/fail, per-test counts, runtime, and the failing
   test lines.
3. **Rubric** (`RUBRIC.md`). Four criteria scored 1 to 5 (correctness,
   readability, edge case handling, test quality), each with a good and a bad
   example.
4. **Judge** (`code_review_eval/judge.py`). Scores both candidates on the
   rubric from static signals (docstrings, naming, guard clauses, doctest
   count) and picks a winner with a one-sentence reason. It sees the code but
   **not** the test results.
5. **Analysis** (`code_review_eval/analysis.py`). The objective winner of a
   task is the candidate that passes more tests. Agreement is the share of
   decisive (non-tie) tasks where the judge picked that candidate.

## Usage

Requires Python 3.10+ and a running Docker daemon.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m code_review_eval all          # everything

python -m code_review_eval run-tests    # -> results/test_results.json
python -m code_review_eval judge        # -> preferences.jsonl
python -m code_review_eval analyze      # -> report.md

python -m pytest                        # tests for the pipeline itself
```

`--backend local` runs pytest in a plain subprocess instead of Docker; it is
meant for development only and gives no isolation.

## Results

The committed `preferences.jsonl`, `report.md` and `results/test_results.json`
come from one run with the Docker backend.

| | |
|---|---|
| Tasks | 10 |
| Decisive tasks (one candidate passes more tests) | 8 |
| Objective ties | 2 |
| Judge picked the objectively better candidate | **7 of 8 (88%)** |
| 95% Wilson interval | 53% to 98% |
| Correctness scores ordered the same way as the tests | 4 of 10 |

The one disagreement is `09_chunk`: the judge preferred the candidate with
type hints, a docstring and doctests, which silently drops the final partial
chunk and fails 2 of 8 tests. That is exactly the failure the task was
written to expose.

The headline number flatters the judge. Its correctness *score* tracks the
tests in only 4 of 10 tasks; it reaches 7 of 8 on the final pick because in
this task set the better-working candidate usually also has more doctests and
guard clauses.

## Limitations

- **Ten tasks.** The confidence interval on 7 of 8 spans 53% to 98%. Nothing
  here supports a claim finer than "mostly agrees".
- **Tests are the ground truth, and they are mine.** "Objective" means
  "passes more of the tests I wrote". A candidate can pass every test and
  still be wrong, and partial credit by test count treats all tests as equally
  important.
- **Hand-written candidates.** The buggy candidates contain the kinds of bugs
  I thought of, and the tasks are far smaller than real review work.
- **The judge never reads the logic.** It counts surface signals. It cannot
  tell a correct loop bound from a wrong one.
- **Ties are dropped.** Two tasks have no objective winner, so the judge's
  preference there is recorded but never checked. Runtime is measured but not
  used to decide a winner.
- **Test quality is judged on doctests.** Candidates carry their own tests as
  doctests so there is something to score. That is a narrow stand-in for a
  real test suite.
- **The sandbox is basic.** Containers have no network, a read-only mount and
  resource limits, which is adequate for trusted toy tasks. It is not a
  hardened sandbox for hostile code.

See [DECISIONS.md](DECISIONS.md) for the design choices behind these.
