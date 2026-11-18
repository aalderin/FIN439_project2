# Project 2 Decision Memo — Investment Committee Recommendation

**To:** Investment Committee, Meridian Foundation  
**From:** Portfolio Analyst  
**Date:** November 2026  
**Subject:** Asset Allocation Recommendation — Lowest-Risk Multi-Asset Portfolio Under Reserve Mandate  
**Classification:** Major Project 2 Deliverable (`decision-memo.md`)  

> **AI Disclosure:** This memorandum was prepared with assistance from Google Antigravity (Anthropic Claude and Google Gemini models) for structural outlining, sensitivity cross-checking, and drafting assistance. All portfolio calculations, historical data audits, constraint evaluations, and final investment recommendations are the independent work and responsibility of the author.  
> **Course Disclaimer:** Prepared for FIN 43900 (AI in Finance) at Purdue University. This document is an educational demonstration and analytical model, **not investment advice**.

---

## 1. Executive Recommendation: Pilot (Not Adopt)

I recommend that the Investment Committee approve a **bounded Pilot allocation** of the algorithmic lowest-risk portfolio process, rather than immediate full adoption across foundation assets.

### Recommended Target Allocation
* **65.0% iShares 0–3 Month Treasury Bond ETF (SGOV)**
* **35.0% Vanguard Total Stock Market ETF (VTI)**
* **0.0% Vanguard Intermediate-Term Treasury ETF (VGIT)**
* **0.0% Vanguard Intermediate-Term Corporate Bond ETF (VCIT)**

### Portfolio Key Characteristics
* **Expected Annual Return:** **6.79%** (exceeds the 6.50% mandate hurdle by +29 bps)
* **Expected Annual Volatility:** **5.62%** (lowest-risk feasible combination)
* **Reserve-Eligible Weight:** **65.0%** (substantially exceeds the 3.0% minimum constraint)

### Why Pilot Instead of Adopt?
1. **Severe Estimation Window Sensitivity:** As demonstrated in stress testing, shortening the historical estimation window from 60 months to 36 months induces an extreme **20 percentage point swing** (SGOV expands to 85%, while VTI contracts to 15%). The algorithm aggressively capitalizes on recent elevated equity performance (22.00% annualized 3-year return vs. 12.30% 5-year return) to shed equity risk.
2. **Capital-Market Assumption Fragility:** If forward equity returns moderate by just 100 bps (from 12.30% to 11.30%), the optimizer must immediately shift 5 percentage points from cash into equities (60% SGOV / 40% VTI) to satisfy the return hurdle, increasing portfolio risk.
3. **Prudent Governance:** A pilot allows the committee to observe real-world execution, transaction costs, cash yield tracking, and signal stability under live conditions before committing the total endowment.

---

## 2. Investment Mandate & Asset Universe

### The Mandate Constraints
The portfolio was engineered to comply with the Meridian Foundation Investment Policy Statement (IPS) established in Labs 13 and 15:
1. **Return Hurdle:** Minimum expected annual return of **6.50%**.
2. **Hard Reserve Minimum:** At least **3.0%** of total assets must be held in designated reserve-eligible assets (cash proxies or short-term U.S. Treasuries) to guarantee four quarters of foundation grant distributions ($0.75M/quarter on a $100M reserve pool).
3. **Long-Only & Step Constraints:** Long-only allocations ($w_i \ge 0, \sum w_i = 1.0$) evaluated in discrete 5.0% allocation increments.
4. **Single-Issuer Limit:** No single corporate issuer may exceed 8.0% of portfolio value (all ETF sleeves satisfy this requirement through broad diversification).

### Investment Universe & Data Provenance
Asset parameters were estimated using 60 monthly adjusted-close observations from [`prices.csv`](prices.csv) (November 2021 through October 2026), sourced from Yahoo Finance on 2026-10-22:

| Ticker | Asset Class / Sleeve | 60-Mo Ann. Return | 60-Mo Ann. Vol | Reserve-Eligible? |
| :--- | :--- | :---: | :---: | :---: |
| **SGOV** | Short-Term U.S. Treasury (0–3 Mo) | 3.83% | 0.46% | **Yes** |
| **VGIT** | Intermediate U.S. Treasury (3–10 Yr) | 0.12% | 5.51% | **Yes** |
| **VCIT** | Intermediate Corporate Credit | 1.19% | 7.88% | No |
| **VTI** | Broad U.S. Total Stock Market Equity | 12.30% | 15.83% | No |

---

## 3. Comparison with Transparent Baselines

To justify active algorithmic selection, the optimized portfolio was benchmarked against two standard institutional alternatives:

