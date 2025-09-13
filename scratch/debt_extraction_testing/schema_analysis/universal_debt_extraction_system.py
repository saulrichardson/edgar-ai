"""
Universal Debt Economics Extraction System
Version 3.0 - Production Ready

This module provides the complete extraction system combining:
1. Natural language instructions for clarity
2. Structured output format for consistency
3. Comprehensive examples for edge cases
"""

EXTRACTION_SYSTEM = {
    "system_role": "You are a financial document analyzer specializing in debt instruments.",
    
    "extraction_prompt": """
You are a financial document analyzer specializing in debt instruments. Your task is to extract ALL economic terms from debt documents, converting them into a structured format suitable for quantitative analysis.

## Core Principles

1. **Extract Observable Facts Only** - If it's not explicitly stated in the document, don't infer it
2. **Standardize Numbers** - Convert all text descriptions to analyzable numbers  
3. **Preserve Context** - When numeric extraction is uncertain, include the source text
4. **Be Exhaustive** - Better to over-extract than miss critical terms
5. **Adapt to Complexity** - Simple notes have fewer terms; complex agreements have many

## Number Standardization Rules

### Amounts and Principal
- Convert to base units: "$12.5 million" → 12500000
- Remove formatting: "USD 1,000,000" → 1000000

### Interest Rates and Spreads
- ALWAYS use basis points: "LIBOR + 2.50%" → spread_bps: 250
- Fixed rates too: "8% fixed" → spread_bps: 800

### Ratios
- Use decimals: "3.5x" → 3.5, "350%" → 3.5

### Dates
- Format YYYY-MM-DD: "December 31, 2025" → "2025-12-31"

## What to Extract

For each document, identify and extract:

1. **PARTIES AND OBLIGATIONS**
   - Every entity with a role (borrower, lender, agent, guarantor)
   - All lending commitments (amounts, types, availability)

2. **PRICING TERMS**
   - Interest rates (benchmark + spread)
   - Performance pricing grids
   - Default rates and floors

3. **REPAYMENT TERMS**
   - Maturity dates
   - Amortization schedules
   - Prepayment rights and penalties

4. **CONDITIONS AND COVENANTS**
   - Financial covenants with thresholds
   - Negative covenants and restrictions
   - Events of default

5. **FEES AND COSTS**
   - All fees beyond interest
   - Payment timing and recipients

6. **SECURITY AND GUARANTEES**
   - Collateral and lien priority
   - Guarantee structures

7. **ADMINISTRATIVE TERMS**
   - Governing law
   - Amendment provisions

Return results in the JSON structure specified below.
""",
    
    "output_structure": {
        "document_type": "string - type of debt instrument",
        "effective_date": "YYYY-MM-DD format",
        
        "obligations": {
            "parties": [
                {
                    "role": "string - borrower|lender|agent|guarantor",
                    "name": "string - full legal name",
                    "entity_type": "string - corporation|LLC|individual",
                    "jurisdiction": "string - state/country if stated"
                }
            ],
            "commitments": [
                {
                    "facility_type": "string - term loan|revolver|etc",
                    "amount": "number - in base currency units",
                    "currency": "string - USD|EUR|etc",
                    "availability_period": "string - description",
                    "purpose": "string - use of proceeds if stated"
                }
            ]
        },
        
        "pricing": {
            "base_interest_rate": {
                "rate_type": "floating|fixed",
                "benchmark": "string - SOFR|LIBOR|Prime|fixed",
                "spread_bps": "number - basis points",
                "floor_bps": "number or null",
                "cap_bps": "number or null",
                "day_count": "string - if stated"
            },
            "performance_pricing": [
                {
                    "metric": "string - leverage_ratio|rating|etc",
                    "pricing_grid": [
                        {
                            "condition": "string - e.g. < 3.0x",
                            "spread_adjustment_bps": "number - positive or negative"
                        }
                    ],
                    "test_frequency": "string"
                }
            ],
            "default_pricing": {
                "trigger": "string",
                "rate_increase_bps": "number",
                "application": "string"
            }
        },
        
        "repayment": {
            "maturity": {
                "final_maturity_date": "YYYY-MM-DD",
                "extension_options": "string or null"
            },
            "scheduled_amortization": {
                "schedule_type": "string",
                "payments": [
                    {
                        "date": "YYYY-MM-DD",
                        "amount": "number",
                        "percentage": "number - if stated as %"
                    }
                ]
            },
            "mandatory_prepayments": [
                {
                    "trigger": "string",
                    "percentage": "decimal - 1.0 for 100%",
                    "application": "string"
                }
            ],
            "voluntary_prepayment": {
                "permitted": "boolean",
                "minimum_amount": "number or null",
                "premium": "string - description",
                "notice_days": "number or null"
            }
        },
        
        "conditions": {
            "financial_covenants": [
                {
                    "metric": "string",
                    "requirement": "maximum|minimum",
                    "threshold_value": "number",
                    "test_frequency": "string",
                    "cure_rights": "string or null"
                }
            ],
            "negative_covenants": [
                {
                    "restriction_type": "string",
                    "description": "string",
                    "exceptions": "string"
                }
            ],
            "events_of_default": [
                {
                    "event_type": "string",
                    "description": "string",
                    "grace_period": "string",
                    "materiality_threshold": "number or null"
                }
            ]
        },
        
        "fees_and_costs": {
            "fees": [
                {
                    "fee_type": "string",
                    "amount_or_rate": "number",
                    "rate_basis": "string",
                    "payment_timing": "string",
                    "recipient": "string"
                }
            ]
        },
        
        "security_and_guarantees": {
            "security": {
                "secured": "boolean",
                "collateral_description": "string",
                "lien_priority": "string",
                "perfection_requirements": "string"
            },
            "guarantees": [
                {
                    "guarantor": "string",
                    "guarantee_type": "string",
                    "guarantee_cap": "number or null"
                }
            ]
        },
        
        "administrative": {
            "governing_terms": {
                "governing_law": "string",
                "jurisdiction": "string",
                "waiver_of_jury_trial": "boolean",
                "amendment_threshold": "string"
            }
        }
    },
    
    "examples": {
        "simple_note": {
            "document_type": "promissory note",
            "effective_date": "2024-01-01",
            "obligations": {
                "parties": [
                    {"role": "borrower", "name": "John Smith", "entity_type": "individual"},
                    {"role": "lender", "name": "Jane Doe", "entity_type": "individual"}
                ],
                "commitments": [
                    {"facility_type": "term loan", "amount": 50000, "currency": "USD"}
                ]
            },
            "pricing": {
                "base_interest_rate": {
                    "rate_type": "fixed",
                    "benchmark": "fixed", 
                    "spread_bps": 800
                }
            },
            "repayment": {
                "maturity": {"final_maturity_date": "2026-01-01"}
            }
            # Other sections would be empty/null
        },
        
        "complex_facility": {
            # Would show multiple tranches, pricing grids, covenants, etc.
        }
    },
    
    "edge_case_handling": {
        "uncertain_values": {
            "format": {
                "value": "number or null",
                "source_text": "original document text", 
                "interpretation_notes": "any assumptions"
            }
        },
        "formulas": {
            "format": {
                "formula": "the calculation description",
                "current_value": "number if calculable",
                "source_text": "section reference"
            }
        }
    }
}

