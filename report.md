# Judge vs. Tests Report

- Judge: `mock`
- Test backend: `docker`
- Tasks: 10

## Headline

The judge picked the candidate that passes more tests in **7 of 8** decisive tasks (**88%**, 95% Wilson interval 53% to 98%).

2 task(s) were objective ties (both candidates pass the same number of tests) and are left out of the agreement rate.

The judge's correctness scores ranked the candidates the same way as the tests (including ties) in 4 of 10 tasks.

## Per task

| Task | A tests | B tests | Objective | Judge | Agree |
|------|---------|---------|-----------|-------|-------|
| 01_two_sum | 9/9 | 9/9 | tie | A | n/a |
| 02_is_palindrome | 6/8 | 8/8 | B | B | yes |
| 03_merge_intervals | 8/8 | 5/8 | A | A | yes |
| 04_roman_to_int | 12/12 | 12/12 | tie | A | n/a |
| 05_flatten | 4/8 | 8/8 | B | B | yes |
| 06_top_words | 8/8 | 6/8 | A | A | yes |
| 07_binary_search | 33/36 | 36/36 | B | B | yes |
| 08_parse_duration | 14/14 | 5/14 | A | A | yes |
| 09_chunk | 8/8 | 6/8 | A | B | **no** |
| 10_lru_cache | 7/9 | 9/9 | B | B | yes |

## Disagreements

- **09_chunk**: tests favour A (8/8 vs 6/8), judge picked B. Judge's reason: Candidate B scores higher on readability (5 vs 1) with a weighted total of 23 against 12.

## Pick distribution

| | A | B | Tie |
|---|---|---|-----|
| Tests | 4 | 4 | 2 |
| Judge | 5 | 5 | n/a |

## Mean judge scores

| Candidate | correctness | readability | edge case handling | test quality |
|---|---|---|---|---|
| A | 3.80 | 4.50 | 2.90 | 3.60 |
| B | 3.30 | 4.10 | 2.60 | 3.00 |
