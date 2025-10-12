# code-review-eval

[![CI](https://github.com/OmariOmar1/code-review-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/OmariOmar1/code-review-eval/actions/workflows/ci.yml)

Compares two candidate solutions per coding task, records which one a judge
prefers and why, and checks those preferences against what the tests say.

## Problem

Pairwise preference data ("solution A is better than solution B, because...")
is useful for training and evaluating code models, and an LLM judge is the
cheap way to produce it. But a judge that reads code can be fooled by code
that merely *looks* good. Before trusting its preferences you want to know
how often the judge's pick is the candidate that actually works.

This project is a small, self-contained harness for that question.

## Approach

```
tasks/  ──►  runner (Docker)  ──►  results/test_results.json ─┐
   │                                                          ├─►  analysis  ──►  report.md
   └─────►  judge (LLM or mock) ──►  preferences.jsonl ───────┘
```

1. **Tasks** (`tasks/`). Ten small Python problems. Each directory holds a
   `prompt.md`, a pytest file, and two candidates of differing quality. The
   stronger candidate is A in some tasks and B in others. Two tasks are
   deliberate ties on the tests (the candidates differ only in quality), and
   one (`09_chunk`) pairs ugly-but-correct code against polished-but-buggy
   code to see whether a judge is swayed by presentation.
2. **Runner** (`code_review_eval/runner.py`). Copies one candidate and the
   task's tests into a temp directory and runs pytest in a throwaway
   container: no network, read-only mount, 256 MB memory, one CPU, 60 s
   timeout. It records pass/fail, per-test counts, runtime, and the failing
   test lines.
3. **Rubric** (`RUBRIC.md`). Four criteria scored 1 to 5 (correctness,
   readability, edge case handling, test quality), each with a good and a bad
   example.
4. **Judge** (`code_review_eval/judge.py`). Scores both candidates on the
   rubric and picks a winner with a one-sentence reason. The judge sees the
   prompt and the code but **not** the test results.
   - `llm`: calls the Anthropic Messages API and asks for a JSON verdict,
     which is validated before it is written. The key is read from
     `ANTHROPIC_API_KEY` and the model name from `JUDGE_MODEL`.
   - `mock`: deterministic static-analysis heuristics (docstrings, naming,
     guard clauses, doctest count). No key or network needed.
5. **Analysis** (`code_review_eval/analysis.py`). The objective winner of a
   task is the candidate that passes more tests. Agreement is the share of
   decisive (non-tie) tasks where the judge picked that candidate.

## Usage

Requires Python 3.10+ and a running Docker daemon.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Everything, offline, with the mock judge
python -m code_review_eval all --judge mock

# With the LLM judge
export ANTHROPIC_API_KEY=...
export JUDGE_MODEL=...   # model name to judge with
python -m code_review_eval all --judge llm

# Individual stages
python -m code_review_eval run-tests            # -> results/test_results.json
python -m code_review_eval judge --judge mock   # -> preferences.jsonl
python -m code_review_eval analyze              # -> report.md

# Tests for the pipeline itself
python -m pytest
```

`--judge auto` (the default) uses the LLM judge when `ANTHROPIC_API_KEY` is
set and the mock judge otherwise. `--backend local` runs pytest in a plain
subprocess instead of Docker; it is meant for development only and gives no
isolation.

Each line of `preferences.jsonl` looks like this:

```json
{"task_id": "09_chunk",
 "scores": {"A": {"correctness": 3, "readability": 1, "edge_case_handling": 4, "test_quality": 1},
            "B": {"correctness": 4, "readability": 5, "edge_case_handling": 5, "test_quality": 5}},
 "winner": "B",
 "reason": "Candidate B scores higher on readability (5 vs 1) with a weighted total of 23 against 12.",
 "judge": "mock"}
```

## Results

The committed `preferences.jsonl`, `report.md` and `results/test_results.json`
come from one run with the Docker backend and the **mock** judge.

| | |
|---|---|
| Tasks | 10 |
| Decisive tasks (one candidate passes more tests) | 8 |
| Objective ties | 2 |
| Judge picked the objectively better candidate | **7 of 8 (88%)** |
| 95% Wilson interval | 53% to 98% |
| Correctness scores ordered the same way as the tests | 4 of 10 |

The one disagreement is `09_chunk`: the mock judge preferred the candidate
with type hints, a docstring and doctests, which silently drops the final
partial chunk and fails 2 of 8 tests. That is exactly the failure the task
was written to expose.

The headline number flatters the mock judge. Its correctness *score* tracks
the tests in only 4 of 10 tasks; it reaches 7 of 8 on the final pick because
in this task set the better-working candidate usually also has more doctests
and guard clauses. It is a baseline that keeps the pipeline runnable offline,
not a judge to rely on.

No LLM judge results are included. That path is covered by unit tests against
a stubbed client, but it has not been run against the live API in this
repository, so there is no number to report for it yet.

## Limitations

- **Ten tasks.** The confidence interval on 7 of 8 spans 53% to 98%. Nothing
  here supports a claim finer than "mostly agrees".
- **Tests are the ground truth, and they are mine.** "Objective" means
  "passes more of the tests I wrote". A candidate can pass every test and
  still be wrong, and partial credit by test count treats all tests as equally
  important.
- **Hand-written candidates.** The buggy candidates contain the kinds of bugs
  I thought of. Real model output fails in other ways, and the tasks are far
  smaller than real review work.
- **Ties are dropped.** Two tasks have no objective winner, so the judge's
  preference there (readability, runtime) is recorded but never checked.
  Runtime is measured but not used to decide a winner.
- **Fixed A/B order.** Candidates are always shown as A then B. The better
  one is split evenly between positions, but position bias in an LLM judge is
  not measured; that would need each pair judged in both orders.
- **Single judgment per task.** LLM judges are not deterministic. One call
  per task says nothing about variance between runs.
- **Test quality is judged on doctests.** Candidates carry their own tests as
  doctests so there is something to score. That is a narrow stand-in for a
  real test suite.
- **The sandbox is basic.** Containers have no network, a read-only mount and
  resource limits, which is adequate for trusted toy tasks. It is not a
  hardened sandbox for hostile code.

See [DECISIONS.md](DECISIONS.md) for the design choices behind these.
