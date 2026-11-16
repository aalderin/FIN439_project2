# Lab 20 — Project 2 Readiness

**One thing today: prove that a stranger can reach your Project 2 decision from your GitHub repository alone.**

## D — The question

> **Could a committee member who has never met you reach your decision from your repository — and does the decision survive one changed input?**

Yes. A committee member cloning this repository can follow the one-line setup in `README.md`, launch `streamlit run app.py`, and observe the exact lowest-risk portfolio (65% SGOV / 35% VTI) and mandate verdicts in under a minute without coaching. Furthermore, the decision is resilient to input shocks: when a fixed-income estimate is shocked by +241 bps, the allocation remains unchanged because cash plus equity strictly dominates intermediate credit.

---

## I — The cold run, by your partner

*Step followed: Gave partner only the repository URL. No verbal coaching.*

| Cold run element | Partner record |
| :--- | :--- |
| **Timestamp & Duration** | **4:56 PM – 4:59 PM EST, Nov 16, 2026** (Elapsed time: **3 minutes**) |
| **Commands run** | `git clone https://github.com/aalderin/FIN439_project2.git`<br>`cd FIN439_project2`<br>`python -m venv .venv`<br>`source .venv/bin/activate`<br>`pip install streamlit pandas`<br>`python portfolio.py`<br>`python mandate.py`<br>`streamlit run app.py` |
| **First failure / Error text** | **None** ("no error text" — clean cold run, zero errors encountered) |
| **Where the result is** | Yes, visible output on **`http://localhost:8501`** under the heading **"Lowest-risk mix"** |
| **Observed numbers** | **SGOV: 65.0%**, **VTI: 35.0%**, VGIT: 0.0%, VCIT: 0.0%<br>Expected return: **6.79%** \| Volatility: **5.62%** \| Reserve-eligible: **65.00%** |

---

## V — One changed input, predicted first

### 1. Pre-Run Prediction (Committed with AI Closed)
* **Load-bearing input:** VCIT (Intermediate Corporate Bond ETF) expected return estimate.
* **Old value:** `1.19%`
* **New value:** `3.60%` (+241 bps increase)
* **Expected output direction:** Allocation weights will remain identical at **65% SGOV / 35% VTI**; portfolio expected return will remain **6.79%** and volatility will remain **5.62%**.
* **Expected effect on decision:** **No change.** The committee recommendation remains a bounded **Pilot**.
* **Financial rationale:** Even at 3.60%, VCIT's expected return remains far below the mandate's 6.50% hurdle. Furthermore, VCIT's volatility (7.88%) is substantially higher than SGOV's (0.46%). Because SGOV offers 3.83% yield with negligible risk, the optimizer strictly prefers combining risk-free cash with high-return equity (VTI at 12.30%) to reach 6.50% at lowest variance. VCIT remains economically uncompetitive.

### 2. Post-Run Actual Result
* **Observed allocation:** **65% SGOV / 35% VTI** (Largest weight change = **0.00 percentage points**).
* **Observed portfolio metrics:** Return: **6.79%** | Volatility: **5.62%** | Reserve: **65.00%**.
* **Did the decision change?** **No.** The committee decision remains a bounded **Pilot**.
* **Reconciliation:** Actual matched prediction perfectly. The 5-point discrete grid search confirmed that no mix containing VCIT can achieve lower portfolio variance than the 65% SGOV / 35% VTI blend while clearing the 6.50% return hurdle.

---

## Explain the code (Six minutes, no AI)

The core decision engine is `lowest_risk_mix` in [`portfolio.py`](portfolio.py) (called by [`app.py`](app.py)):

```python
def lowest_risk_mix(sleeves, correlations, objective, reserve_assets, reserve_min):
    cov = covariance_matrix(sleeves, correlations)
    best_mix = None
    best_vol = float("inf")

    # Discrete grid search in 5 percentage point steps across 4 assets
    for w1 in range(0, 105, 5):
        for w2 in range(0, 105 - w1, 5):
            for w3 in range(0, 105 - w1 - w2, 5):
                w4 = 100 - w1 - w2 - w3
                weights = dict(zip(sleeves.keys(), [w1, w2, w3, w4]))
                
                # Check 1: Return hurdle (must be >= 6.5%)
                exp_ret = sum(weights[a] * sleeves[a]["expected_return"] for a in sleeves) / 100.0
                if exp_ret < objective:
                    continue
                
                # Check 2: Reserve constraint (must be >= 3.0%)
                res_wt = sum(weights[a] for a in reserve_assets)
                if res_wt < reserve_min:
                    continue
                
                # Check 3: Portfolio variance w^T * Sigma * w
                var = sum(weights[i] * weights[j] * cov[i][j] for i in sleeves for j in sleeves) / 10000.0
                vol = sqrt(var)
                if vol < best_vol:
                    best_vol = vol
                    best_mix = {"weights": weights, "expected_return": exp_ret, "volatility": vol, "reserve_eligible_weight": res_wt}
    return best_mix
```

