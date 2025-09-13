#!/usr/bin/env python3
"""Test the latest universal debt extraction prompt on rf_monolithics_loan.txt"""

import os
import json
from pathlib import Path
from datetime import datetime

# Set environment
os.environ["EDGAR_AI_VERBOSE"] = "1"

from edgar_ai.interfaces import Document
from edgar_ai.clients import llm_gateway
from edgar_ai.config import settings

# Load the extraction prompt
prompt_path = Path("schema_analysis/FINAL_universal_debt_extraction_prompt.md")
extraction_prompt = prompt_path.read_text()

# Load the RF Monolithics loan document
doc_path = Path("rf_monolithics_loan.txt")
doc_text = doc_path.read_text()

# Create document
doc = Document(
    doc_id="rf_monolithics_loan",
    text=doc_text
)

print("=" * 80)
print("Testing Latest Universal Debt Extraction System")
print("=" * 80)
print(f"Document: {doc.doc_id}")
print(f"Document size: {len(doc.text)} characters")
print(f"Model: claude-3-5-sonnet-20241022 (4.1-nano)")
print("=" * 80)

# Create output directory
output_dir = Path("schema_analysis/rf_monolithics_extraction")
output_dir.mkdir(exist_ok=True)

try:
    print("\nExtracting economic terms...")
    print("This may take a moment as the document is analyzed...\n")
    
    # Call LLM with lower temperature for consistent extraction
    messages = [
        {"role": "system", "content": "You are a financial document analyzer specializing in debt instruments."},
        {"role": "user", "content": f"{extraction_prompt}\n\n---\n\nNow extract all economic terms from this loan agreement:\n\n{doc.text}"}
    ]
    
    # Override model to use 4.1-nano (claude-3-5-sonnet)
    response = llm_gateway.chat_completions(
        model="claude-3-5-sonnet-20241022",
        messages=messages,
        temperature=0.1
    )
    
    # Parse response
    content = response["choices"][0]["message"]["content"]
    
    # Save raw response
    with open(output_dir / "raw_response.txt", 'w') as f:
        f.write(content)
    
    # Extract JSON from response
    if "```json" in content:
        json_start = content.find("```json") + 7
        json_end = content.rfind("```")
        json_str = content[json_start:json_end].strip()
    else:
        # Try to find JSON object directly
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        json_str = content[json_start:json_end]
    
    # Parse JSON
    extracted_data = json.loads(json_str)
    
    # Save extraction results
    output_file = output_dir / "extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
            "document_id": doc.doc_id,
            "model": "claude-3-5-sonnet-20241022",
            "document_length": len(doc.text),
            "extracted_data": extracted_data
        }, f, indent=2)
    
    print(f"✓ Extraction complete! Results saved to {output_file}")
    
    # Print comprehensive summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    
    # Document type and date
    print(f"\nDocument Type: {extracted_data.get('document_type', 'Not identified')}")
    print(f"Effective Date: {extracted_data.get('effective_date', 'Not found')}")
    
    # Obligations summary
    if 'obligations' in extracted_data:
        parties = extracted_data['obligations'].get('parties', [])
        commitments = extracted_data['obligations'].get('commitments', [])
        print(f"\nParties: {len(parties)} identified")
        for party in parties[:3]:  # Show first 3
            print(f"  - {party.get('name', 'Unknown')} ({party.get('role', 'Unknown role')})")
        if len(parties) > 3:
            print(f"  ... and {len(parties) - 3} more")
            
        print(f"\nCommitments: {len(commitments)} facilities")
        total_amount = sum(c.get('amount', 0) for c in commitments)
        print(f"  Total amount: ${total_amount:,.0f}")
    
    # Pricing summary
    if 'pricing' in extracted_data:
        base_rate = extracted_data['pricing'].get('base_interest_rate', {})
        if base_rate:
            print(f"\nBase Interest Rate:")
            print(f"  - Type: {base_rate.get('rate_type', 'Unknown')}")
            print(f"  - Benchmark: {base_rate.get('benchmark', 'Unknown')}")
            print(f"  - Spread: {base_rate.get('spread_bps', 'Unknown')} bps")
            
        perf_pricing = extracted_data['pricing'].get('performance_pricing', [])
        if perf_pricing:
            print(f"\nPerformance Pricing: {len(perf_pricing)} grids")
    
    # Covenants summary
    if 'conditions' in extracted_data:
        fin_covs = extracted_data['conditions'].get('financial_covenants', [])
        neg_covs = extracted_data['conditions'].get('negative_covenants', [])
        defaults = extracted_data['conditions'].get('events_of_default', [])
        
        print(f"\nCovenants and Conditions:")
        print(f"  - Financial Covenants: {len(fin_covs)}")
        print(f"  - Negative Covenants: {len(neg_covs)}")
        print(f"  - Events of Default: {len(defaults)}")
    
    # Fees summary
    if 'fees_and_costs' in extracted_data:
        fees = extracted_data['fees_and_costs'].get('fees', [])
        print(f"\nFees: {len(fees)} types")
        for fee in fees[:3]:
            print(f"  - {fee.get('fee_type', 'Unknown')}: {fee.get('amount_or_rate', 'Unknown')} bps")
    
    # Security summary
    if 'security_and_guarantees' in extracted_data:
        security = extracted_data['security_and_guarantees'].get('security', {})
        guarantees = extracted_data['security_and_guarantees'].get('guarantees', [])
        print(f"\nSecurity:")
        print(f"  - Secured: {security.get('secured', 'Unknown')}")
        print(f"  - Guarantees: {len(guarantees)}")
    
    # Coverage analysis
    print("\n" + "-" * 40)
    print("SCHEMA COVERAGE ANALYSIS")
    print("-" * 40)
    
    categories = ['obligations', 'pricing', 'repayment', 'conditions', 
                  'fees_and_costs', 'security_and_guarantees', 'administrative']
    
    populated = 0
    for cat in categories:
        if cat in extracted_data:
            cat_data = extracted_data[cat]
            if cat_data and (isinstance(cat_data, dict) and any(cat_data.values()) or 
                           isinstance(cat_data, list) and len(cat_data) > 0):
                populated += 1
                print(f"✓ {cat}")
            else:
                print(f"○ {cat} (empty)")
        else:
            print(f"✗ {cat} (missing)")
    
    print(f"\nCoverage: {populated}/{len(categories)} ({populated/len(categories)*100:.1f}%)")
    
    # Data quality checks
    print("\n" + "-" * 40)
    print("DATA QUALITY CHECKS")
    print("-" * 40)
    
    # Check numeric standardization
    print("\nNumeric Standardization:")
    
    # Check if amounts are numbers
    if 'obligations' in extracted_data:
        for commitment in extracted_data['obligations'].get('commitments', []):
            amount = commitment.get('amount')
            if isinstance(amount, (int, float)):
                print(f"✓ Amount properly numeric: {amount:,.0f}")
            else:
                print(f"✗ Amount not numeric: {amount}")
    
    # Check if spreads are in basis points
    if 'pricing' in extracted_data:
        base_rate = extracted_data['pricing'].get('base_interest_rate', {})
        spread = base_rate.get('spread_bps')
        if isinstance(spread, (int, float)):
            print(f"✓ Spread in basis points: {spread}")
        else:
            print(f"✗ Spread not properly converted: {spread}")
    
    # Check date formatting
    print("\nDate Formatting:")
    dates_found = []
    
    if extracted_data.get('effective_date'):
        dates_found.append(('Effective Date', extracted_data['effective_date']))
    
    if 'repayment' in extracted_data:
        maturity = extracted_data['repayment'].get('maturity', {})
        if maturity.get('final_maturity_date'):
            dates_found.append(('Maturity Date', maturity['final_maturity_date']))
    
    for date_type, date_val in dates_found:
        if isinstance(date_val, str) and len(date_val) == 10 and date_val[4] == '-':
            print(f"✓ {date_type}: {date_val} (correct format)")
        else:
            print(f"✗ {date_type}: {date_val} (incorrect format)")
    
    # Save analysis report
    report_path = output_dir / "analysis_report.txt"
    with open(report_path, 'w') as f:
        f.write("RF MONOLITHICS LOAN EXTRACTION ANALYSIS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Extraction Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Document: {doc.doc_id}\n")
        f.write(f"Document Size: {len(doc.text):,} characters\n")
        f.write(f"Model: claude-3-5-sonnet-20241022\n\n")
        
        f.write("Key Findings:\n")
        f.write(f"- Document Type: {extracted_data.get('document_type', 'Not identified')}\n")
        f.write(f"- Total Facilities: {len(commitments) if 'obligations' in extracted_data else 0}\n")
        f.write(f"- Total Amount: ${total_amount:,.0f}\n" if 'total_amount' in locals() else "")
        f.write(f"- Schema Coverage: {populated}/{len(categories)} categories\n")
        
    print(f"\n✓ Analysis report saved to {report_path}")

except json.JSONDecodeError as e:
    print(f"\n❌ Error parsing JSON response: {e}")
    print("\nAttempting to save raw response for debugging...")
    error_file = output_dir / "extraction_error.txt"
    with open(error_file, 'w') as f:
        f.write(f"JSON Parse Error: {e}\n\n")
        f.write("Raw Response:\n")
        f.write(content if 'content' in locals() else "No response received")
    print(f"Error details saved to {error_file}")
    
except Exception as e:
    print(f"\n❌ Error during extraction: {e}")
    import traceback
    traceback.print_exc()
    
    error_file = output_dir / "extraction_error.txt"
    with open(error_file, 'w') as f:
        f.write(f"Error: {e}\n\n")
        traceback.print_exc(file=f)
    print(f"\nError details saved to {error_file}")