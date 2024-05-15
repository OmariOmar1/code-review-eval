# Review Rubric

Each candidate is scored from 1 to 5 on four criteria. The judge reads the
task prompt and both candidates' source code. It does **not** see the test
results, so every score is a prediction made from the code alone.

Scale used for every criterion:

| Score | Meaning |
|-------|---------|
| 5 | Excellent. Nothing meaningful to improve. |
| 4 | Good. Minor issues only. |
| 3 | Acceptable. Noticeable gaps, but the core is sound. |
| 2 | Weak. Significant problems. |
| 1 | Poor. Fails the criterion. |

## 1. Correctness

Does the code do what the prompt asks for ordinary, well-formed input?

**Good (5)** - sorts before merging, so any input order works:

```python
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
```

**Bad (1)** - assumes the input is already sorted, which the prompt does not
promise, and so returns wrong answers for most inputs:

```python
def merge_intervals(intervals):
    result = []
    for interval in intervals:
        if result and interval[0] <= result[-1][1]:
            result[-1][1] = max(result[-1][1], interval[1])
        else:
            result.append(interval)
    return result
```

## 2. Readability

Can another developer understand and change the code quickly? Look at naming,
structure, docstrings, and line length. Do not reward comments that restate
the code.

**Good (5)** - descriptive names, one idea per line, a docstring that says
what is returned:

```python
def two_sum(nums, target):
    """Return indices (i, j), i < j, whose values add up to target."""
    seen = {}
    for index, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return (seen[complement], index)
        seen[value] = index
    return None
```

**Bad (1)** - single-letter names, statements crammed together, no hint of
intent:

```python
def chunk(l, n):
    if n < 1: raise ValueError(n)
    r = []; i = 0
    while i < len(l):
        r.append(l[i:i + n]); i += n
    return r
```

## 3. Edge case handling

Does the code deal with boundary and invalid input the prompt mentions or
implies: empty input, a single element, bad arguments, values at the limits?

**Good (5)** - rejects anything that is not entirely made of valid groups:

```python
def parse_duration(text):
    cleaned = text.strip().lower()
    if not FULL.fullmatch(cleaned):
        raise ValueError(f"invalid duration: {text!r}")
    return sum(int(n) * SECONDS[u] for n, u in GROUP.findall(cleaned))
```

**Bad (1)** - silently returns `0` for an empty string or garbage, and
ignores stray characters:

```python
def parse_duration(text):
    total = 0
    for amount, unit in re.findall(r"(\d+)([dhms])", text.lower()):
        total += int(amount) * units[unit]
    return total
```

## 4. Test quality

How good are the tests the author shipped with the solution? In this project
candidates carry their own tests as doctests. Score how well they cover the
behaviour, including edge cases and error paths, not how many there are.

**Good (5)** - covers the normal path, a boundary, and the miss case:

```python
def binary_search(items, target):
    """
    >>> binary_search([1, 3, 5, 7, 9], 9)
    4
    >>> binary_search([1, 3, 5], 10)
    -1
    >>> binary_search([], 1)
    -1
    """
```

**Bad (1)** - no tests at all, or a single happy-path example that would pass
for a badly broken implementation:

```python
def top_words(text, n):
    """
    >>> top_words("a b a", 1)
    [('a', 2)]
    """
```

## Picking a winner

The winner is the candidate a careful reviewer would merge. Correctness
outweighs everything else: polished code that returns wrong answers loses to
plain code that works. When both are equally correct, prefer the one that
handles edge cases better, then the more readable one. The judge must always
pick `A` or `B` and give a single-sentence reason.