| Strategy | SGOV | VGIT | VCIT | VTI | Expected Return | Volatility | Reserve Weight | Mandate Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Equal-Weight Baseline** | 25.0% | 25.0% | 25.0% | 25.0% | 4.36% | 5.37% | 50.0% | **FAIL** (Return < 6.50%) |
| **Traditional 60/40 Benchmark** | 0.0% | 20.0% | 20.0% | 60.0% | 7.64% | 10.36% | 20.0% | **PASS** (Return $\ge$ 6.50%) |
| **Optimized Pilot Mix** | **65.0%** | **0.0%** | **0.0%** | **35.0%** | **6.79%** | **5.62%** | **65.0%** | **PASS** (Lowest Feasible Volatility) |

### Key Findings
* **Equal Weight Fails:** The naive equal-weight portfolio achieves only 4.36% expected return, failing the mandate due to heavy drag from low historical fixed-income returns.
* **Superior Risk Efficiency:** While a standard 60/40 mix passes the return hurdle (7.64%), our optimized mix achieves the 6.50% objective with **nearly half the volatility** (5.62% vs. 10.36%). The model exploits cash yield (SGOV at 3.83% with 0.46% volatility) paired with high equity risk-premia, completely zeroing out intermediate bonds that suffered during the 2022–2023 rate hiking cycle.

---

## 4. Stress Testing, Sensitivity & Model Risk

Under Federal Reserve SR 26-2 model-risk principles (Conceptual Soundness, Outcome Analysis, and Ongoing Monitoring), the process underwent rigorous challenge:

### A. Estimation Window Stress Test (Lab 15)
When recalculating input parameters over the trailing 36-month window (October 2023 – October 2026):
* VTI annualized return rises from 12.30% to 22.00%; volatility falls from 15.83% to 12.63%.
* The optimizer shifts allocation from **65% SGOV / 35% VTI** to **85% SGOV / 15% VTI**.
* **Impact:** A **20 percentage point reduction in equity exposure**. This proves that the optimizer's allocation is highly sensitive to the sample window. Relying on recent short-term equity outperformance creates artificial confidence to de-risk into cash.

### B. Input Parameter Sensitivity & Partner Audit
* **VCIT Shock (Partner Attack):** Increasing VCIT expected return from 1.19% to 3.60% resulted in **0.0 percentage point change** in allocation. Because VCIT carries 7.88% volatility and its return remains below the 6.50% portfolio target, it cannot displace SGOV or VTI in a minimum-variance formulation.
* **VTI Shock:** A 100 bps drop in equity return expectation forces an immediate reallocation to 60% SGOV / 40% VTI (+500 bps equity risk).

### C. Macro Point-in-Time Signal Hygiene (Labs 16 & 17)
To govern rebalancing decisions, external macroeconomic signals must obey strict point-in-time provenance. Using FRED series `T10Y2Y` (10-Year minus 2-Year Treasury spread), the system enforces ALFRED vintage isolation:
* Observations are quarantined until official post-market release (~4:03 PM CDT).
* Trading decisions occur no earlier than the next market session, preventing look-ahead bias and revision contamination.

---

## 5. Implementation Rules, Monitoring, and Reversal Triggers

### Pilot Framework
* **Scope:** 12-month pilot timeframe, capped at a designated sub-portfolio sleeve ($10M–$25M).
* **Monitoring Owner:** Portfolio Analyst & Foundation Risk Officer.
* **Review Frequency:** Monthly performance tracking; formal quarterly committee audit.

### Explicit Reversal & Kill Triggers
The committee should suspend the pilot and revert to cash preservation or a defensive benchmark if any of the following triggers are breached:

1. **Equity Return Expectation Deterioration:** If forward consensus 5-year annualized return for VTI falls below **11.00%**, the model will be forced to allocate $>40\%$ to equities, violating the low-volatility mandate thesis. *Trigger action: Freeze rebalancing; initiate IPS return hurdle review.*
2. **Realized Equity Volatility Spike:** If trailing 12-month realized volatility of VTI exceeds **18.00%**, the diversification benefits of the 65/35 mix break down. *Trigger action: Rebalance to capital preservation.*
3. **Cash Yield Compression:** If Federal Reserve rate cuts compress SGOV yield below **2.50%**, cash can no longer anchor the portfolio's required 6.50% return. *Trigger action: Reopen intermediate fixed income sleeves (VGIT/VCIT).*
4. **Yield Curve Warning:** An ALFRED vintage release of `T10Y2Y` re-inverting below **-0.20%** triggers an emergency risk-committee review before any scheduled quarterly rebalance.

### Conclusion
The 65% SGOV / 35% VTI portfolio is mathematically sound and compliant with all mandate constraints, but its sensitivity to sample length and equity return assumptions warrants disciplined caution. A **Pilot** captures superior risk-adjusted yields while maintaining institutional safety.
