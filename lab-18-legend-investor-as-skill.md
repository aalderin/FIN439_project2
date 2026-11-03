# Lab 18 - Legend Investor as Skill

Lab: [Legend Investor as Skill](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-11/lab-18-legend-investor-as-skill.md)

## Question

> Can an investor's philosophy become a skill an AI runs consistently, with every number computed from the 10-K and judgment left to the model?

## Answer

Yes—if the skill makes the evidence and calculations deterministic.

Code should retrieve only the allowed 10-K facts, apply the same XBRL-tag fallback rules, calculate ROE and owner earnings, and return “not found” or “not known” when evidence is missing. The model can then apply the investor’s qualitative philosophy to those printed results and write the memo.

That makes the process repeatable and auditable, while keeping subjective judgment separate from the numbers.

## My request to AI

> Build a reusable Buffett investor skill in my \`Skill\` folder. Use SEC EDGAR 10-K company facts only and create a Python script that accepts a ticker, prints the last five fiscal years of revenue, net income, operating cash flow, capex, equity, ROE, and owner earnings with their XBRL tags. Follow the rules in this Lab 18 Markdown file, including “not found” and “not known” handling. Then create a Streamlit app that charts owner earnings and net income, shows the table and checks, and displays a Buffett-style memo based only on the script output. Test it with COST and help me fix discrepancies.

## Build requirements

Create a Buffett-investor skill and a Streamlit app. The skill takes a ticker, obtains the company's SEC EDGAR facts with a descriptive User-Agent, and calculates the last five fiscal years from 10-K data only.

| Metric | SEC XBRL tag / calculation |
|---|---|
| Revenue | \`RevenueFromContractWithCustomerExcludingAssessedTax\`, then \`Revenues\` |
| Net income | \`NetIncomeLoss\` |
| Operating cash flow | \`NetCashProvidedByUsedInOperatingActivities\` |
| Capital spending | \`PaymentsToAcquirePropertyPlantAndEquipment\`, then \`PaymentsToAcquireProductiveAssets\` |
| Equity | \`StockholdersEquity\` |
| ROE | Net income / year-end equity |
| Owner earnings | Operating cash flow - capital spending |

The script must use one-year values for flow measures and allow the latest filing to replace an earlier filing for the same fiscal period. It must print the selected XBRL tag next to each value. A missing value stays **not found**; the script must never estimate one. If equity is zero or negative, ROE is **not known**.

## Buffett checks

The code, not the model, evaluates these checks:

| Check | Pass condition |
|---|---|
| Durable return on equity | ROE is at least 15% in every available year |
| Positive owner earnings | Owner earnings are positive in every year |
| Growing owner earnings | Last-year owner earnings exceed first-year owner earnings |

Any check whose input is missing is **not known**.

## COST validation

Costco is the known-answer test. Values are USD millions.

| FY end | Revenue | Net income | Operating cash flow | Capex | Equity | ROE | Owner earnings |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022-08-28 | 226,954 | 5,844 | 7,392 | 3,891 | 20,642 | 28.3% | 3,501 |
| 2023-09-03 | 242,290 | 6,292 | 11,068 | 4,323 | 25,058 | 25.1% | 6,745 |
| 2024-09-01 | 254,453 | 7,367 | 11,339 | 4,710 | 23,622 | 31.2% | 6,629 |
| 2025-08-31 | 275,235 | 8,099 | 13,335 | 5,498 | 29,164 | 27.8% | 7,837 |
| 2026-08-30 | 303,154 | 9,226 | 15,817 | 6,435 | 35,803 | 25.8% | 9,382 |

All three checks pass for COST. JPM is the missing-data test: capital spending and owner earnings should be **not found**, and the two owner-earnings checks should be **not known**.

## Memo and app

The skill saves a short Buffett-style memo as Markdown: **own the business**, **watch it**, or **pass**. The memo can use only numbers printed by the script and judges the business, not its market price.

The Streamlit app must show:

- A five-year chart of owner earnings and net income.
- The data table and the three checks.
- The saved memo, with any number that was not printed by the script flagged.
- The disclosure: "Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice."

## Explain the code

The function \`build_rows\` in \`Skill/buffett_app.py\` turns EDGAR facts into one row for each fiscal year.

- \`for end in fiscal_year_ends(company_facts):\` loops through the five latest fiscal-year-end dates found in SEC data.
- \`row = {"FY end": end}\` starts one table row for that year.
- \`for metric in METRICS:\` loops through revenue, net income, operating cash flow, capital spending, and equity.
- \`row[metric], row[f"{metric} tag"] = choose_metric(...)\` asks \`choose_metric\` to find the correct 10-K value and records the value and XBRL tag used.
- \`income, equity = ...\` and \`ocf, capex = ...\` store the inputs needed for the calculations.
- \`row["ROE"] = ...\` calculates net income divided by equity only when both inputs exist and equity is positive. Otherwise, it stores \`None\`, which the app displays as \`not known\`.
- \`row["Owner earnings"] = ...\` calculates operating cash flow minus capital spending only when both inputs exist. Otherwise, it stores \`None\`.
- \`rows.append(row)\` saves the completed fiscal-year row, and \`return rows\` sends the five rows to the chart, table, and checks.

### Where “not found” comes from

In \`choose_metric\`, this line runs when neither the preferred XBRL tag nor its fallback has a valid 10-K value for that fiscal year:

\`\`\`python
return None, "not found"
\`\`\`

\`None\` is stored as the missing number. Later, \`display_value\` converts \`None\` to the text \`"not found"\` for the table. This is why JPM's capital spending and owner earnings remain missing rather than being estimated.

## Decision

I trust Buffett's verdict on COST because the five years of 10-K data show ROE above 15% every year, positive owner earnings every year, and owner earnings growing from $3.5 billion to $9.4 billion. The verdict is supported by repeatable SEC calculations rather than invented numbers.

## Agent skills — Learn on your own

### 1. What is it?

A skill is a reusable folder of instructions for an AI. Its required file is \`SKILL.md\`, which tells the AI what task it handles and the rules to follow.

### 2. How does it work?

The AI reads the name and description first because they are a quick label for deciding whether the skill applies. It reads the rest of \`SKILL.md\` only when the request matches, which saves context and prevents unrelated instructions from affecting other tasks.

### 3. Why do the numbers belong in code, not in the model?

Numbers belong in code because code can retrieve the same 10-K facts, apply the same XBRL-tag rules, and calculate ROE and owner earnings the same way every time. A model can misunderstand, estimate, or invent a number; code can show \`not found\` when the filing does not supply the needed data. The model should use the verified output to make the business judgment, not create the evidence.

## Reflection

### What the skill makes the same every time

The skill makes the evidence process consistent: it uses SEC EDGAR 10-K facts, selects the same XBRL tags and fallback tags, uses the latest filing for a repeated period, calculates ROE and owner earnings in code, and applies the same three Buffett checks. It leaves the qualitative judgment to the model: whether the printed business results support owning, watching, or passing on the business, and the explanation for that verdict.

### Why “not found” is better than an estimate

“Not found” is better because it makes the evidence gap visible. An estimate could look precise even though it did not come from the company's 10-K and could change the owner-earnings calculation or verdict. By keeping the value missing and marking the affected check “not known,” the skill is honest about what the available evidence can and cannot support.
