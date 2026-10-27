# Lab 16 — Provenance Gate

Lab: [Lab 16 — Provenance Gate](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-10/lab-16-provenance-gate.md)

## Question

> On the day you would have traded, what did this data actually say — and how much of what you see now came later?

## Answer

The decision date was March 31, 2026. On that date, the knowable panel contained rows 1, 4, 5, 6, 9, and 12. The filter quarantined row 11 because it had no ticker, removed row 7 as an exact duplicate, excluded rows 3, 8, and 10 because they were published after the decision date, and replaced row 2 with its later knowable revision in row 4.

The data available on the trade date therefore said:

| Ticker | Latest knowable month | As-of signal |
|---|---|---:|
| AAA | February 2026 | +1.98% |
| BBB | February 2026 | -1.02% |
| CCC | February 2026 | +0.91% |

What I see now includes later information. Ignoring publication dates produces the naive signals of +5.83% for AAA in March, -5.15% for BBB in March, and +1.82% for CCC in February. AAA and BBB's March values were not published until April, after the trade date. CCC's later February revision was also published after the trade date.

So the hindsight gap is material: AAA appears to have gained 3.85 percentage points more than was knowable, BBB appears 4.13 percentage points worse, and CCC appears 0.91 percentage points stronger. A backtest using the naive column would use future releases and revisions, creating look-ahead bias rather than reproducing the information actually available when a trade could have been made.

The calculation is reproduced in [asof.py](asof.py) with `python asof.py`.

## Rule 4: revisions

In `apply_as_of_rules`, `latest_by_series = {}` creates a place to store one selected row for each `(ticker, month)` pair. The `for row in working:` loop checks every row that survived the first three rules. `key = (row["ticker"], row["month"])` groups two publications of the same ticker and measured month together. `prior = latest_by_series.get(key)` retrieves the row currently selected for that group. If there is no selected row yet, or if `parse_day(row["published"]) > parse_day(prior["published"])`, the current row replaces it. Because rule 3 has already removed publications after the decision date, the replacement is the latest publication that was actually knowable on the trade date. Finally, the code identifies and removes every other row from that ticker-month group.

**Partner question:** How did I define this variable?

```python
def print_funnel_rule(number, description, removed):
    row_numbers = ", ".join(str(row["row"]) for row in removed) or "none"
    print(f"Rule {number} — {description}: removed {len(removed)} row(s): {row_numbers}")
```

**My answer:** `print_funnel_rule` is a function defined with three inputs: `number` is the rule number, `description` is its text label, and `removed` is the list of rows that rule excluded. Inside the function, `row_numbers` is defined by looking at every dictionary in `removed`, taking its original `"row"` value, converting it to text, and joining the values with `", "`. For example, rows 3, 8, and 10 become `"3, 8, 10"`. If `removed` is empty, `join()` produces an empty string, so `or "none"` makes the displayed value `"none"` instead. The final `print` statement inserts those inputs and the computed variable into the funnel line.

## Point-in-Time Learning

### 1. What is look-ahead bias?

Look-ahead bias happens when an analysis or backtest uses information that was not available at the time a decision supposedly occurred. It makes a strategy appear to have used knowledge of the future, so its reported signals or performance are not realistic.

### 2. How does it work — event time, publication time, revision?

Event time is the period the data describes, such as February 2026 card spending. Publication time is when an analyst could first see that value, such as March 10 or March 25. A revision is a later publication that changes a value for a period already reported. A point-in-time analysis filters on publication time, not just event time: on March 31, it can use only publications made by March 31, and it must retain the latest version available by that date.

### 3. Explain it to your partner with AAA: why does +5.83% look better than anything you could have known?

For AAA, the latest knowable February value on March 31 was the March 25 revision of 103.0, compared with January's 101.0. The real-time signal was therefore `(103.0 / 101.0 - 1) × 100 = +1.98%`. The naive +5.83% signal instead compares March's 109.0 with February's 103.0. March's value was not published until April 10, after the March 31 decision date. It uses a future release, skips ahead one month, and makes AAA's momentum look 3.85 percentage points stronger than a trader could have known.

## Reflection

### 1. Which rule removed the row that mattered most?

Rule 3, which removes publications after the decision date, mattered most because it removed AAA row 3 and BBB row 8. Those rows contain March values but were not published until April 10, so they could not have informed a March 31 trade. Removing them prevents the apparent AAA +5.83% March signal and BBB -5.15% March signal from being treated as real-time information. Rule 4 also matters because it correctly selects AAA's March 25 revision in row 4 over the older row 2, but rule 3 is what blocks the future month from entering the decision.

### 2. What would a backtest built on the naive column claim?

A backtest built on the naive column would claim that a trader could have recognized a much stronger AAA signal (+5.83% rather than +1.98%), a much sharper BBB decline (-5.15% rather than -1.02%), and a stronger CCC increase (+1.82% rather than +0.91%). It could therefore make a momentum or relative-strength strategy look more timely and more profitable than it really was. Those results would be overstated because the backtest is using releases and revisions that arrived after the trade date.
