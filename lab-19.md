# Lab 19 — Legend Panel

## My request to AI

> Extend my existing Buffett 10-K skill and Streamlit app into a three-investor panel without removing any Lab 18 behavior. Use the same five annual SEC 10-K facts and the same missing-data rules as Lab 18, and also retrieve and print `Liabilities`, `AssetsCurrent`, and `LiabilitiesCurrent`. Calculate current ratio as current assets ÷ current liabilities only when both inputs are present and current liabilities are nonzero; otherwise display `not known`.
>
> Add reusable Cathie Wood and Burry skills based on their FAskills pages. Make the checks deterministic code, not model judgment: Cathie checks revenue growth, net-income growth, and owner-earnings growth from the first to the last year. Burry checks operating cash flow ≥ net income in every year and latest liabilities ≤ 2 × equity. A missing input must make the affected check `not known`; never estimate it.
>
> Have Buffett, Cathie Wood, and Burry each write a short memo using only values printed by the script. Update the app to show a panel table with investor, check, and `pass`/`fail`/`not known`; show all three verdicts and memos side by side; and flag any number appearing in any memo that the script did not print. Validate COST against the revised panel checks.

Sources used: [Cathie Wood's FAskills page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/cathie_wood.md), [Burry's FAskills page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/michael_burry.md), and [Streamlit documentation](https://docs.streamlit.io/).

## Partner explanation

Buffett would read Costco primarily as a durable business: its 2022–2026 10-K facts show ROE above 15% each year, positive owner earnings each year, and owner earnings growing from $3.5 billion to $9.4 billion. Cathie Wood would read the same historical growth as only a starting point: her page asks whether a company participates in disruptive platforms and can capture an expanding TAM over five years—evidence the shared facts alone cannot establish. Burry would ask a different question: whether income turns into cash and whether liabilities are manageable. Costco passes those two mechanical checks, but Burry's approach still calls for forensic reading of the filing's footnotes rather than treating a pass as proof that no risk exists.

## Same evidence, different lenses

| Investor | What the shared 10-K facts show | Where the investor differs |
|---|---|---|
| Buffett | COST passes all three checks: durable ROE, positive owner earnings, and owner-earnings growth. | Focuses on the business's ability to compound owner earnings. |
| Cathie Wood | COST has growing revenue, net income, and owner earnings over the five years. | Treats those historical growth facts as a proxy only; the fuller innovation thesis needs TAM, cost-curve, and technology evidence. |
| Burry | Operating cash flow exceeds net income in every year and latest liabilities/equity is 1.49, below 2.0. | Treats cash conversion and balance-sheet resilience as the starting point for deeper forensic work, not the conclusion. |

## COST validation

With Cathie Wood replacing Graham, COST passes Buffett's three checks, Cathie's three historical-growth checks, and Burry's two checks. Cathie's memo labels these checks as a limited facts-only growth screen rather than claiming that they prove disruption or a five-year price target.

## Would I trust the panel?

Only with a condition: I would use it to screen companies and to expose the reason for disagreement, but not to make a purchase decision. All three skills share the same limited 10-K facts, so common missing evidence or a weak threshold can produce a tidy but incomplete answer. Before any decision, I would check valuation, the current business context, and the relevant 10-K disclosures and footnotes.

**Project 2 decision:** Only with a condition: I would let the panel screen companies only after every `not known` result is investigated and valuation plus the relevant 10-K footnotes are reviewed separately.

## My Project 2 company

I selected VTI's largest holding, NVIDIA (NVDA), for the company run. The completed app run showed one failed check: Burry's operating-cash-flow-at-least-net-income test. The remaining panel checks passed; the company files 10-Ks, so no fallback holding was needed.

## Explain the Cathie Wood code to my partner

The relevant function is `panel_checks` in `Skill/investor_panel.py`.

1. The `_growth_result` helper takes a five-year list, such as revenue, net income, or owner earnings.
2. `if len(values) != 5 or any(value is None for value in values): return "not known"` stops the check when a year is missing; the code does not estimate it.
3. `return "pass" if float(values[-1]) > float(values[0]) else "fail"` compares the final fiscal year with the first fiscal year when all five values exist.
4. The Cathie Wood section of `panel_checks` calls `_growth_result` three times: once for revenue, once for net income, and once for owner earnings. It returns the three labeled results to the app's panel table.
5. The memo then describes the results as a historical-growth proxy, not proof of disruptive innovation, TAM expansion, or a five-year price target.

**Answer to my partner's missing-input question:** the code never fills the gap. It keeps `None` and returns `not known` for the affected check.

## NVDA partner attack

**Bear case (partner):** NVDA failed Burry's operating-cash-flow-at-least-net-income test in one of the five fiscal years. That break between reported profit and operating cash generation is a reason to inspect working capital and cash-flow quality before trusting the earnings story.

**Bull case (my response):** Re-run NVDA after the panel update and use the Cathie growth results with Buffett's passes and Burry's liabilities-to-equity result. The single cash-conversion failure remains a focused diligence question, not enough by itself to settle the long-horizon growth case.

## What a panel of AI skills is

A panel is a set of reusable investor-specific instructions that reads a common evidence set but applies different deterministic checks. It can disagree honestly because the investors privilege different risks: Buffett emphasizes owner earnings, Cathie Wood emphasizes long-horizon growth, and Burry tests cash backing and leverage. The shared calculations make the disagreement auditable; they do not make it independent investment advice.

## Reflection to explain to my partner

1. **Agreement and split on NVDA:** Re-run the updated panel to record Cathie Wood's three growth-check results beside Buffett and Burry. The prior run showed Burry's cash-conversion test failing because operating cash flow was below net income in at least one fiscal year, pointing to earnings-quality diligence.

2. **What the panel replacement means:** Replacing Graham with Cathie Wood changes the question without changing the 10-K facts: liquidity discipline is no longer the panel's test, and historical growth becomes the available proxy for a long-horizon innovation thesis. A screen's verdict is therefore partly a design choice: the investor lens and its limits must be justified before the output is used as a decision signal.
