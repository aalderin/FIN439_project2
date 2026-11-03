---
name: buffett-10k-investor
description: Analyze a public company's last five 10-K fiscal years with Buffett-style business-quality checks using SEC EDGAR facts. Use when asked to produce an evidence-based investor memo without using market-price data.
---

# Buffett 10-K Investor

Use this skill to evaluate the quality of a business from SEC EDGAR 10-K facts. Keep the evidence-gathering and calculations in code; use the model only to interpret the printed results.

## Data rules

- Download the SEC ticker-to-CIK file and the company's \`companyfacts\` JSON directly from SEC EDGAR. Do not use paid data services.
- Send a descriptive \`User-Agent\` containing the user's name and email address. If those details are unavailable, ask for them before making the SEC request.
- Use 10-K facts only and present the latest five fiscal years, labeled with their fiscal-year-end dates.
- Use one-year durations for revenue, net income, operating cash flow, and capital spending.
- When multiple filings report the same fiscal period, use the latest filing.
- Do not estimate missing data. Print \`not found\` instead.

## Metrics

Print each metric with the XBRL tag used.

| Metric | Tag or calculation |
|---|---|
| Revenue | \`RevenueFromContractWithCustomerExcludingAssessedTax\`; fall back to \`Revenues\` |
| Net income | \`NetIncomeLoss\` |
| Operating cash flow | \`NetCashProvidedByUsedInOperatingActivities\` |
| Capital spending | \`PaymentsToAcquirePropertyPlantAndEquipment\`; fall back to \`PaymentsToAcquireProductiveAssets\` |
| Equity | \`StockholdersEquity\` |
| ROE | Net income / year-end equity |
| Owner earnings | Operating cash flow - capital spending |

If equity is zero or below, report ROE as \`not known\`. If an input to a check is missing, report that check as \`not known\`.

## Required checks

Compute and print these checks in code:

1. ROE is at least 15% in every year.
2. Owner earnings are positive in every year.
3. Owner earnings grew from the first year to the last year.

## Memo

After the script has printed the table and checks, write a short Buffett-style Markdown memo with one verdict: **own the business**, **watch it**, or **pass**.

Use only the numbers printed by the script. Judge the business, not its price: do not use price data, valuation multiples, or unverified numbers. If owner earnings are unavailable, say that the owner-earnings portion of the judgment cannot be made.

## App and validation

When implementing this skill, create a Streamlit app that accepts a ticker and:

- charts owner earnings and net income over the five fiscal years;
- displays the calculated table and the three checks;
- displays the saved memo and flags every number in it that the script did not print; and
- includes this disclosure under the title: "Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice."

Validate the data logic with \`COST\`. Its five-year values must match the Lab 18 validation table before considering the implementation complete. Test \`JPM\` as a missing-data case: capital spending and owner earnings must remain \`not found\`, and the owner-earnings checks must be \`not known\`.
