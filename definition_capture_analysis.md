# Definition Capture Analysis: Credit Agreement Extraction

## Definitions Successfully Captured ✅

### 1. **Core Financial Metrics**
- **Leverage Ratio**: "Total Debt divided by EBITDA for the period consisting of such fiscal quarter and each of the three immediately preceding fiscal quarters"
  - ✅ Properly captures the TTM (trailing twelve months) calculation method
  - ✅ Used consistently in both performance pricing grid and financial covenants

- **Fixed Charge Coverage Ratio**: "EBITDA minus capital expenditures divided by fixed charges"
  - ✅ Basic calculation captured
  - ⚠️ Missing: Definition of what constitutes "fixed charges" (likely interest + scheduled principal)

### 2. **Interest Rate Components**
- **LIBO Rate (Benchmark)**: "interest rate per annum for deposits in dollars for a period equal to the relevant interest period which appears on Telerate Page 3750"
  - ✅ Specific source and methodology captured

### 3. **Cash Flow & Prepayment Triggers**
- **Excess Cash Flow**: "EBITDA minus interest expense, scheduled principal repayments, income taxes, capital expenditures, investments, restricted payments, and interest payments"
  - ✅ Complete list of deductions captured
  
- **Net Disposition Proceeds**: "gross cash proceeds from disposition minus reasonable and customary fees, taxes, and payments to retire indebtedness"
  - ✅ Clear netting methodology

### 4. **Administrative Terms**
- **Required Lenders**: "Lenders holding more than 50% of the aggregate Commitments and Loans outstanding"
  - ✅ Voting threshold clearly defined

- **Unused Commitment**: "Total Commitments minus outstanding Loans, as calculated daily"
  - ✅ Calculation method for commitment fees

### 5. **Negative Covenant Baskets**
- **Available Amount (for dividends)**: "50% of cumulative net income from closing date"
  - ✅ Basic builder basket concept captured

## Critical Definitions Missing or Incomplete ❌

### 1. **EBITDA Components**
From source document: "EBITDA means, for any applicable period, the sum of (a) the excess of (i) net income (excluding any non-cash revenues included in the computation of net income) over (ii) restricted payments permitted under clauses (c) and (d) of section 7.2.6, plus (b) to the extent deducted in determining net income, the sum of (i) amounts attributable to amortization, (ii) income tax expense, (iii) interest expense, (iv) depreciation of assets and (v) other non-cash, non-recurring charges"

**Missing elements:**
- ❌ Exclusion of non-cash revenues
- ❌ Adjustment for restricted payments
- ❌ Non-recurring charges treatment

### 2. **Total Debt Definition**
- ❌ Not captured at all
- Critical for understanding what's included (e.g., capital leases, guarantees, letters of credit)

### 3. **Fixed Charges Definition**
- ❌ Only partially captured in Fixed Charge Coverage Ratio
- Missing what specific charges are included (interest, principal, lease payments, etc.)

### 4. **Net Income Definition**
- ❌ Not captured
- Important for understanding GAAP vs adjusted basis

### 5. **Capital Expenditures Definition**
From source: "Capital Expenditures means... expenditures for fixed or capital assets... [including] acquisition of all the capital securities of an entity that owns fixed or capital assets"
- ❌ Missing the inclusion of acquisitions as capex

## Economic Impact Assessment

### High Impact Missing Definitions 🔴
1. **EBITDA adjustments** - Can materially affect covenant calculations
2. **Total Debt composition** - Critical for leverage ratio accuracy
3. **Fixed Charges details** - Essential for coverage ratio calculations

### Medium Impact Missing Definitions 🟡
1. **Net Income basis** - Important for builder baskets
2. **Capital Expenditures scope** - Affects excess cash flow sweeps

### Low Impact (Adequately Captured) 🟢
1. **Benchmark rates** - Well defined
2. **Voting thresholds** - Clear
3. **Basic prepayment triggers** - Sufficient detail

## Recommendations for Prompt Enhancement

1. **Add explicit requests for base component definitions:**
   - When capturing EBITDA-based metrics, also capture EBITDA definition
   - When capturing debt ratios, also capture Total Debt definition
   - When capturing coverage ratios, also capture Fixed Charges definition

2. **Create definition dependencies:**
   - If Leverage Ratio is mentioned → require Total Debt AND EBITDA definitions
   - If Coverage Ratio is mentioned → require Fixed Charges definition
   - If builder baskets mentioned → require Net Income definition

3. **Add validation checks:**
   - Flag when a metric uses undefined terms
   - Request recursive definition capture (define the terms used in definitions)

## Overall Assessment

**Definition Capture Score: 7/10**

✅ **Strengths:**
- Captures primary calculation methods well
- Gets benchmark and administrative definitions
- Includes most prepayment trigger definitions

❌ **Weaknesses:**
- Misses foundational GAAP metric definitions (EBITDA, Net Income, Total Debt)
- Doesn't capture full adjustment methodology
- Lacks recursive definition depth

The enhanced prompt successfully captures ~70% of economically critical definitions, but misses some foundational components that could affect modeling accuracy by 10-20% in covenant calculations.