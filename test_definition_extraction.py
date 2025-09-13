#!/usr/bin/env python3
"""Test the enhanced extraction prompt with definition capture."""

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
    raise ValueError("No OpenAI API key found. Set EDGAR_AI_OPENAI_API_KEY or OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def load_prompt():
    """Load the enhanced extraction prompt."""
    prompt_path = Path("FINAL_enhanced_debt_extraction_prompt.md")
    return prompt_path.read_text()

def load_document(path):
    """Load a credit agreement document."""
    return Path(path).read_text()

def extract_with_definitions(document_text, prompt_text):
    """Run extraction using the enhanced prompt."""
    
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": f"Extract all economic terms from this credit agreement:\n\n{document_text}"}
    ]
    
    print("Calling OpenAI API...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def save_results(results, doc_name):
    """Save extraction results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"test_results/definitions_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{doc_name}_extraction.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    return output_file

def analyze_definitions(extraction):
    """Check which fields have definitions captured."""
    definitions_found = []
    
    def find_definitions(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if key in ["definition", "benchmark_definition", "unused_commitment_definition", 
                          "utilization_definition", "available_amount_definition", 
                          "threshold_definition", "required_lenders_definition"]:
                    if value and value != "":
                        definitions_found.append({
                            "path": new_path,
                            "definition": value
                        })
                find_definitions(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_definitions(item, f"{path}[{i}]")
    
    find_definitions(extraction)
    return definitions_found

def main():
    print("Loading enhanced extraction prompt...")
    prompt = load_prompt()
    
    # Test documents
    test_docs = [
        ("credit_agreement", "tests/fixtures/credit_agreement.txt"),
        ("credit_agreement_2", "tests/fixtures/credit-agreement-2.txt")
    ]
    
    for doc_name, doc_path in test_docs:
        print(f"\n{'='*60}")
        print(f"Processing: {doc_name}")
        print('='*60)
        
        # Load document
        print(f"Loading document from {doc_path}...")
        document = load_document(doc_path)
        print(f"Document size: {len(document)} characters")
        
        # Run extraction
        print("Running extraction with definition capture...")
        try:
            extraction = extract_with_definitions(document, prompt)
            
            # Save results
            output_file = save_results(extraction, doc_name)
            
            # Analyze definitions
            definitions = analyze_definitions(extraction)
            print(f"\nDefinitions captured: {len(definitions)}")
            
            if definitions:
                print("\nSample definitions found:")
                for d in definitions[:5]:  # Show first 5
                    print(f"  - {d['path']}")
                    print(f"    Definition: {d['definition'][:100]}...")
            
        except Exception as e:
            print(f"Error processing {doc_name}: {e}")
            continue

if __name__ == "__main__":
    main()
