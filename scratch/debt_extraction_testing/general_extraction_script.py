#!/usr/bin/env python3
"""General extraction script for debt documents using the latest prompt"""

import os
import json
import openai
from pathlib import Path
from datetime import datetime
import sys

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

def extract_document(document_path, output_dir=None, model="gpt-4.1-nano", filing_url=None):
    """Extract economic terms from a debt document"""
    
    # Read document
    doc_path = Path(document_path)
    if not doc_path.exists():
        print(f"Error: Document not found: {doc_path}")
        return None
        
    doc_text = doc_path.read_text()
    doc_name = doc_path.stem
    
    # Set output directory
    if output_dir is None:
        output_dir = Path(f"extractions/{doc_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print(f"Document: {doc_name}")
    print(f"Size: {len(doc_text):,} characters")
    print(f"Model: {model}")
    print(f"Output: {output_dir}")
    print("=" * 80)
    
    # Create messages
    messages = [
        {
            "role": "system", 
            "content": "You are a financial document analyzer specializing in debt instruments. Extract information exactly as requested and return only JSON."
        },
        {
            "role": "user",
            "content": f"{extraction_prompt}\n\n---\n\nNow extract all economic terms from this loan agreement:\n\n{doc_text}"
        }
    ]
    
    # Make API call
    print("\nExtracting terms...")
    start_time = datetime.now()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✓ Extraction complete in {elapsed:.1f} seconds")
        
        # Parse response
        content = response.choices[0].message.content
        extracted_data = json.loads(content)
        
        # Save raw response
        with open(output_dir / "raw_response.txt", 'w') as f:
            f.write(content)
        
        # Save formatted JSON with minimal metadata
        output_file = output_dir / "extracted_terms.json"
        result = {
            "document_name": doc_name,
            "extraction_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "model": model
        }
        
        if filing_url:
            result["filing_url"] = filing_url
            
        result["extracted_data"] = extracted_data
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✓ Results saved to {output_file}")
        
        # Create summary
        print_summary(extracted_data)
        
        return extracted_data, output_dir
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Save error details
        with open(output_dir / "error.txt", 'w') as f:
            f.write(f"Error: {e}\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n")
            f.write(f"Model: {model}\n")
            f.write(f"Document: {doc_name}\n")
        
        return None, output_dir

def print_summary(data):
    """Print a summary of extracted data"""
    print("\n" + "-" * 40)
    print("EXTRACTION SUMMARY")
    print("-" * 40)
    
    print(f"Document Type: {data.get('document_type', 'Not identified')}")
    print(f"Effective Date: {data.get('effective_date', 'Not found')}")
    
    if 'obligations' in data:
        parties = data['obligations'].get('parties', [])
        commitments = data['obligations'].get('commitments', [])
        
        print(f"\nParties: {len(parties)}")
        for party in parties[:3]:
            print(f"  - {party.get('name')} ({party.get('role')})")
        if len(parties) > 3:
            print(f"  ... and {len(parties)-3} more")
        
        print(f"\nFacilities: {len(commitments)}")
        total = 0
        for comm in commitments:
            amount = comm.get('amount', 0) or 0
            total += amount
            print(f"  - {comm.get('facility_type')}: ${amount:,.0f}")
        if total > 0:
            print(f"  Total: ${total:,.0f}")
    
    if 'pricing' in data and data['pricing'].get('base_interest_rate'):
        rate = data['pricing']['base_interest_rate']
        print(f"\nBase Rate: {rate.get('benchmark')} + {rate.get('spread_bps')} bps")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python general_extraction_script.py <document_path> [output_dir] [model] [filing_url]")
        print("\nExample:")
        print("  python general_extraction_script.py rf_monolithics_loan.txt")
        print("  python general_extraction_script.py loan.pdf output/ gpt-4.1-nano https://www.sec.gov/...")
        sys.exit(1)
    
    document_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    model = sys.argv[3] if len(sys.argv) > 3 else "gpt-4.1-nano"
    filing_url = sys.argv[4] if len(sys.argv) > 4 else None
    
    extract_document(document_path, output_dir, model, filing_url)