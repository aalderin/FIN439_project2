# Project 2 — Validation, Model Risk, and AI-Use Record

**Course:** FIN 43900 (AI in Finance), Purdue University  
**Project:** Project 2 — Investment Management Application  
**Artifact:** `docs/validation-and-ai-use.md`  

> **AI Disclosure:** Antigravity (Anthropic Claude and Google Gemini models) was utilized as an interactive programming and research assistant for code structuring, debugging Streamlit callbacks, refactoring XBRL parsing logic, and organizing sensitivity tables. All model outputs, mathematical calculations, and financial conclusions were independently verified and audited against standard financial principles.  
> **Course Disclaimer:** Built for educational purposes for FIN 43900; this analysis constitutes an academic demonstration, not professional investment advice.

---

## 1. AI-Use Disclosure & Log

### AI Tools Utilized
* **Primary Assistant:** Google Antigravity paired with Anthropic Claude 3.5 Sonnet / Gemini models.
* **Scope of Assistance:**
  * Drafting the interactive Streamlit UI in [`app.py`](../app.py) and [`Skill/buffett_app.py`](../Skill/buffett_app.py).
  * Structuring the 5-point discrete grid-search optimizer in [`portfolio.py`](../portfolio.py).
  * Parsing SEC EDGAR company facts JSON and XBRL tag fallback dictionaries.
  * Formatting Markdown tables and documentation templates.

### Audited AI Output (Detailed Walkthrough)
* **The AI Claim / Output:** During the construction of [`portfolio.py`](../portfolio.py), the AI assistant proposed calculating annualized portfolio variance directly by multiplying monthly returns by 12, but initially proposed annualizing monthly standard deviation by multiplying by 12 (rather than $\sqrt{12}$).
* **Independent Audit & Correction:**
  * In financial mathematics, if monthly returns $R_m$ are independent and identically distributed with variance $\sigma_m^2$, annual variance is:
    $$\sigma_{annual}^2 = 12 \times \sigma_m^2$$
  * Therefore, annual standard deviation (volatility) must scale with the square root of time:
    $$\sigma_{annual} = \sigma_m \times \sqrt{12} \approx 3.4641 \times \sigma_m$$
  * I audited this formula against standard portfolio theory, caught the linear scaling error, and implemented the exact `sqrt(12)` calculation in `portfolio.py` (`estimate_from_csv` function):
    ```python
    volatilities[asset] = stdev(returns[asset]) * sqrt(12) * 100.0
    ```
  * This audit ensured that portfolio volatilities (e.g. SGOV at 0.46% and VTI at 15.83%) match true annualized market risk rather than being distorted by a factor of $\sqrt{12}$.

---

## 2. Locked Changed-Input Record

In accordance with course validation standards (Week 6 pattern), this record documents a pre-committed, AI-off prediction followed by the empirical code run.

| Field | Record Details |
| :--- | :--- |
| **Model / Script** | [`portfolio.py`](../portfolio.py) / [`app.py`](../app.py) |
| **Dataset** | [`prices.csv`](../prices.csv) (60 monthly adjusted closes) |
| **Base Configuration** | Full 60-month sample; 6.5% return objective; 3.0% reserve minimum |
| **Baseline Optimal Mix** | **65% SGOV / 35% VTI** (Return: 6.79%, Volatility: 5.62%, Reserve: 65.0%) |
| **Input Changed** | **VCIT expected return estimate altered from 1.19% to 3.60%** (+241 bps shock) |
| **Pre-Run Prediction (AI-Off)** | **Allocation will remain unchanged (65% SGOV / 35% VTI).**<br>*Rationale:* Even at 3.60%, VCIT's expected return remains substantially below the 6.50% portfolio hurdle. Furthermore, VCIT's volatility (7.88%) is dramatically higher than SGOV's (0.46%). Because SGOV provides a 3.83% return with near-zero risk, blending high-return equity (VTI at 12.30%) with near-cash (SGOV) dominates an intermediate credit allocation. |
| **Observed Post-Run Result** | **Exact allocation: 65% SGOV / 35% VTI** (Largest weight change = **0.00 percentage points**). |
| **Verification Status** | **PASSED.** The empirical execution perfectly confirmed the theoretical prediction. |