def create_extraction_prompt(include_examples=True):
    """
    Generate the complete extraction prompt for an LLM.
    
    Args:
        include_examples: Whether to include example outputs
        
    Returns:
        str: Complete prompt ready for LLM consumption
    """
    prompt_parts = [
        EXTRACTION_SYSTEM["extraction_prompt"],
        "\n## Output Structure\n",
        "Return your extraction as a JSON object with this exact structure:",
        "```json",
        str(EXTRACTION_SYSTEM["output_structure"]),
        "```"
    ]
    
    if include_examples:
        prompt_parts.extend([
            "\n## Example Outputs\n",
            "Simple Note:",
            "```json",
            str(EXTRACTION_SYSTEM["examples"]["simple_note"]),
            "```"
        ])
    
    prompt_parts.extend([
        "\n## Edge Case Handling\n",
        "When values are uncertain:",
        str(EXTRACTION_SYSTEM["edge_case_handling"]["uncertain_values"]),
        "\nFor complex formulas:",
        str(EXTRACTION_SYSTEM["edge_case_handling"]["formulas"])
    ])
    
    return "\n".join(prompt_parts)

def validate_extraction(extracted_data):
    """
    Validate that extracted data matches expected structure.
    
    Args:
        extracted_data: Dictionary of extracted terms
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    required_fields = ["document_type", "effective_date", "obligations", "pricing"]
    errors = []
    
    for field in required_fields:
        if field not in extracted_data:
            errors.append(f"Missing required field: {field}")
    
    # Add more validation as needed
    
    return len(errors) == 0, errors

# Usage example:
if __name__ == "__main__":
    # Generate the prompt
    prompt = create_extraction_prompt(include_examples=True)
    
    # This would be sent to the LLM along with the document text
    print("Generated extraction prompt:")
    print(prompt[:500] + "...")  # Show first 500 chars
    
    print(f"\nTotal prompt length: {len(prompt)} characters")