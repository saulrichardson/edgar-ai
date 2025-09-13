#!/usr/bin/env python3
"""Test the Universal Debt Economics Schema on a credit agreement."""

import os
import json
from pathlib import Path
from datetime import datetime

# Set environment
os.environ["EDGAR_AI_VERBOSE"] = "1"

from edgar_ai.interfaces import Document
from edgar_ai.clients import llm_gateway
from edgar_ai.config import settings

# Load the universal schema
schema_path = Path("schema_analysis/universal_debt_economics_schema.json")
with open(schema_path) as f:
    universal_schema = json.load(f)

# Load the credit agreement
doc_path = Path("tests/fixtures/credit_agreement.txt")
doc_text = doc_path.read_text()

# Create the extraction prompt
extraction_prompt = f"""
You are a financial document analyzer specializing in debt instruments.

{json.dumps(universal_schema['extraction_instructions'])}

For each category below, extract ALL relevant information found in the document:

{json.dumps(universal_schema['term_definitions'], indent=2)}

Return a JSON object following this exact structure:
{json.dumps(universal_schema['output_format'], indent=2)}

Important:
- Use empty arrays [] for categories with no relevant information
- Preserve exact text for complex terms
- Include source quotes in a "source_text" field when helpful
- For dates, use YYYY-MM-DD format
- For amounts, use numeric values without currency symbols
"""

# Create document
doc = Document(
    doc_id="credit_agreement_test",
    text=doc_text
)

print("=" * 80)
print("Testing Universal Debt Economics Schema")
print("=" * 80)
print(f"Document: {doc.doc_id}")
print(f"Document size: {len(doc.text)} characters")
print(f"Schema version: {universal_schema['version']}")
print("=" * 80)

try:
    print("\nExtracting economic terms using universal schema...")
    
    # Call LLM
    messages = [
        {"role": "system", "content": extraction_prompt},
        {"role": "user", "content": f"Extract all economic terms from this credit agreement:\n\n{doc.text}"}
    ]
    
    response = llm_gateway.chat_completions(
        model=settings.model_extractor,
        messages=messages,
        temperature=0.1  # Low temperature for consistent extraction
    )
    
    # Parse response
    content = response["choices"][0]["message"]["content"]
    
    # Try to extract JSON from the response
    if "```json" in content:
        json_start = content.find("```json") + 7
        json_end = content.rfind("```")
        json_str = content[json_start:json_end].strip()
    else:
        json_str = content
    
    extracted_data = json.loads(json_str)
    
    # Save the extraction
    output_path = Path("schema_analysis/universal_schema_extraction_result.json")
    with open(output_path, 'w') as f:
        json.dump({
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
            "document_id": doc.doc_id,
            "schema_version": universal_schema['version'],
            "extracted_data": extracted_data
        }, f, indent=2)
    
    print(f"\n✓ Extraction complete! Saved to {output_path}")
    
    # Print summary
    print("\n" + "-" * 40)
    print("EXTRACTION SUMMARY")
    print("-" * 40)
    
    for category, items in extracted_data.items():
        if isinstance(items, list):
            print(f"\n{category.upper()}: {len(items)} items")
            if items and len(items) > 0:
                # Show first item as example
                print(f"  Example: {json.dumps(items[0], indent=2)[:200]}...")
        else:
            print(f"\n{category.upper()}: {items}")
    
    # Analyze completeness
    print("\n" + "-" * 40)
    print("SCHEMA COVERAGE ANALYSIS")
    print("-" * 40)
    
    total_categories = len([k for k in universal_schema['term_definitions'].keys()])
    populated_categories = len([k for k, v in extracted_data.items() if v and (isinstance(v, str) or len(v) > 0)])
    
    print(f"Categories with data: {populated_categories}/{total_categories}")
    print(f"Coverage: {populated_categories/total_categories*100:.1f}%")
    
    # Check for key economic terms
    print("\nKey Economic Terms Found:")
    
    # Principal/Commitments
    if 'obligations' in extracted_data and extracted_data['obligations']:
        commitments = [c for c in extracted_data['obligations'] if 'commitments' in str(c)]
        print(f"✓ Commitments: {len(commitments)} facilities")
    
    # Pricing
    if 'pricing' in extracted_data and extracted_data['pricing']:
        print(f"✓ Pricing terms: {len(extracted_data['pricing'])} items")
    
    # Covenants
    if 'conditions' in extracted_data and extracted_data['conditions']:
        financial_covs = [c for c in extracted_data['conditions'] if 'financial_covenant' in str(c).lower()]
        print(f"✓ Financial covenants: {len(financial_covs)}")
    
    # Maturity
    if 'repayment' in extracted_data and extracted_data['repayment']:
        maturity_items = [r for r in extracted_data['repayment'] if 'maturity' in str(r)]
        print(f"✓ Maturity terms: {len(maturity_items)}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Save error for debugging
    error_path = Path("schema_analysis/universal_schema_error.txt")
    with open(error_path, 'w') as f:
        f.write(f"Error: {e}\n\n")
        traceback.print_exc(file=f)
        if 'content' in locals():
            f.write(f"\n\nRaw LLM Response:\n{content}")
    
    print(f"\nError details saved to {error_path}")