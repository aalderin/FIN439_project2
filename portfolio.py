"""Portfolio comparison using editable capital-market assumptions.

Standard library only. All results are calculated from the inputs below.
"""

import csv
import io
import os
from math import sqrt


# ---------------------------------------------------------------------------
# EDITABLE INPUTS
# ---------------------------------------------------------------------------

# Expected returns and volatilities are annual percentages.
SLEEVES = {
    "Treasury bills": {"expected_return": 3.5, "volatility": 0.5},
    "Treasury 10-year note": {"expected_return": 4.3, "volatility": 7.0},
    "Investment-grade bond fund": {"expected_return": 5.0, "volatility": 6.0},
    "Global equity index fund": {"expected_return": 8.0, "volatility": 16.0},
}

# Correlations are unitless. Every sleeve must have a row and column.
CORRELATIONS = {
    "Treasury bills": {
        "Treasury bills": 1.00,
        "Treasury 10-year note": 0.10,
        "Investment-grade bond fund": 0.05,
        "Global equity index fund": 0.00,
    },
    "Treasury 10-year note": {
        "Treasury bills": 0.10,
        "Treasury 10-year note": 1.00,
        "Investment-grade bond fund": 0.80,
        "Global equity index fund": -0.10,
    },
    "Investment-grade bond fund": {
        "Treasury bills": 0.05,
        "Treasury 10-year note": 0.80,
        "Investment-grade bond fund": 1.00,
        "Global equity index fund": 0.25,
    },
    "Global equity index fund": {
        "Treasury bills": 0.00,
        "Treasury 10-year note": -0.10,
        "Investment-grade bond fund": 0.25,
        "Global equity index fund": 1.00,
    },
}

OBJECTIVE_RETURN = 6.5
RESERVE_ELIGIBLE = {"Treasury bills", "Treasury 10-year note"}


# ---------------------------------------------------------------------------
# REUSABLE CALCULATIONS
# ---------------------------------------------------------------------------

def validate_inputs(sleeves, correlations):
    """Raise ValueError when inputs cannot form a valid correlation matrix."""
    assets = set(sleeves)
    if set(correlations) != assets:
        raise ValueError("Correlation table must contain exactly one row for every sleeve.")

    for asset, assumptions in sleeves.items():
        volatility = assumptions["volatility"]
        if volatility <= 0:
            raise ValueError(f"Volatility for {asset!r} must be greater than zero.")

    for left in sleeves:
        if set(correlations[left]) != assets:
            raise ValueError(
                f"Correlation row for {left!r} must contain exactly one value for every sleeve."
            )
        for right in sleeves:
            correlation = correlations[left][right]
            if not -1.0 <= correlation <= 1.0:
                raise ValueError(
                    f"Correlation for {left!r} and {right!r} is {correlation}; it must be between -1 and 1."
                )
            if correlation != correlations[right][left]:
                raise ValueError(
                    f"Correlation table is not symmetric: {left!r}/{right!r} does not match "
                    f"{right!r}/{left!r}."
                )


def covariance_matrix(sleeves, correlations):
    """Return covariance entries, in percentage-squared units, by sleeve pair."""
    return {
        left: {
            right: (
                correlations[left][right]
                * sleeves[left]["volatility"]
                * sleeves[right]["volatility"]
            )
            for right in sleeves
        }
        for left in sleeves
    }


def benchmark_weights(sleeves):
    """Return the 40% investment-grade bond / 60% equity benchmark."""
    weights = {asset: 0.0 for asset in sleeves}
    weights["Investment-grade bond fund"] = 40.0
    weights["Global equity index fund"] = 60.0
    return weights


def equal_weight_weights(sleeves):
    """Return weights equally split across every sleeve."""
    return {asset: 100.0 / len(sleeves) for asset in sleeves}


