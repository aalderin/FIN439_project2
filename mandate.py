"""
=============================================================================
Meridian Foundation Mandate Compliance Checker (mandate.py)
Standard library only. Computes all metrics dynamically from inputs.
=============================================================================
"""

# ---------------------------------------------------------------------------
# EDITABLE INPUTS
# ---------------------------------------------------------------------------

# Holdings table: (holding_name, issuer, business_days_to_redeem, reserve_eligible)
HOLDINGS = [
    {"holding": "Cash",                       "issuer": "none",             "days": 0,  "reserve_eligible": True},
    {"holding": "Treasury bills",             "issuer": "U.S. Treasury",    "days": 1,  "reserve_eligible": True},
    {"holding": "Treasury 10-year note",       "issuer": "U.S. Treasury",    "days": 1,  "reserve_eligible": True},
    {"holding": "Global equity index fund",    "issuer": "diversified fund", "days": 2,  "reserve_eligible": False},
    {"holding": "Investment-grade bond fund",  "issuer": "diversified fund", "days": 3,  "reserve_eligible": False},
    {"holding": "Private real estate fund",    "issuer": "diversified fund", "days": 90, "reserve_eligible": False},
    {"holding": "Acme Corp bonds",             "issuer": "Acme Corp",        "days": 4,  "reserve_eligible": False},
    {"holding": "Acme Corp stock",             "issuer": "Acme Corp",        "days": 1,  "reserve_eligible": False},
]

# Candidates A, B, C, and D as percent weights corresponding to HOLDINGS
CANDIDATES = {
    "Candidate A": [2.0, 2.0, 10.0, 60.0, 26.0,  0.0, 0.0, 0.0],
    "Candidate B": [1.0, 0.0,  0.0, 55.0, 20.0, 15.0, 5.0, 4.0],
    "Candidate C": [1.0, 1.0,  0.0, 70.0, 20.0,  0.0, 0.0, 8.0],
    "Candidate D": [3.0, 0.0,  0.0, 97.0,  0.0,  0.0, 0.0, 0.0],
}

# Mandate parameters
RESERVE_SIZE = 100.0             # USD millions
QUARTERLY_DISTRIBUTION = 0.75    # USD millions per quarter
QUARTERS_TO_COVER = 4            # Quarters of payouts required
LIQUIDITY_WINDOW = 5             # Business days to redeem
MINIMUM_LIQUID_SHARE = 90.0      # Minimum percent redeemable within window
ISSUER_LIMIT = 8.0               # Maximum percent in any single company

# Issuers exempt from the single-company limit
EXEMPT_ISSUERS = {"none", "U.S. Treasury", "diversified fund"}

# ---------------------------------------------------------------------------
# CALCULATION & VERIFICATION ENGINE
# ---------------------------------------------------------------------------

def evaluate_mandate():
    # 1. Compute and print reserve minimum
    reserve_min_pct = (QUARTERS_TO_COVER * QUARTERLY_DISTRIBUTION / RESERVE_SIZE) * 100.0
    print("=" * 78)
    print("MERIDIAN FOUNDATION MANDATE COMPLIANCE REPORT")
    print("=" * 78)
    print(f"Reserve minimum: {reserve_min_pct:.1f}% "
          f"({QUARTERS_TO_COVER} quarters x ${QUARTERLY_DISTRIBUTION:.2f}M / ${RESERVE_SIZE:.1f}M)\n")

    # 2. Evaluate each candidate portfolio
    for name, weights in CANDIDATES.items():
        print("-" * 78)
        print(f"{name}")
        print("-" * 78)

        failed_count = 0

        # Check 1: Weights sum to 100
        total_weight = sum(weights)
        pass_sum = abs(total_weight - 100.0) < 1e-5
        status_sum = "pass" if pass_sum else "FAIL"
        if not pass_sum:
            failed_count += 1
        print(f"  Weights sum to 100:                          {total_weight:5.1f}%  -> {status_sum}")

        # Check 2: Lowest weight not negative (long-only)
        lowest_weight = min(weights)
        pass_lowest = lowest_weight >= 0.0
        status_lowest = "pass" if pass_lowest else "FAIL"
        if not pass_lowest:
            failed_count += 1
        print(f"  Lowest weight not negative (long-only):      {lowest_weight:5.1f}%  -> {status_lowest}")

        # Check 3: Reserve-eligible weight at least reserve minimum
        reserve_weight = sum(w for w, h in zip(weights, HOLDINGS) if h["reserve_eligible"])
        pass_reserve = reserve_weight >= (reserve_min_pct - 1e-5)
        status_reserve = "pass" if pass_reserve else "FAIL"
        if not pass_reserve:
            failed_count += 1
        print(f"  Reserve-eligible weight (min {reserve_min_pct:.1f}%):           {reserve_weight:5.1f}%  -> {status_reserve}")

        # Check 4: Weight redeemable within window at least minimum liquid share
        liquid_weight = sum(w for w, h in zip(weights, HOLDINGS) if h["days"] <= LIQUIDITY_WINDOW)
        pass_liquid = liquid_weight >= (MINIMUM_LIQUID_SHARE - 1e-5)
        status_liquid = "pass" if pass_liquid else "FAIL"
        if not pass_liquid:
            failed_count += 1
        print(f"  Liquid weight in <= {LIQUIDITY_WINDOW} days (min {MINIMUM_LIQUID_SHARE:.1f}%):      {liquid_weight:5.1f}%  -> {status_liquid}")

        # Check 5: Largest single company at most issuer limit
        company_weights = {}
        for w, h in zip(weights, HOLDINGS):
            issuer = h["issuer"]
            if issuer not in EXEMPT_ISSUERS:
                company_weights[issuer] = company_weights.get(issuer, 0.0) + w

        largest_company_weight = max(company_weights.values()) if company_weights else 0.0
        pass_issuer = largest_company_weight <= (ISSUER_LIMIT + 1e-5)
        status_issuer = "pass" if pass_issuer else "FAIL"
        if not pass_issuer:
            failed_count += 1
        print(f"  Largest single company (max {ISSUER_LIMIT:.1f}%):             {largest_company_weight:5.1f}%  -> {status_issuer}")

        # Check 6: Calendar-year loss rule
        print("  Calendar-year loss rule (<= 10% max loss):   requires CIO clarification")

        # Candidate conclusion
        if failed_count == 0:
            conclusion = "passes every checkable rule"
        elif failed_count == 1:
            conclusion = "fails 1 rule"
        else:
            conclusion = f"fails {failed_count} rules"

        print(f"  Result: {conclusion}\n")


if __name__ == "__main__":
    evaluate_mandate()
