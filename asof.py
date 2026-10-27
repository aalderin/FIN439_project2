"""Build a point-in-time index panel and compare it with a naive latest-data view.

Edit DECISION_DATE and ROWS below, then run: python asof.py
"""

from datetime import date, datetime


# ---------------------------------------------------------------------------
# Editable inputs
# ---------------------------------------------------------------------------

DECISION_DATE = "2026-03-31"

ROWS = [
    {"row": 1, "ticker": "AAA", "month": "2026-01", "published": "2026-02-10", "index": 101.0},
    {"row": 2, "ticker": "AAA", "month": "2026-02", "published": "2026-03-10", "index": 104.0},
    {"row": 3, "ticker": "AAA", "month": "2026-03", "published": "2026-04-10", "index": 109.0},
    {"row": 4, "ticker": "AAA", "month": "2026-02", "published": "2026-03-25", "index": 103.0},
    {"row": 5, "ticker": "BBB", "month": "2026-01", "published": "2026-02-10", "index": 98.0},
    {"row": 6, "ticker": "BBB", "month": "2026-02", "published": "2026-03-10", "index": 97.0},
    {"row": 7, "ticker": "BBB", "month": "2026-02", "published": "2026-03-10", "index": 97.0},
    {"row": 8, "ticker": "BBB", "month": "2026-03", "published": "2026-04-10", "index": 92.0},
    {"row": 9, "ticker": "CCC", "month": "2026-01", "published": "2026-02-10", "index": 110.0},
    {"row": 10, "ticker": "CCC", "month": "2026-02", "published": "2026-04-05", "index": 112.0},
    {"row": 11, "ticker": "", "month": "2026-02", "published": "2026-03-10", "index": 99.0},
    {"row": 12, "ticker": "CCC", "month": "2026-02", "published": "2026-03-10", "index": 111.0},
]


def parse_day(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_month(value):
    return datetime.strptime(value, "%Y-%m").date()


def previous_month(month):
    year, number = map(int, month.split("-"))
    if number == 1:
        return f"{year - 1}-12"
    return f"{year}-{number - 1:02d}"


def month_name(month):
    return parse_month(month).strftime("%B %Y")


def exact_key(row):
    """All data fields except the original row number define an exact duplicate."""
    return (row["ticker"], row["month"], row["published"], row["index"])


def print_funnel_rule(number, description, removed):
    row_numbers = ", ".join(str(row["row"]) for row in removed) or "none"
    print(f"Rule {number} — {description}: removed {len(removed)} row(s): {row_numbers}")


def apply_as_of_rules(rows, decision_day):
    """Apply the stated rules in order and return the surviving point-in-time panel."""
    working = list(rows)

    removed = [row for row in working if not row["ticker"].strip()]
    print_funnel_rule(1, "no ticker", removed)
    working = [row for row in working if row not in removed]

    seen = set()
    removed = []
    kept = []
    for row in working:
        key = exact_key(row)
        if key in seen:
            removed.append(row)
        else:
            seen.add(key)
            kept.append(row)
    print_funnel_rule(2, "exact duplicate", removed)
    working = kept

    removed = [row for row in working if parse_day(row["published"]) > decision_day]
    print_funnel_rule(3, "published after the decision date", removed)
    working = [row for row in working if row not in removed]

    latest_by_series = {}
    for row in working:
        key = (row["ticker"], row["month"])
        prior = latest_by_series.get(key)
        if prior is None or parse_day(row["published"]) > parse_day(prior["published"]):
            latest_by_series[key] = row
    survivors = set(row["row"] for row in latest_by_series.values())
    removed = [row for row in working if row["row"] not in survivors]
    print_funnel_rule(4, "superseded revision", removed)
    return [row for row in working if row["row"] in survivors]


def latest_publication_panel(rows):
    """Use every publication date, retaining the latest publication per ticker/month."""
    working = [row for row in rows if row["ticker"].strip()]
    seen = set()
    deduplicated = []
    for row in working:
        key = exact_key(row)
        if key not in seen:
            seen.add(key)
            deduplicated.append(row)

    latest_by_series = {}
    for row in deduplicated:
        key = (row["ticker"], row["month"])
        prior = latest_by_series.get(key)
        if prior is None or parse_day(row["published"]) > parse_day(prior["published"]):
            latest_by_series[key] = row
    return list(latest_by_series.values())


def print_panel(panel):
    print("Row  Ticker  Month measured  Published on  Index")
    for row in sorted(panel, key=lambda item: (item["ticker"], item["month"])):
        print(
            f"{row['row']:>3}  {row['ticker']:<6}  {row['month']:<14}  "
            f"{row['published']:<12}  {row['index']:.1f}"
        )


def print_signals(panel, title):
    print(f"\n{title}")
    by_ticker = {}
    for row in panel:
        by_ticker.setdefault(row["ticker"], {})[row["month"]] = row

    for ticker in sorted(by_ticker):
        series = by_ticker[ticker]
        latest = max(series, key=parse_month)
        prior = series.get(previous_month(latest))
        if prior is None:
            print(f"{ticker}: unavailable (no {month_name(previous_month(latest))} observation)")
            continue
        change = (series[latest]["index"] / prior["index"] - 1.0) * 100.0
        print(f"{ticker}: {change:+.2f}% in {month_name(latest)}")


def main():
    decision_day = parse_day(DECISION_DATE)
    print(f"Decision date: {decision_day.isoformat()}")
    print("\nRow funnel")
    as_of_panel = apply_as_of_rules(ROWS, decision_day)

    print("\nAs-of panel")
    print_panel(as_of_panel)
    print_signals(as_of_panel, "\nAs-of signals")

    naive_panel = latest_publication_panel(ROWS)
    print_signals(
        naive_panel,
        "Naive signals (latest publication for every row; publication date ignored)",
    )


if __name__ == "__main__":
    main()
