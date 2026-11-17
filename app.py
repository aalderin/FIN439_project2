"""Streamlit interface for the Meridian portfolio learning demonstration."""

import copy
import hashlib

import streamlit as st

from portfolio import (
    CORRELATIONS,
    OBJECTIVE_RETURN,
    RESERVE_ELIGIBLE,
    SLEEVES,
    covariance_matrix,
    estimate_from_csv,
    expected_return,
    lowest_risk_mix,
    portfolio_volatility,
    reserve_eligible_weight,
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
        estimate_context = "meridian"
    else:
        file_bytes = uploaded_prices.getvalue()
        baseline_sleeves, baseline_correlations = estimate_from_csv(file_bytes)
        active_sleeves, active_correlations = estimate_from_csv(file_bytes, use_last_36)
        source_label = "CSV estimates" + (" (last 36 monthly returns)" if use_last_36 else " (all monthly returns)")
        estimate_context = f"csv:{hashlib.sha256(file_bytes).hexdigest()}:{use_last_36}"
except ValueError as error:
    st.error(f"Could not estimate inputs from the CSV: {error}")
    st.stop()

st.subheader(f"Expected-return estimates — {source_label}")
if st.session_state.get("estimate_context") != estimate_context:
    for asset, assumptions in active_sleeves.items():
        st.session_state[f"return_{asset}"] = float(assumptions["expected_return"])
    st.session_state["estimate_context"] = estimate_context

edited_sleeves = copy.deepcopy(active_sleeves)
input_columns = st.columns(min(4, len(active_sleeves)))
for index, asset in enumerate(active_sleeves):
    with input_columns[index % len(input_columns)]:
        edited_sleeves[asset]["expected_return"] = st.number_input(
            f"{asset} expected return (%)",
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

# ---------------------------------------------------------------------------
# BASELINES & MANDATE VERDICTS COMPARISON
# ---------------------------------------------------------------------------
st.subheader("Mandate & Baselines Comparison")

cov = covariance_matrix(edited_sleeves, active_correlations)

# 1. Equal-Weight Baseline
ew_weights = {asset: 100.0 / len(edited_sleeves) for asset in edited_sleeves}
ew_ret = expected_return(ew_weights, edited_sleeves)
ew_vol = portfolio_volatility(ew_weights, cov)
ew_res = reserve_eligible_weight(ew_weights, selected_reserve_assets)
if ew_ret + 1e-6 < objective:
    ew_verdict = f"FAIL (Return {ew_ret:.2f}% < {objective:.1f}%)"
elif ew_res + 1e-6 < reserve_minimum:
    ew_verdict = f"FAIL (Reserve {ew_res:.1f}% < {reserve_minimum:.1f}%)"
else:
    ew_verdict = "PASS"

# 2. 60/40 Benchmark Mix
bm_weights = {asset: 0.0 for asset in edited_sleeves}
if "Global equity index fund" in edited_sleeves and "Investment-grade bond fund" in edited_sleeves:
    bm_weights["Investment-grade bond fund"] = 40.0
    bm_weights["Global equity index fund"] = 60.0
elif "VTI" in edited_sleeves:
    bm_weights["VTI"] = 60.0
    if "VGIT" in edited_sleeves and "VCIT" in edited_sleeves:
        bm_weights["VGIT"] = 20.0
        bm_weights["VCIT"] = 20.0
    elif "VCIT" in edited_sleeves:
        bm_weights["VCIT"] = 40.0
bm_ret = expected_return(bm_weights, edited_sleeves)
bm_vol = portfolio_volatility(bm_weights, cov)
bm_res = reserve_eligible_weight(bm_weights, selected_reserve_assets)
if bm_ret + 1e-6 < objective:
    bm_verdict = f"FAIL (Return {bm_ret:.2f}% < {objective:.1f}%)"
elif bm_res + 1e-6 < reserve_minimum:
    bm_verdict = f"FAIL (Reserve {bm_res:.1f}% < {reserve_minimum:.1f}%)"
else:
    bm_verdict = "PASS"

# 3. Optimized Portfolio (Lowest-risk mix)
if current_result is not None:
    opt_ret = current_result["expected_return"]
    opt_vol = current_result["volatility"]
    opt_res = current_result["reserve_eligible_weight"]
    opt_verdict = "PASS (Lowest Volatility)"
    opt_weights_summary = ", ".join(f"{k}: {v:.0f}%" for k, v in current_result["weights"].items() if v > 0)
else:
    opt_ret = 0.0
    opt_vol = 0.0
    opt_res = 0.0
    opt_verdict = "FAIL (No feasible mix)"
    opt_weights_summary = "None"

ew_weights_summary = f"{100.0 / len(edited_sleeves):.1f}% each"
bm_weights_summary = ", ".join(f"{k}: {v:.0f}%" for k, v in bm_weights.items() if v > 0)

comparison_table = [
    {
        "Portfolio": "Equal-Weight Baseline",
        "Key Weights": ew_weights_summary,
        "Expected Return": f"{ew_ret:.2f}%",
        "Volatility": f"{ew_vol:.2f}%",
        "Reserve Weight": f"{ew_res:.1f}%",
        "Mandate Verdict": ew_verdict,
    },
    {
        "Portfolio": "Benchmark (40/60 Mix)",
        "Key Weights": bm_weights_summary,
        "Expected Return": f"{bm_ret:.2f}%",
        "Volatility": f"{bm_vol:.2f}%",
        "Reserve Weight": f"{bm_res:.1f}%",
        "Mandate Verdict": bm_verdict,
    },
    {
        "Portfolio": "Optimized Mix (Lowest-Risk)",
        "Key Weights": opt_weights_summary,
        "Expected Return": f"{opt_ret:.2f}%",
        "Volatility": f"{opt_vol:.2f}%",
        "Reserve Weight": f"{opt_res:.1f}%",
        "Mandate Verdict": opt_verdict,
    },
]

st.dataframe(comparison_table, hide_index=True, width="stretch")
