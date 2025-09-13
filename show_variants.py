import os
import json
os.environ["EDGAR_AI_VERBOSE"] = "1"

from edgar_ai.interfaces import Document
from edgar_ai.services import schema_variants

# Create a test document
doc = Document(
    doc_id="test-credit",
    text="""CREDIT AGREEMENT dated as of November 17, 1999, 
among WEEKLY READER CORPORATION, a Delaware corporation ("Borrower"),
and BANK OF AMERICA, N.A., as Administrative Agent ("Agent").

Term A Loan Commitment: $31,000,000
Term B Loan Commitment: $100,000,000
Interest Rate: LIBOR + 3.25%
Maturity Date: November 17, 2005
Governing Law: New York"""
)

print("Generating 3 schema variants...")
print("=" * 80)

try:
    variants = schema_variants.generate_variants(doc)
    
    variant_names = ["MAXIMALIST", "MINIMALIST", "BALANCED"]
    
    for i, (variant, name) in enumerate(zip(variants, variant_names)):
        print(f"\n{name} VARIANT (Variant {i}):")
        print("-" * 40)
        print("Overview:", variant.get('overview', '')[:200] + "...")
        print("\nTopics:", variant.get('topics', []))
        print(f"\nNumber of fields: {len(variant.get('fields', []))}")
        print("\nFields:")
        for field in variant.get('fields', [])[:10]:  # Show first 10 fields
            print(f"  - {field['name']}: {field['description'][:60]}...")
        if len(variant.get('fields', [])) > 10:
            print(f"  ... and {len(variant.get('fields', [])) - 10} more fields")
            
    print("\n" + "=" * 80)
    print("Running referee to pick the best variant...")
    winner_idx, reason = schema_variants.referee(variants, doc)
    print(f"\nWINNER: Variant {winner_idx} ({variant_names[winner_idx]})")
    print(f"Reason: {reason}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()