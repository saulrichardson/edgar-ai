#!/usr/bin/env python3
"""Direct OpenAI API call to test extraction with claude-3-5-sonnet (4.1-nano)"""

import os
import json
import openai
from pathlib import Path
from datetime import datetime

# Read the API key from .env
env_path = Path(".env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "EDGAR_AI_OPENAI_API_KEY" in line:
                api_key = line.split("=")[1].strip()
                os.environ["OPENAI_API_KEY"] = api_key
                break

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load the extraction prompt
prompt_path = Path("schema_analysis/FINAL_universal_debt_extraction_prompt.md")
extraction_prompt = prompt_path.read_text()

# Load the RF Monolithics loan document
doc_path = Path("rf_monolithics_loan.txt")
doc_text = doc_path.read_text()

# Truncate document for testing (to avoid token limits)
# Take first 10,000 characters which should include key terms
doc_text_truncated = doc_text[:10000]

print("=" * 80)
print("Direct OpenAI Extraction Test")
print("=" * 80)
print(f"Document: RF Monolithics Loan Agreement")
print(f"Document size: {len(doc_text)} characters (using first 10,000)")
print(f"Model: gpt-4.1-nano")
print("=" * 80)

# Create output directory
output_dir = Path("schema_analysis/rf_monolithics_extraction")
output_dir.mkdir(exist_ok=True)

try:
    print("\nCalling OpenAI API for extraction...")
    print("This may take a moment...\n")
    
    # Create the messages
    messages = [
        {
            "role": "system", 
            "content": "You are a financial document analyzer specializing in debt instruments. Extract information exactly as requested and return only JSON."
        },
        {
            "role": "user",
            "content": f"{extraction_prompt}\n\n---\n\nNow extract all economic terms from this loan agreement:\n\n{doc_text_truncated}"
        }
    ]
    
    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4.1-nano",  # New model as requested
        messages=messages,
        temperature=0.1,
        max_tokens=4000,
        response_format={"type": "json_object"}  # Force JSON response
    )
    
    # Get the content
    content = response.choices[0].message.content
    
    # Save raw response
    with open(output_dir / "openai_raw_response.txt", 'w') as f:
        f.write(content)
    
    # Parse JSON
    extracted_data = json.loads(content)
    
    # Save extraction results
    output_file = output_dir / "openai_extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
            "document_id": "rf_monolithics_loan",
            "model": "gpt-4.1-nano",
            "api": "openai_direct",
            "document_length_processed": len(doc_text_truncated),
            "total_document_length": len(doc_text),
            "extracted_data": extracted_data
        }, f, indent=2)
    
    print(f"✓ Extraction complete! Results saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    
    # Document basics
    print(f"\nDocument Type: {extracted_data.get('document_type', 'Not identified')}")
    print(f"Effective Date: {extracted_data.get('effective_date', 'Not found')}")
    
    # Parties and amounts
    if 'obligations' in extracted_data:
        parties = extracted_data['obligations'].get('parties', [])
        commitments = extracted_data['obligations'].get('commitments', [])
        
        print(f"\nParties ({len(parties)}):")
        for party in parties[:5]:
            print(f"  - {party.get('name')} ({party.get('role')})")
        
        if commitments:
            print(f"\nFacilities ({len(commitments)}):")
            for comm in commitments:
                amount = comm.get('amount', 0)
                print(f"  - {comm.get('facility_type')}: ${amount:,.0f} {comm.get('currency', '')}")
    
    # Interest rates
    if 'pricing' in extracted_data:
        base_rate = extracted_data['pricing'].get('base_interest_rate', {})
        if base_rate:
            print(f"\nInterest Rate:")
            print(f"  - Type: {base_rate.get('rate_type')}")
            print(f"  - Benchmark: {base_rate.get('benchmark')}")
            print(f"  - Spread: {base_rate.get('spread_bps')} bps")
            print(f"  - Floor: {base_rate.get('floor_bps')} bps")
    
    # Maturity
    if 'repayment' in extracted_data:
        maturity = extracted_data['repayment'].get('maturity', {})
        if maturity:
            print(f"\nMaturity Date: {maturity.get('final_maturity_date')}")
    
    # Covenants summary
    if 'conditions' in extracted_data:
        fin_covs = len(extracted_data['conditions'].get('financial_covenants', []))
        neg_covs = len(extracted_data['conditions'].get('negative_covenants', []))
        defaults = len(extracted_data['conditions'].get('events_of_default', []))
        
        if any([fin_covs, neg_covs, defaults]):
            print(f"\nCovenants & Conditions:")
            if fin_covs: print(f"  - Financial Covenants: {fin_covs}")
            if neg_covs: print(f"  - Negative Covenants: {neg_covs}")
            if defaults: print(f"  - Events of Default: {defaults}")
    
    # Fees
    if 'fees_and_costs' in extracted_data:
        fees = extracted_data['fees_and_costs'].get('fees', [])
        if fees:
            print(f"\nFees ({len(fees)}):")
            for fee in fees[:3]:
                print(f"  - {fee.get('fee_type')}: {fee.get('amount_or_rate')} bps")
    
    # Create markdown report
    report_path = output_dir / "extraction_report.md"
    with open(report_path, 'w') as f:
        f.write("# RF Monolithics Loan - Extraction Results\n\n")
        f.write(f"**Model**: gpt-4.1-nano\n")
        f.write(f"**Extraction Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"**Document Length**: {len(doc_text_truncated):,} characters analyzed\n\n")
        
        f.write("## Key Terms Extracted\n\n")
        f.write("```json\n")
        f.write(json.dumps(extracted_data, indent=2)[:2000])
        if len(json.dumps(extracted_data)) > 2000:
            f.write("\n... (truncated)")
        f.write("\n```\n")
    
    print(f"\n✓ Report saved to {report_path}")
    
    # Test data quality
    print("\n" + "-" * 40)
    print("DATA QUALITY CHECKS")
    print("-" * 40)
    
    # Check numeric conversions
    issues = []
    successes = []
    
    if 'obligations' in extracted_data:
        for comm in extracted_data['obligations'].get('commitments', []):
            if isinstance(comm.get('amount'), (int, float)):
                successes.append("✓ Amount is numeric")
            else:
                issues.append(f"✗ Amount not numeric: {comm.get('amount')}")
    
    if 'pricing' in extracted_data:
        base_rate = extracted_data['pricing'].get('base_interest_rate', {})
        if isinstance(base_rate.get('spread_bps'), (int, float)):
            successes.append(f"✓ Spread in basis points: {base_rate.get('spread_bps')}")
        else:
            issues.append(f"✗ Spread not numeric: {base_rate.get('spread_bps')}")
    
    for success in successes[:3]:
        print(success)
    for issue in issues[:3]:
        print(issue)
    
    if not issues:
        print("\n✓ All numeric conversions successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    
    error_file = output_dir / "openai_error.txt"
    with open(error_file, 'w') as f:
        f.write(f"Error: {e}\n\n")
        traceback.print_exc(file=f)
        if 'content' in locals():
            f.write(f"\n\nRaw content:\n{content}")
    
    print(f"Error details saved to {error_file}")
    traceback.print_exc()