def inverse_volatility_weights(sleeves):
    """Return weights proportional to one divided by volatility."""
    inverse_volatility = {
        asset: 1.0 / assumptions["volatility"]
        for asset, assumptions in sleeves.items()
    }
    total = sum(inverse_volatility.values())
    return {asset: value / total * 100.0 for asset, value in inverse_volatility.items()}


def expected_return(weights, sleeves):
    """Return the portfolio's annual expected return as a percentage."""
    return sum(
        weights[asset] / 100.0 * sleeves[asset]["expected_return"]
        for asset in sleeves
    )


def portfolio_volatility(weights, covariances):
    """Return portfolio annual volatility as a percentage."""
    variance = sum(
        weights[left] / 100.0 * weights[right] / 100.0 * covariances[left][right]
        for left in weights
        for right in weights
    )
    return sqrt(variance)


def reserve_eligible_weight(weights, reserve_eligible):
    """Return the combined percent weight in reserve-eligible sleeves."""
    return sum(weights[asset] for asset in reserve_eligible)


def meets_objective(portfolio_expected_return, objective_return):
    """Return whether expected return is at least the stated objective."""
    return portfolio_expected_return >= objective_return


def lowest_risk_mix(
    sleeves,
    correlations,
    objective_return,
    reserve_eligible,
    minimum_reserve,
    step=5.0,
):
    """Find the lowest-volatility long-only allocation on a fixed weight grid.

    All percentages are expressed as percentage points.  Returns ``None`` when
    no grid allocation can meet both the return objective and reserve minimum.
    """
    validate_inputs(sleeves, correlations)
    if step <= 0 or 100.0 % step > 1e-9:
        raise ValueError("Step must be a positive divisor of 100.")

    assets = list(sleeves)
    units = round(100.0 / step)
    covariances = covariance_matrix(sleeves, correlations)
    best = None

    def search(asset_index, units_left, weights):
        nonlocal best
        if asset_index == len(assets) - 1:
            candidate = dict(weights)
            candidate[assets[asset_index]] = units_left * step
            candidate_return = expected_return(candidate, sleeves)
            candidate_reserve = reserve_eligible_weight(candidate, reserve_eligible)
            if candidate_return + 1e-9 < objective_return:
                return
            if candidate_reserve + 1e-9 < minimum_reserve:
                return

            candidate_volatility = portfolio_volatility(candidate, covariances)
            if best is None or candidate_volatility < best["volatility"] - 1e-9:
                best = {
                    "weights": candidate,
                    "expected_return": candidate_return,
                    "volatility": candidate_volatility,
                    "reserve_eligible_weight": candidate_reserve,
                }
            return

        asset = assets[asset_index]
        for units_for_asset in range(units_left + 1):
            weights[asset] = units_for_asset * step
            search(asset_index + 1, units_left - units_for_asset, weights)
        weights.pop(asset, None)

    search(0, units, {})
    return best


