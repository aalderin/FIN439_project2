"""Print Buffett-style 10-K facts from SEC EDGAR for one ticker."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
METRICS = {
    "Revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "Net income": ("NetIncomeLoss",),
    "Operating cash flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "Capital spending": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ),
    "Equity": ("StockholdersEquity",),
}
FLOW_METRICS = {"Revenue", "Net income", "Operating cash flow", "Capital spending"}


def sec_json(url: str, user_agent: str) -> dict:
    """Download SEC JSON using the identifying User-Agent SEC requires."""
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(f"SEC EDGAR request failed: {error}") from error


def load_company_facts(ticker: str, user_agent: str) -> dict:
    ticker_rows = sec_json(TICKERS_URL, user_agent)
    matches = [
        record for record in ticker_rows.values()
        if record.get("ticker", "").upper() == ticker.upper()
    ]
    if not matches:
        raise RuntimeError(f"No SEC CIK was found for {ticker.upper()}.")
    cik = int(matches[0]["cik_str"])
    return sec_json(FACTS_URL.format(cik=cik), user_agent)


def annual_facts(company_facts: dict, tag: str, flow: bool) -> list[dict]:
    """Select one latest-filed, annual 10-K fact for each fiscal-year end."""
    facts = company_facts.get("facts", {}).get("us-gaap", {}).get(tag, {})
    candidates = facts.get("units", {}).get("USD", [])
    selected: dict[str, dict] = {}

    for item in candidates:
        if item.get("form") != "10-K" or item.get("fp") != "FY" or not item.get("end"):
            continue
        if flow:
            if not item.get("start"):
                continue
            start = datetime.fromisoformat(item["start"]).date()
            end = datetime.fromisoformat(item["end"]).date()
            if not 300 <= (end - start).days <= 380:
                continue
        prior = selected.get(item["end"])
        if prior is None or item.get("filed", "") > prior.get("filed", ""):
            selected[item["end"]] = item
    return list(selected.values())


def choose_metric(company_facts: dict, metric: str, end: str) -> tuple[float | None, str]:
    """Use the first available tag in the metric's required preference order."""
    for tag in METRICS[metric]:
        for item in annual_facts(company_facts, tag, metric in FLOW_METRICS):
            if item["end"] == end:
                return float(item["val"]), tag
    return None, "not found"


def fiscal_year_ends(company_facts: dict) -> list[str]:
    ends: set[str] = set()
    for metric, tags in METRICS.items():
        for tag in tags:
            ends.update(item["end"] for item in annual_facts(company_facts, tag, metric in FLOW_METRICS))
    return sorted(ends)[-5:]


def build_rows(company_facts: dict) -> list[dict]:
    rows = []
    for end in fiscal_year_ends(company_facts):
        row: dict[str, object] = {"FY end": end}
        for metric in METRICS:
            row[metric], row[f"{metric} tag"] = choose_metric(company_facts, metric, end)
        income, equity = row["Net income"], row["Equity"]
        ocf, capex = row["Operating cash flow"], row["Capital spending"]
        row["ROE"] = float(income) / float(equity) if income is not None and equity is not None and float(equity) > 0 else None
        row["Owner earnings"] = float(ocf) - float(capex) if ocf is not None and capex is not None else None
        rows.append(row)
    return rows


def all_or_unknown(values: list[float | None], predicate) -> str:
    if len(values) != 5 or any(value is None for value in values):
        return "not known"
    return "pass" if all(predicate(float(value)) for value in values) else "fail"


def checks_for(rows: list[dict]) -> list[tuple[str, str]]:
    roe = [row["ROE"] for row in rows]
    owner_earnings = [row["Owner earnings"] for row in rows]
    growing = "not known"
    if len(owner_earnings) == 5 and all(value is not None for value in owner_earnings):
        growing = "pass" if float(owner_earnings[-1]) > float(owner_earnings[0]) else "fail"
    return [
        ("ROE of 15% or more every year", all_or_unknown(roe, lambda value: value >= 0.15)),
        ("Owner earnings positive every year", all_or_unknown(owner_earnings, lambda value: value > 0)),
        ("Owner earnings grew, first year to last", growing),
    ]


def money(value: float | None) -> str:
    return "not found" if value is None else f"{value / 1_000_000:,.0f}"


def roe(value: float | None) -> str:
    return "not known" if value is None else f"{value * 100:.1f}%"


def print_results(ticker: str, rows: list[dict]) -> None:
    print(f"{ticker.upper()} - SEC EDGAR 10-K facts (USD millions)")
    for row in rows:
        print(f"\nFY end: {row['FY end']}")
        for metric in METRICS:
            print(f"  {metric}: {money(row[metric])} | XBRL tag: {row[f'{metric} tag']}")
        print(f"  ROE: {roe(row['ROE'])}")
        print(f"  Owner earnings: {money(row['Owner earnings'])}")

    print("\nBuffett checks")
    for label, result in checks_for(rows):
        print(f"  {label}: {result}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Buffett-style 10-K facts from SEC EDGAR.")
    parser.add_argument("ticker", help="Stock ticker, for example COST")
    parser.add_argument("--name", required=True, help="Your name for the SEC User-Agent")
    parser.add_argument("--email", required=True, help="Your email for the SEC User-Agent")
    args = parser.parse_args()

    try:
        rows = build_rows(load_company_facts(args.ticker.upper(), f"{args.name} {args.email}"))
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    if len(rows) != 5:
        raise SystemExit("SEC EDGAR did not return five usable annual 10-K fiscal years for this ticker.")
    print_results(args.ticker, rows)


if __name__ == "__main__":
    main()
