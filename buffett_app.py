"""Streamlit app for Lab 18: Buffett-style analysis from SEC EDGAR 10-K facts."""

from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st


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
    """Download SEC JSON with the identifying User-Agent SEC requires."""
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(f"SEC EDGAR request failed: {error}") from error


@st.cache_data(ttl=3600, show_spinner=False)
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
    """Return one latest-filed 10-K observation for each fiscal-year end."""
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
    """Choose the first available tag for one fiscal-year-end date."""
    for tag in METRICS[metric]:
        for item in annual_facts(company_facts, tag, metric in FLOW_METRICS):
            if item["end"] == end:
                return float(item["val"]), tag
    return None, "not found"


def fiscal_year_ends(company_facts: dict) -> list[str]:
    """Find the five latest annual fiscal year ends visible in required facts."""
    ends: set[str] = set()
    for metric, tags in METRICS.items():
        for tag in tags:
            ends.update(item["end"] for item in annual_facts(company_facts, tag, metric in FLOW_METRICS))
    return sorted(ends)[-5:]


def display_value(value: float | None) -> str:
    return "not found" if value is None else f"{value / 1_000_000:,.0f}"


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


def checks_for(rows: list[dict]) -> list[dict[str, str]]:
    roe = [row["ROE"] for row in rows]
    owner_earnings = [row["Owner earnings"] for row in rows]
    growing = "not known"
    if len(owner_earnings) == 5 and all(value is not None for value in owner_earnings):
        growing = "pass" if float(owner_earnings[-1]) > float(owner_earnings[0]) else "fail"
    return [
        {"Buffett check": "ROE of 15% or more every year", "Result": all_or_unknown(roe, lambda value: value >= 0.15)},
        {"Buffett check": "Owner earnings positive every year", "Result": all_or_unknown(owner_earnings, lambda value: value > 0)},
        {"Buffett check": "Owner earnings grew, first year to last", "Result": growing},
    ]


def table_for_display(rows: list[dict]) -> pd.DataFrame:
    output = []
    for row in rows:
        output.append({
            "FY end": row["FY end"],
            "Revenue ($m)": display_value(row["Revenue"]),
            "Net income ($m)": display_value(row["Net income"]),
            "Operating cash flow ($m)": display_value(row["Operating cash flow"]),
            "Capital spending ($m)": display_value(row["Capital spending"]),
            "Equity ($m)": display_value(row["Equity"]),
            "ROE": "not known" if row["ROE"] is None else f"{float(row['ROE']) * 100:.1f}%",
            "Owner earnings ($m)": display_value(row["Owner earnings"]),
        })
    return pd.DataFrame(output)


def printed_numbers(rows: list[dict]) -> set[float]:
    allowed: set[float] = {15.0}
    for row in rows:
        allowed.update(float(part) for part in re.findall(r"\d+", str(row["FY end"])))
        for metric in (*METRICS.keys(), "Owner earnings"):
            value = row[metric]
            if value is not None:
                millions = float(value) / 1_000_000
                allowed.update({round(millions, 1), round(millions, 0)})
        if row["ROE"] is not None:
            allowed.add(round(float(row["ROE"]) * 100, 1))
    return allowed


def unprinted_memo_numbers(memo: str, rows: list[dict]) -> list[str]:
    allowed = printed_numbers(rows)
    flagged = []
    for match in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?", memo):
        text = match.group()
        number = float(text.rstrip("%").replace(",", ""))
        if not any(abs(number - value) < 0.051 for value in allowed):
            flagged.append(text)
    return sorted(set(flagged), key=lambda item: (float(item.rstrip("%").replace(",", "")), item))


st.set_page_config(page_title="Buffett 10-K Investor", layout="wide")
st.title("Buffett 10-K Investor")
st.caption("Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.")

with st.sidebar:
    st.header("SEC request details")
    name = st.text_input("Your name")
    email = st.text_input("Your email")
    ticker = st.text_input("Ticker", value="COST").strip().upper()
    run_analysis = st.button("Analyze 10-K facts", type="primary")

st.write("This app uses 10-K facts, calculates metrics in code, and preserves missing values as not found or not known.")

if run_analysis:
    if not name.strip() or not email.strip():
        st.error("Enter your name and email so the SEC User-Agent identifies the request.")
    elif not ticker or not re.fullmatch(r"[A-Z.\-]{1,10}", ticker):
        st.error("Enter a valid ticker symbol.")
    else:
        with st.spinner(f"Downloading SEC EDGAR facts for {ticker}..."):
            try:
                rows = build_rows(load_company_facts(ticker, f"{name.strip()} {email.strip()}"))
            except RuntimeError as error:
                st.error(str(error))
                rows = []
        if len(rows) < 5:
            st.error("SEC EDGAR did not return five usable annual 10-K fiscal years for this ticker.")
        else:
            st.session_state["rows"] = rows
            st.session_state["ticker"] = ticker

rows = st.session_state.get("rows", [])
if rows:
    st.subheader(f"{st.session_state['ticker']} - five fiscal years from 10-K facts")
    st.caption("Dollar amounts are USD millions.")
    chart_data = pd.DataFrame({
        "FY end": [row["FY end"] for row in rows],
        "Owner earnings": [None if row["Owner earnings"] is None else float(row["Owner earnings"]) / 1_000_000 for row in rows],
        "Net income": [None if row["Net income"] is None else float(row["Net income"]) / 1_000_000 for row in rows],
    }).set_index("FY end")
    st.line_chart(chart_data, y=["Owner earnings", "Net income"])

    st.subheader("Calculated facts")
    st.dataframe(table_for_display(rows), hide_index=True, width="stretch")
    st.subheader("Buffett checks")
    st.dataframe(pd.DataFrame(checks_for(rows)), hide_index=True, width="stretch")

    st.subheader("Buffett memo")
    memo = st.text_area("Paste the Markdown memo produced from this script output", key="memo", height=180, placeholder="Paste your memo here. Do not include price data.")
    if memo.strip():
        st.markdown(memo)
        flagged = unprinted_memo_numbers(memo, rows)
        if flagged:
            st.warning("Numbers in the memo that were not printed by the script: " + ", ".join(f"'{number}'" for number in flagged))
        else:
            st.success("Every number in the memo was printed by the script.")