def estimate_from_csv(price_csv, last_36_months=False):
    """Estimate annualized sleeve inputs from monthly adjusted-close prices.

    ``price_csv`` may be a file path, text, bytes, or a file-like uploaded
    object.  Its first column must be ``Date`` and remaining columns are ticker
    symbols, with rows oldest first.  Set ``last_36_months`` to use only the
    most recent 36 monthly returns.
    """
    if hasattr(price_csv, "read"):
        raw_text = price_csv.read()
    elif isinstance(price_csv, (str, os.PathLike)) and os.path.exists(price_csv):
        with open(price_csv, "r", encoding="utf-8-sig", newline="") as file:
            raw_text = file.read()
    else:
        raw_text = price_csv

    if isinstance(raw_text, bytes):
        raw_text = raw_text.decode("utf-8-sig")
    if not isinstance(raw_text, str):
        raise ValueError("Price data must be CSV text, bytes, a path, or a file-like object.")

    rows = list(csv.DictReader(io.StringIO(raw_text)))
    if not rows or not rows[0]:
        raise ValueError("The CSV must contain a header and price rows.")
    fieldnames = list(rows[0])
    if len(fieldnames) < 2 or fieldnames[0] != "Date":
        raise ValueError("The first CSV column must be Date, followed by ticker columns.")
    tickers = fieldnames[1:]
    dates = [row["Date"] for row in rows]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("Dates must be unique and ordered oldest first.")

    prices = {}
    for ticker in tickers:
        try:
            values = [float(row[ticker]) for row in rows]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{ticker} contains a missing or invalid price.") from error
        if any(value <= 0 for value in values):
            raise ValueError(f"{ticker} prices must all be greater than zero.")
        prices[ticker] = values

    if len(rows) < 3:
        raise ValueError("At least three monthly price rows are required.")
    monthly_returns = {
        ticker: [current / previous - 1.0 for previous, current in zip(values, values[1:])]
        for ticker, values in prices.items()
    }
    if last_36_months:
        monthly_returns = {ticker: values[-36:] for ticker, values in monthly_returns.items()}
    observations = len(next(iter(monthly_returns.values())))
    if observations < 2:
        raise ValueError("At least two monthly returns are required.")

    means = {
        ticker: sum(values) / observations
        for ticker, values in monthly_returns.items()
    }
    sample_std = {
        ticker: sqrt(sum((value - means[ticker]) ** 2 for value in values) / (observations - 1))
        for ticker, values in monthly_returns.items()
    }
    if any(value == 0 for value in sample_std.values()):
        raise ValueError("Each ticker needs price variation to estimate correlations.")

    sleeves = {
        ticker: {
            "expected_return": means[ticker] * 12.0 * 100.0,
            "volatility": sample_std[ticker] * sqrt(12.0) * 100.0,
        }
        for ticker in tickers
    }
    correlations = {ticker: {} for ticker in tickers}
    for left_index, left in enumerate(tickers):
        for right in tickers[left_index:]:
            correlation = (
                1.0
                if left == right
                else sum(
                    (left_value - means[left]) * (right_value - means[right])
                    for left_value, right_value in zip(monthly_returns[left], monthly_returns[right])
                )
                / ((observations - 1) * sample_std[left] * sample_std[right])
            )
            correlations[left][right] = correlation
            correlations[right][left] = correlation
    return sleeves, correlations


def print_portfolio(name, weights, sleeves, covariances, objective_return, reserve_eligible):
    """Print all requested metrics for one portfolio."""
    result_return = expected_return(weights, sleeves)
    result_volatility = portfolio_volatility(weights, covariances)
    reserve_weight = reserve_eligible_weight(weights, reserve_eligible)
    weights_text = ", ".join(f"{asset}: {weight:.1f}%" for asset, weight in weights.items())
    objective_result = "Yes" if meets_objective(result_return, objective_return) else "No"

    print(name)
    print(f"  Weights: {weights_text}")
    print(f"  Expected return: {result_return:.2f}%")
    print(f"  Volatility: {result_volatility:.2f}%")
    print(f"  Reserve-eligible weight: {reserve_weight:.1f}%")
    print(f"  Meets {objective_return:.1f}% objective: {objective_result}")


def main():
    """Validate inputs, build covariance, and compare the three portfolios."""
    try:
        validate_inputs(SLEEVES, CORRELATIONS)
    except ValueError as error:
        raise SystemExit(f"Input error: refusing to run. {error}")

    covariances = covariance_matrix(SLEEVES, CORRELATIONS)
    portfolios = {
        "Benchmark (40% IG bonds / 60% equity)": benchmark_weights(SLEEVES),
        "Equal weight": equal_weight_weights(SLEEVES),
        "Inverse volatility": inverse_volatility_weights(SLEEVES),
    }

    for name, weights in portfolios.items():
        print_portfolio(
            name, weights, SLEEVES, covariances, OBJECTIVE_RETURN, RESERVE_ELIGIBLE
        )
        print()


if __name__ == "__main__":
    main()
