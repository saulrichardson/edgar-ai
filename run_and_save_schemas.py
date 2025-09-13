#!/usr/bin/env python3
"""Run the extraction pipeline and save all schema variants for analysis."""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Set environment variables
os.environ["EDGAR_AI_VERBOSE"] = "1"

# Import after setting env vars
from edgar_ai.interfaces import Document
from edgar_ai.services import schema_variants
from edgar_ai.pipeline.choose_schema import choose_schema
# Create output directory
OUTPUT_DIR = Path("schema_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

# Read the credit agreement text
credit_agreement_path = Path("tests/fixtures/credit_agreement.txt")
if not credit_agreement_path.exists():
    print(f"Error: {credit_agreement_path} not found")
    sys.exit(1)

doc_text = credit_agreement_path.read_text()

# Create document
doc = Document(
    doc_id="credit_agreement",
    text=doc_text
)

print("=" * 80)
print("EDGAR-AI Schema Extraction Pipeline")
print("=" * 80)
print(f"Document: {doc.doc_id}")
print(f"Document size: {len(doc.text)} characters")
print(f"Output directory: {OUTPUT_DIR.absolute()}")
print("=" * 80)

try:
    print("\n1. GENERATING SCHEMA VARIANTS...")
    print("-" * 40)
    
    # Generate the 3 variants
    variants = schema_variants.generate_variants(doc)
    print(f"✓ Generated {len(variants)} schema variants")
    
    # Save each variant
    variant_names = ["maximalist", "minimalist", "balanced"]
    for i, (variant, name) in enumerate(zip(variants, variant_names)):
        filename = OUTPUT_DIR / f"variant_{i}_{name}.json"
        with open(filename, 'w') as f:
            json.dump(variant, f, indent=2)
        print(f"  ✓ Saved {name} variant to {filename}")
        
        # Print summary
        fields = variant.get('fields', [])
        print(f"    - Overview: {variant.get('overview', '')[:100]}...")
        print(f"    - Topics: {len(variant.get('topics', []))} topics")
        print(f"    - Fields: {len(fields)} fields")
        
    print("\n2. RUNNING REFEREE TO SELECT BEST SCHEMA...")
    print("-" * 40)
    
    # Run referee
    winner_idx, reason = schema_variants.referee(variants, doc)
    print(f"✓ Winner: Variant {winner_idx} ({variant_names[winner_idx]})")
    print(f"  Reason: {reason}")
    
    # Save referee decision
    referee_decision = {
        "winner_index": winner_idx,
        "winner_name": variant_names[winner_idx],
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    with open(OUTPUT_DIR / "referee_decision.json", 'w') as f:
        json.dump(referee_decision, f, indent=2)
    
    print("\n3. RUNNING MERGE REFEREE (ALTERNATIVE APPROACH)...")
    print("-" * 40)
    
    # Also try merge_referee
    merged_schema = schema_variants.merge_referee(variants, doc)
    with open(OUTPUT_DIR / "merged_schema.json", 'w') as f:
        json.dump(merged_schema, f, indent=2)
    print(f"✓ Generated merged schema with {len(merged_schema.get('fields', []))} fields")
    
    print("\n4. SAVING SCHEMA COMPARISON...")
    print("-" * 40)
    
    # Create comparison summary
    comparison = {
        "document_id": doc.doc_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "variants": {
            name: {
                "field_count": len(variants[i].get('fields', [])),
                "fields": list(variants[i].get('fields', {}).keys()) if isinstance(variants[i].get('fields'), dict) else [f['name'] for f in variants[i].get('fields', [])]
            }
            for i, name in enumerate(variant_names)
        },
        "referee_winner": variant_names[winner_idx],
        "merged_field_count": len(merged_schema.get('fields', []))
    }
    
    with open(OUTPUT_DIR / "schema_comparison.json", 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print("✓ Saved schema comparison")
    
    # Create a markdown report
    report_lines = [
        "# Schema Extraction Analysis",
        f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"\nDocument: `{doc.doc_id}`",
        "\n## Schema Variants\n",
        "| Variant | Field Count | Description |",
        "|---------|-------------|-------------|"
    ]
    
    for i, name in enumerate(variant_names):
        variant = variants[i]
        field_count = len(variant.get('fields', []))
        overview = variant.get('overview', '')[:100] + "..."
        report_lines.append(f"| {name.capitalize()} | {field_count} | {overview} |")
    
    report_lines.extend([
        f"\n## Referee Decision",
        f"\n**Winner**: {variant_names[winner_idx].capitalize()} variant",
        f"\n**Reason**: {reason}",
        f"\n## Merged Schema",
        f"\nThe merge referee created a schema with {len(merged_schema.get('fields', []))} fields by combining the best aspects of all variants.",
        "\n## Field Comparison\n"
    ])
    
    # Add field listing for each variant
    for i, name in enumerate(variant_names):
        variant = variants[i]
        fields = variant.get('fields', {})
        if isinstance(fields, dict):
            field_names = list(fields.keys())
        else:
            field_names = [f['name'] for f in fields]
        
        report_lines.extend([
            f"\n### {name.capitalize()} Fields ({len(field_names)} total)\n",
            "```"
        ])
        for field in sorted(field_names)[:20]:  # Show first 20
            report_lines.append(field)
        if len(field_names) > 20:
            report_lines.append(f"... and {len(field_names) - 20} more")
        report_lines.append("```")
    
    with open(OUTPUT_DIR / "analysis_report.md", 'w') as f:
        f.write('\n'.join(report_lines))
    
    print("✓ Generated analysis report")
    
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETE!")
    print(f"\nAll outputs saved to: {OUTPUT_DIR.absolute()}")
    print("\nFiles created:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        print(f"  - {file.name}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Save error log
    with open(OUTPUT_DIR / "error_log.txt", 'w') as f:
        f.write(f"Error: {e}\n\n")
        traceback.print_exc(file=f)