#!/usr/bin/env python3
"""Compare extraction with and without definition capture."""

import json
import os
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("EDGAR_AI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No OpenAI API key found")
client = OpenAI(api_key=api_key)

# Basic prompt without definition emphasis
BASIC_PROMPT = """Extract the key economic terms from this credit agreement in JSON format.
Include: parties, commitments, interest rates, covenants, fees, and repayment terms."""

def load_enhanced_prompt():
    """Load the enhanced extraction prompt."""
    prompt_path = Path("FINAL_enhanced_debt_extraction_prompt.md")
    return prompt_path.read_text()

def extract_document(document_text, system_prompt):
    """Run extraction with given prompt."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract terms from this agreement:\n\n{document_text}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def count_definitions(extraction):
    """Count definition fields in extraction."""
    count = 0
    definitions = []
    
    def search(obj, path=""):
        nonlocal count
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if "definition" in key.lower() and value:
                    count += 1
                    definitions.append({
                        "field": new_path,
                        "value": str(value)[:150]
                    })
                search(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search(item, f"{path}[{i}]")
    
    search(extraction)
    return count, definitions

def main():
    # Load test document (using the longer one for better comparison)
    doc_path = Path("tests/fixtures/credit-agreement-2.txt")
    document = doc_path.read_text()
    print(f"Document loaded: {len(document)} characters")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"test_results/comparison_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("1. BASIC EXTRACTION (no definition emphasis)")
    print("="*60)
    
    print("Running basic extraction...")
    basic_result = extract_document(document, BASIC_PROMPT)
    basic_file = output_dir / "basic_extraction.json"
    with open(basic_file, "w") as f:
        json.dump(basic_result, f, indent=2)
    
    basic_count, basic_defs = count_definitions(basic_result)
    print(f"✓ Basic extraction complete")
    print(f"  Definitions captured: {basic_count}")
    
    print("\n" + "="*60)
    print("2. ENHANCED EXTRACTION (with definition capture)")
    print("="*60)
    
    print("Running enhanced extraction...")
    enhanced_prompt = load_enhanced_prompt()
    enhanced_result = extract_document(document, enhanced_prompt)
    enhanced_file = output_dir / "enhanced_extraction.json"
    with open(enhanced_file, "w") as f:
        json.dump(enhanced_result, f, indent=2)
    
    enhanced_count, enhanced_defs = count_definitions(enhanced_result)
    print(f"✓ Enhanced extraction complete")
    print(f"  Definitions captured: {enhanced_count}")
    
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    print(f"Basic extraction:    {basic_count} definitions")
    print(f"Enhanced extraction: {enhanced_count} definitions")
    print(f"Improvement:         {enhanced_count - basic_count} additional definitions")
    print(f"Increase:            {((enhanced_count / max(basic_count, 1)) - 1) * 100:.0f}%")
    
    if enhanced_defs:
        print("\n" + "="*60)
        print("SAMPLE DEFINITIONS FROM ENHANCED EXTRACTION")
        print("="*60)
        for d in enhanced_defs[:5]:
            print(f"\n{d['field']}:")
            print(f"  {d['value']}")
    
    # Save comparison summary
    summary = {
        "timestamp": timestamp,
        "document": doc_path.name,
        "document_size": len(document),
        "basic_extraction": {
            "definitions_count": basic_count,
            "file": str(basic_file)
        },
        "enhanced_extraction": {
            "definitions_count": enhanced_count,
            "file": str(enhanced_file)
        },
        "improvement": {
            "additional_definitions": enhanced_count - basic_count,
            "percentage_increase": f"{((enhanced_count / max(basic_count, 1)) - 1) * 100:.0f}%"
        },
        "sample_definitions": enhanced_defs[:10]
    }
    
    summary_file = output_dir / "comparison_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_dir}")

if __name__ == "__main__":
    main()