---

## 3. Second Stress Run: Estimation Window Sensitivity

| Test Parameter | Full 60-Month Window | Trailing 36-Month Window | Variance / Impact |
| :--- | :---: | :---: | :---: |
| **SGOV Ann. Return / Vol** | 3.83% / 0.46% | 4.38% / 0.22% | +55 bps return / -24 bps vol |
| **VTI Ann. Return / Vol** | 12.30% / 15.83% | 22.00% / 12.63% | +970 bps return / -320 bps vol |
| **Optimal Allocation** | **65% SGOV / 35% VTI** | **85% SGOV / 15% VTI** | **+20.0 pts SGOV / -20.0 pts VTI** |
| **Portfolio Expected Return** | 6.79% | 7.02% | +23 bps |
| **Portfolio Volatility** | 5.62% | 1.95% | -367 bps |

* **Analysis:** Shortening the window creates artificial optimism in equity returns (22.00% annualized). The optimizer exploits this high return by reducing equity exposure to the absolute minimum necessary (15%) to satisfy the 6.5% hurdle, concentrating 85% into short Treasuries. This proves the system's sensitivity to sample horizon and directly justifies the **Pilot (not Adopt)** recommendation.

---

## 4. Partner Audit & Sceptic Defense Record

During the Week 12 studio session, my partner conducted a cold review of the repository and challenged key claims:

### Sceptical Challenge 1 (Data Provenance & Look-Ahead Bias)
* **Partner Question:** *"Why can't we use today's FRED release for T10Y2Y to adjust portfolio weights immediately before the open?"*
* **Response & Evidence:** As documented in [`lab-17-point-in-time.md`](../lab-17-point-in-time.md), FRED daily series (such as `T10Y2Y`) are released at 4:03 PM CDT—after markets close. Using same-day FRED observations to trade at the market open introduces severe look-ahead bias. In [`asof_app.py`](../asof_app.py), our system enforces ALFRED vintage isolation: trades execute on the subsequent trading session based solely on data available as of that historical decision date.

### Sceptical Challenge 2 (Cash Drag in Low-Rate Environments)
* **Partner Question:** *"Your 65% SGOV allocation relies on cash yielding 3.83%. What happens when the Federal Reserve cuts rates to 2.0%?"*
* **Response & Evidence:** This is an explicit reversal trigger documented in [`docs/decision-memo.md`](decision-memo.md). If cash yield compresses below 2.50%, SGOV can no longer serve as the return anchor. Under that condition, the pilot is automatically paused, and the intermediate bond sleeves (VGIT/VCIT) must be reopened to provide duration and income.

### Sceptical Challenge 3 (Investor Skill Hallucination Risk)
* **Partner Question:** *"How do we know the LLM in the Legend Panel isn't inventing numbers for Buffett, Wood, or Burry?"*
* **Response & Evidence:** All financial metrics in [`Skill/buffett_facts.py`](../Skill/buffett_facts.py) and [`Skill/investor_panel.py`](../Skill/investor_panel.py) are computed using deterministic Python functions directly from SEC EDGAR XBRL company facts JSON. The code enforces strict missing-data rules: if a tag is absent, the metric displays `not found` and the check displays `not known`. Furthermore, [`Skill/buffett_app.py`](../Skill/buffett_app.py) runs an automated regex validation scan over the generated memo text and flags any number that was not explicitly printed by the deterministic Python script.

---

## 5. Model Risk Management Principles (Federal Reserve SR 26-2 Alignment)

1. **Conceptual Soundness:** The mean-variance optimization model uses classical modern portfolio theory (Markowitz) with discrete long-only step constraints that reflect real-world implementation.
2. **Outcome Analysis:** Verified against two transparent baselines (Equal-Weight and 60/40 Benchmark). The model demonstrated that the Equal-Weight mix is unviable (4.36% return), while the optimized mix reduces volatility by 46% compared to the 60/40 mix.
3. **Ongoing Monitoring:** Established explicit quantitative reversal triggers (VTI return $<11.0\%$, VTI volatility $>18.0\%$, SGOV yield $<2.50\%$, and `T10Y2Y` spread re-inversion $<-0.20\%$).

