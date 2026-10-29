# Lab 17 — Point in Time

## R — the data, real and live

| Series | What it is | FRED page |
| --- | --- | --- |
| BAA | Moody's Baa corporate bond yield, monthly | <https://fred.stlouisfed.org/series/BAA> |
| FEDFUNDS | Effective federal funds rate, monthly | <https://fred.stlouisfed.org/series/FEDFUNDS> |
| DGS10 | 10-year Treasury yield, daily | <https://fred.stlouisfed.org/series/DGS10> |
| MORTGAGE30US | 30-year fixed mortgage rate, weekly | <https://fred.stlouisfed.org/series/MORTGAGE30US> |
| Yours | 10-year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity, daily | <https://fred.stlouisfed.org/series/T10Y2Y> |

## FRED series

- **Series:** 10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity
- **ID:** `T10Y2Y`
- **Page address:** <https://fred.stlouisfed.org/series/T10Y2Y> (the final code is `T10Y2Y`)
- **Units:** Percent, Not Seasonally Adjusted
- **Frequency:** Daily
- **Release:** Interest Rate Spreads

I chose this external yield-curve indicator because changes in the 10-year minus 2-year Treasury spread can affect the Treasury, investment-grade bond, and global-equity sleeves in Project 2, without using the funds' own prices.

## Data card — T10Y2Y

- **Source and link:** Federal Reserve Bank of St. Louis, FRED — [T10Y2Y](https://fred.stlouisfed.org/series/T10Y2Y). FRED calculates the spread from the U.S. Treasury's 10-year and 2-year constant-maturity Treasury yields.
- **What it measures:** The 10-year Treasury constant-maturity yield minus the 2-year Treasury constant-maturity yield. A positive value means the 10-year yield is above the 2-year yield.
- **Units:** Percent, not seasonally adjusted.
- **Frequency and publication lag:** Daily. The FRED page showed the 28 October 2026 observation updated at 4:03 PM CDT on 28 October, with the next release scheduled for 29 October. I will treat an observation as usable only after it appears in the ALFRED vintage for the decision date, rather than assuming it was available at the market open.
- **Revisions:** FRED states that all data are subject to revision. Although this daily market-rate series should have little publication lag, Project 2 must use the ALFRED value available on each decision date and let the app's revised-count field test for changed historical values.
- **Download date:** 29 October 2026.

### Three values checked against the FRED page

| Observation date | T10Y2Y value (percent) |
| --- | ---: |
| 2026-10-28 | 0.38 |
| 2026-10-27 | 0.29 |
| 2026-10-26 | 0.32 |

### Partner attack

**Field my partner trusts least:** Units.

**My two-sentence answer:** The FRED page labels T10Y2Y as “Percent, Not Seasonally Adjusted” and defines it as the 10-year Treasury yield minus the 2-year Treasury yield, so the 0.38 observation represents a 0.38-percentage-point yield-curve spread. In Project 2 I will keep it in percentage points, not convert it to a decimal return or combine it directly with the funds’ price returns.

## Project 2 call

**Quarantine:** T10Y2Y is a daily series, but FRED's page shows that the observation is updated after the trading day and warns that data are subject to revision. I will admit it only if Project 2 uses the ALFRED vintage available on each decision date, calculates the signal after that value is released, and trades no earlier than the next eligible session; it must never substitute today's revised FRED history for the historical vintage.

## Reflection — explain to my partner

T10Y2Y is published daily, but it is not safely available at the start of that same trading day: the FRED page showed the 28 October 2026 value updated at 4:03 PM CDT, with the next release on 29 October. In the app, choosing an earlier **as known on** date returns the last observation ALFRED had released by that date, so it can show an earlier business-day observation instead of a value that appeared later that day.

A backtest built from today's FRED values would overstate how quickly the yield-curve signal was available, because it could use a daily value before its publication time. It could also overstate the reliability of the signal by using any later-revised historical values rather than the vintage a trader actually saw.

## Explain the as-known-on download

```python
@st.cache_data(ttl=3600, show_spinner=False)
def download_as_known_on(series_id, vintage_date):
    """Download the ALFRED vintage that was available on ``vintage_date``."""
    url = ALFRED_CSV.format(series_id=series_id, vintage_date=vintage_date.isoformat())
    try:
        with urlopen(url, timeout=20) as response:
            return read_observations(response.read().decode("utf-8-sig"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(f"ALFRED could not download {series_id}: {error}") from error
```

- `@st.cache_data(ttl=3600, show_spinner=False)` tells Streamlit to save a downloaded result for one hour, so the app does not repeatedly request the same series and vintage date. It hides the caching spinner.
- `def download_as_known_on(series_id, vintage_date):` defines a reusable function with the FRED series ID, such as `T10Y2Y`, and the historical date we want to reproduce.
- The triple-quoted line is the function's docstring. It states that the function obtains the ALFRED vintage available on that date, not the values visible today.
- `url = ...` fills the ALFRED CSV address with the series ID and converts the chosen Python date into the `YYYY-MM-DD` format ALFRED expects.
- `try:` starts a block that may fail because the site could be unavailable, the request could take too long, or the response could be invalid.
- `with urlopen(url, timeout=20) as response:` opens that URL and waits at most 20 seconds. `with` closes the connection automatically afterward.
- `return read_observations(...)` reads the downloaded bytes, decodes them as UTF-8 text, sends the CSV text to `read_observations`, removes missing `.` observations there, and returns usable date/value pairs to the app.
- `except ... as error:` catches web, timeout, and invalid-data problems instead of crashing the entire app.
- `raise RuntimeError(...) from error` reports a clear message naming the failed ALFRED series while retaining the original error for debugging. The app catches this error for one series and continues with the rest.

**Partner's question:** Why does the function use ALFRED instead of the regular FRED download?

**My answer:** ALFRED lets the app request the version of the data that was available on a chosen past date. Regular FRED shows today's version, which may include observations published later or revised afterward.
