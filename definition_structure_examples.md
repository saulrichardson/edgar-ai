# How Definitions Are Tied to Economic Terms in the Output

## Structure Pattern: Each term has its definition as a sibling field

### Example 1: Interest Rate Benchmark
```json
"base_interest_rate": {
  "rate_type": "floating",
  "benchmark": "LIBO Rate",
  "benchmark_definition": "interest rate per annum for deposits in dollars for a period equal to the relevant interest period which appears on Telerate Page 3750",
  "spread_bps": 225
}
```
**Pattern:** `benchmark` field paired with `benchmark_definition` field

---

### Example 2: Financial Covenant
```json
"financial_covenants": [
  {
    "metric": "Leverage Ratio",
    "definition": "Total Debt divided by EBITDA for the period consisting of such fiscal quarter and each of the three immediately preceding fiscal quarters",
    "requirement": "maximum",
    "threshold_value": 6.35,
    "test_frequency": "quarterly"
  }
]
```
**Pattern:** `metric` field paired with `definition` field

---

### Example 3: Prepayment Trigger
```json
"mandatory_prepayments": [
  {
    "trigger": "Excess Cash Flow",
    "definition": "EBITDA minus interest expense, scheduled principal repayments, income taxes, capital expenditures, investments, restricted payments, and interest payments",
    "percentage": 0.5,
    "application": "to term loans in order of maturity"
  }
]
```
**Pattern:** `trigger` field paired with `definition` field

---

### Example 4: Fee Calculation
```json
"fees": [
  {
    "fee_type": "commitment",
    "amount_or_rate": 50,
    "rate_basis": "basis points per annum on unused commitments",
    "unused_commitment_definition": "Total Commitments minus outstanding Loans, as calculated daily",
    "payment_timing": "quarterly in arrears"
  }
]
```
**Pattern:** Specific calculation term gets its own definition field (e.g., `unused_commitment_definition`)

---

### Example 5: Administrative Voting
```json
"governing_terms": {
  "amendment_threshold": "Required Lenders",
  "required_lenders_definition": "Lenders holding more than 50% of the aggregate Commitments and Loans outstanding"
}
```
**Pattern:** Voting term paired with its specific definition field

---

## The Naming Convention:

1. **Generic pattern:** `[term]` + `definition`
   - `metric` → `definition`
   - `trigger` → `definition`

2. **Specific pattern:** `[specific_term]_definition`
   - `benchmark` → `benchmark_definition`
   - `unused_commitment` → `unused_commitment_definition`
   - `required_lenders` → `required_lenders_definition`

## Why This Works Well:

✅ **Co-located:** Definition is right next to the term it defines
✅ **Clear naming:** `_definition` suffix makes it obvious what the field contains
✅ **Queryable:** Can easily find all definitions by searching for "definition" fields
✅ **Self-contained:** Each economic term carries its own context
✅ **Machine-readable:** Consistent structure for automated processing

## Full Example - Performance Pricing Grid:
```json
"performance_pricing": [
  {
    "metric": "Leverage Ratio",
    "definition": "Total Debt divided by EBITDA for the period consisting of such fiscal quarter and each of the three immediately preceding fiscal quarters",
    "pricing_grid": [
      {"condition": "> 5.50:1.0", "spread_adjustment_bps": 225},
      {"condition": "5.00:1.0 to 5.50:1.0", "spread_adjustment_bps": 200},
      {"condition": "4.50:1.0 to 5.00:1.0", "spread_adjustment_bps": 175}
    ],
    "test_frequency": "quarterly"
  }
]
```

The definition is embedded right in the object that uses it, making the output completely self-documenting.