### Explanation given to partner:
1. **Covariance Matrix:** `covariance_matrix` turns individual asset volatilities and pairwise correlation coefficients into covariance terms $\sigma_{ij} = \rho_{ij} \sigma_i \sigma_j$.
2. **5-Point Step Constraint:** Nested loops enforce full investment ($\sum w_i = 100\%$) and long-only weights ($w_i \ge 0$) in discrete 5% steps, avoiding fractional execution noise.
3. **Dual Gate Filtering:** Any candidate allocation failing the expected return hurdle ($< 6.5\%$) or reserve minimum ($< 3.0\%$) is immediately skipped via `continue`.
4. **Minimum Volatility Retention:** For all qualifying portfolios, the code calculates portfolio variance $w^T \Sigma w$, tracks standard deviation $\sqrt{\text{variance}}$, and preserves the mix with the minimum volatility.

### Partner Question & Answer:
* **Partner's question to me:** *"Why does w[0] (SGOV) alone enforce the 3% reserve requirement? Since VGIT is also marked reserve-eligible in our asset universe table, why is its weight not included in this calculation?"*
* **My answer:** *"The code does not hardcode `w[0]`; `reserve_eligible_weight` dynamically sums `sum(weights[asset] for asset in reserve_eligible)` across both SGOV and VGIT. VGIT ended up with 0.0% allocation purely because the optimizer minimized portfolio variance: over the 60-month historical sample, VGIT had an annualized return of only 0.12% with 5.51% volatility, whereas SGOV delivered 3.83% return with 0.46% volatility. Because SGOV dominates VGIT in risk-adjusted yield, the optimizer placed 65% into SGOV and 0% into VGIT. SGOV alone satisfies the 3.0% reserve hurdle (delivering 65.0% reserve-eligible weight) without needing VGIT."*

* **My question to partner:** *"Why did you use a 60-month historical window for your portfolio estimates rather than other lookback periods?"*
* **Partner's answer:** *"The 60-month lookback (5 full years, Oct 2021 – Sep 2026) is the standard baseline to capture a full market cycle (both the near-zero rate regime and the aggressive 2022–2023 rate hiking cycle). Shorter windows (like 36 months) create severe recency bias by overfitting to the recent equity run, which causes the optimizer to de-risk prematurely into cash."*

---

## E — Fix one thing

* **Partner critique:** The shared link is `https://github.com/aalderin/FIN439_project2`, but the `README.md` clone instructions initially told a stranger to clone `finance-ai-course` (`git clone https://github.com/aalderin/finance-ai-course.git` and `cd finance-ai-course`). This caused ambiguity about which repository is the official canonical Project 2 submission.
* **Fix pushed:** Standardized the canonical Project 2 repository across all documentation. Updated `README.md` and `docs/submission-manifest.md` to:
  ```bash
  git clone https://github.com/aalderin/FIN439_project2.git
  cd FIN439_project2
  ```
* **Partner rerun:** Partner confirmed the clone command now matches the shared repository URL with zero ambiguity.

---

## Your decision line

> **"Recommend a bounded Pilot of the 65% SGOV / 35% VTI allocation (6.79% expected return, 5.62% volatility, 65.0% reserve-eligible) under a 12-month review; reversed to cash preservation or intermediate bonds if VTI forward return expectation drops below 11.0% or cash yield compresses below 2.50%."**

---

## Reflect — Explain to partner

1. **What the cold run found that I could not see:**  
   When developing on my own machine, I took for granted that Streamlit opens the browser automatically. Watching my partner's cold run showed that a stranger relies completely on the console URL output (`http://localhost:8501`) and needs the `README.md` to state exactly which section of the page displays the final decision numbers (**"Lowest-risk mix"** vs. **"Baseline mix"**).
2. **What I will not touch before the deadline:**  
   I will **freeze** the asset universe (SGOV, VGIT, VCIT, VTI), the 60-month historical price dataset, the 5-point optimization grid, and the core mandate parameters (6.5% return / 3% reserve). I will not introduce new packages, additional asset classes, or solver dependencies before the final submission, keeping the codebase transparent and robust.

---

## Floor Checklist

- [x] Partner's cold-run note recorded with command, failure check, elapsed time, and result location.
- [x] One load-bearing input changed with pre-run prediction, rationale, and verified post-run reconciliation.
- [x] Six-minute code explanation documented with partner Q&A.
- [x] One usability fix pushed and verified.
- [x] Concise, committee-ready decision line with explicit reversal triggers.
