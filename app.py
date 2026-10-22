"""Streamlit interface for the Meridian portfolio learning demonstration."""

import copy

import streamlit as st

from portfolio import (
    CORRELATIONS,
    OBJECTIVE_RETURN,
    RESERVE_ELIGIBLE,
    SLEEVES,
    estimate_from_csv,
    lowest_risk_mix,
)


st.set_page_config(page_title="Meridian portfolio explorer", layout="wide")
st.title("Meridian portfolio explorer")
st.caption("Built with AI help, a learning demonstration, not investment advice.")

with st.sidebar:
    st.header("Inputs")
    objective = st.number_input("Expected-return objective (%)", value=float(OBJECTIVE_RETURN), step=0.1)
    reserve_minimum = st.number_input("Minimum reserve-eligible weight (%)", value=3.0, min_value=0.0, max_value=100.0, step=1.0)
    uploaded_prices = st.file_uploader("Upload monthly adjusted-close prices (.csv)", type="csv")
    use_last_36 = st.toggle("Use last 36 monthly returns", value=False)

try:
    if uploaded_prices is None:
        active_sleeves = copy.deepcopy(SLEEVES)
        active_correlations = copy.deepcopy(CORRELATIONS)
        baseline_sleeves = copy.deepcopy(SLEEVES)
        baseline_correlations = copy.deepcopy(CORRELATIONS)
        source_label = "Meridian inputs"
    else:
        file_bytes = uploaded_prices.getvalue()
        baseline_sleeves, baseline_correlations = estimate_from_csv(file_bytes)
        active_sleeves, active_correlations = estimate_from_csv(file_bytes, use_last_36)
        source_label = "CSV estimates" + (" (last 36 monthly returns)" if use_last_36 else " (all monthly returns)")
except ValueError as error:
    st.error(f"Could not estimate inputs from the CSV: {error}")
    st.stop()

st.subheader(f"Expected-return estimates — {source_label}")
edited_sleeves = copy.deepcopy(active_sleeves)
input_columns = st.columns(min(4, len(active_sleeves)))
for index, asset in enumerate(active_sleeves):
    with input_columns[index % len(input_columns)]:
        edited_sleeves[asset]["expected_return"] = st.number_input(
            f"{asset} expected return (%)",
            value=float(active_sleeves[asset]["expected_return"]),
            step=0.1,
            key=f"return_{asset}",
        )

st.subheader("Reserve eligibility")
reserve_columns = st.columns(min(4, len(edited_sleeves)))
selected_reserve_assets = set()
for index, asset in enumerate(edited_sleeves):
    with reserve_columns[index % len(reserve_columns)]:
        if st.checkbox(
            asset,
            value=asset in RESERVE_ELIGIBLE,
            key=f"reserve_{asset}",
        ):
            selected_reserve_assets.add(asset)

current_result = lowest_risk_mix(
    edited_sleeves,
    active_correlations,
    objective,
    selected_reserve_assets,
    reserve_minimum,
)
baseline_result = lowest_risk_mix(
    baseline_sleeves,
    baseline_correlations,
    objective,
    selected_reserve_assets,
    reserve_minimum,
)


def show_result(result, heading):
    st.subheader(heading)
    if result is None:
        st.warning("No mix meets the objective.")
        return
    st.dataframe(
        {"Asset": list(result["weights"]), "Weight (%)": list(result["weights"].values())},
        hide_index=True,
        width="stretch",
    )
    first, second, third = st.columns(3)
    first.metric("Expected return", f"{result['expected_return']:.2f}%")
    second.metric("Volatility", f"{result['volatility']:.2f}%")
    third.metric("Reserve-eligible", f"{result['reserve_eligible_weight']:.2f}%")


left, right = st.columns(2)
with left:
    show_result(current_result, "Lowest-risk mix")
with right:
    baseline_name = "Loaded-input answer" if uploaded_prices is None else "CSV all-months answer"
    show_result(baseline_result, baseline_name)
    if current_result is not None and baseline_result is not None:
        largest_change = max(
            abs(current_result["weights"][asset] - baseline_result["weights"].get(asset, 0.0))
            for asset in current_result["weights"]
        )
        st.metric("Largest weight change", f"{largest_change:.2f} points")
