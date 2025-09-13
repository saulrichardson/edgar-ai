import os
import sys

# Set environment variables
os.environ["EDGAR_AI_VERBOSE"] = "1"
os.environ["EDGAR_AI_LLM_GATEWAY_URL"] = "http://localhost:8000"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")

# Import after setting env vars
from edgar_ai.interfaces import Document
from edgar_ai.services import schema_variants

# Create a test document
doc = Document(
    doc_id="test-credit-agreement",
    text="""CREDIT AGREEMENT

This Credit Agreement (this "Agreement") is entered into as of November 17, 1999,
among WEEKLY READER CORPORATION, a Delaware corporation, and JLC LEARNING
CORPORATION, a Delaware corporation (each a "Borrower" and collectively, the
"Borrowers"), and BANK OF AMERICA, N.A. as Administrative Agent.

The parties agree that the Term A Loan Commitment shall be $31,000,000 and
the Term B Loan Commitment shall be $100,000,000."""
)

try:
    print("Testing schema variants generation...")
    variants = schema_variants.generate_variants(doc)
    print(f"Generated {len(variants)} variants")
    
    for i, variant in enumerate(variants):
        print(f"\nVariant {i}:")
        print(f"  Overview: {variant.get('overview', 'N/A')[:100]}...")
        print(f"  Topics: {variant.get('topics', [])}")
        print(f"  Fields: {len(variant.get('fields', []))} fields")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()