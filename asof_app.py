"""A small point-in-time FRED and ALFRED explorer for Lab 17.

Run with: streamlit run asof_app.py
"""

import csv
import io
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import streamlit as st


SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
ALFRED_CSV = (
    "https://alfred.stlouisfed.org/graph/alfredgraph.csv?"
    "id={series_id}&vintage_date={vintage_date}"
)


def read_observations(csv_text):
    """Return valid (observation_date, value) pairs, dropping FRED's '.'."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames or len(reader.fieldnames) < 2:
        raise ValueError("The download did not contain an observation-date and value column.")

    date_column = reader.fieldnames[0]
    value_column = reader.fieldnames[-1]
    observations = []
    for row in reader:
        raw_date = (row.get(date_column) or "").strip()
        raw_value = (row.get(value_column) or "").strip()
        if not raw_date or not raw_value or raw_value == ".":
            continue
        try:
            observations.append((date.fromisoformat(raw_date), float(raw_value)))
        except ValueError:
            # FRED CSVs can include an empty or non-numeric observation. It is unusable.
            continue
    return observations


@st.cache_data(ttl=3600, show_spinner=False)
def download_current(series_id):
    """Download the current FRED history for exactly one series."""
    url = FRED_CSV.format(series_id=series_id)
    try:
        with urlopen(url, timeout=20) as response:
            return read_observations(response.read().decode("utf-8-sig"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(f"FRED could not download {series_id}: {error}") from error


@st.cache_data(ttl=3600, show_spinner=False)
def download_as_known_on(series_id, vintage_date):
    """Download the ALFRED vintage that was available on ``vintage_date``."""
    url = ALFRED_CSV.format(series_id=series_id, vintage_date=vintage_date.isoformat())
    try:
        with urlopen(url, timeout=20) as response:
            return read_observations(response.read().decode("utf-8-sig"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(f"ALFRED could not download {series_id}: {error}") from error


def latest(observations):
    """Return the most recent observation, or None when the list is empty."""
    return max(observations, default=None, key=lambda observation: observation[0])


def display_observation(observation):
    if observation is None:
        return "No observation"
    measured_on, value = observation
    return f"{measured_on.isoformat()}: {value:g}"


def carry_forward_for_chart(series_data):
    """Fill display-only gaps so weekly and monthly lines remain visible together."""
    all_dates = sorted(
        {
            measured_on
            for observations in series_data.values()
            for measured_on, _ in observations
        }
    )
    filled = {}
    for series_id, observations in series_data.items():
        values_by_date = dict(observations)
        last_value = None
        filled[series_id] = {}
        for measured_on in all_dates:
            if measured_on in values_by_date:
                last_value = values_by_date[measured_on]
            if last_value is not None:
                filled[series_id][measured_on] = last_value
    return filled


st.set_page_config(page_title="FRED point-in-time rates", layout="wide")
st.title("FRED point-in-time rates")
st.caption(
    "Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded today; "
    "built with AI help, a learning demonstration, not investment advice."
)

with st.sidebar:
    st.header("Controls")
    chosen_ids = st.multiselect(
        "Series",
        options=list(SERIES),
        default=list(SERIES),
        format_func=lambda series_id: f"{series_id} — {SERIES[series_id]}",
    )
    added_id = st.text_input("Add another FRED series ID", placeholder="For example: T10Y2Y")
    start_date = st.date_input("Start date", value=date(2020, 1, 1))
    as_known_on = st.date_input("As known on", value=date.today())

if isinstance(start_date, tuple) or isinstance(as_known_on, tuple):
    st.error("Choose one start date and one as-known-on date.")
    st.stop()
if start_date > as_known_on:
    st.warning("The start date is after the as-known-on date; the chart may be empty.")

added_id = added_id.strip().upper()
series_ids = chosen_ids + ([added_id] if added_id and added_id not in chosen_ids else [])
if not series_ids:
    st.info("Select a listed series or enter another FRED series ID.")
    st.stop()

table_rows = []
combined_chart_data = {}
for series_id in series_ids:
    label = SERIES.get(series_id, "Custom FRED series")
    st.subheader(f"{series_id} — {label}")
    try:
        current = download_current(series_id)
        vintage = download_as_known_on(series_id, as_known_on)
    except RuntimeError as error:
        st.error(str(error))
        continue

    current = [(measured_on, value) for measured_on, value in current if measured_on >= start_date]
    vintage = [(measured_on, value) for measured_on, value in vintage if measured_on >= start_date]
    if not current:
        st.warning(f"No current {series_id} observations are available from {start_date.isoformat()}.")
    else:
        combined_chart_data[series_id] = current
        st.line_chart(
            {series_id: {measured_on: value for measured_on, value in current}},
            x_label="Observation date",
            y_label="Value",
        )

    last_known = latest(vintage)
    last_current = latest(current)
    st.write(f"**Last date known on {as_known_on.isoformat()}:** {display_observation(last_known)}")

    current_by_date = dict(current)
    late_values = (
        sum(measured_on > last_known[0] for measured_on, _ in current)
        if last_known is not None
        else len(current)
    )
    revised_values = sum(
        measured_on in current_by_date and current_by_date[measured_on] != value
        for measured_on, value in vintage
    )
    table_rows.append(
        {
            "ID": f"https://fred.stlouisfed.org/series/{series_id}",
            "Last date measured as known then": (
                last_known[0].isoformat() if last_known else "No observation"
            ),
            "Value as known then": f"{last_known[1]:g}" if last_known else "—",
            "Last date measured today": (
                last_current[0].isoformat() if last_current else "No observation"
            ),
            "Value today": f"{last_current[1]:g}" if last_current else "—",
            "Today's values after last known date": late_values,
            "Revised values on same dates": revised_values,
        }
    )

st.header("Combined comparison")
if combined_chart_data:
    st.line_chart(
        carry_forward_for_chart(combined_chart_data),
        x_label="Observation date",
        y_label="Value",
    )
    st.caption(
        "For this display only, weekly and monthly values are carried forward until their next "
        "release so every series remains visible. Individual charts and the table use the original data."
    )

st.header("Point-in-time comparison")
if table_rows:
    st.dataframe(
        table_rows,
        column_config={
            "ID": st.column_config.LinkColumn(
                "ID", display_text=r".*/series/(.*)", help="Open this FRED series page."
            )
        },
        hide_index=True,
        width="stretch",
    )
else:
    st.info("No series could be downloaded. Check the ID or try again shortly.")
