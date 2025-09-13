#!/usr/bin/env python3
"""Run enhanced extraction on credit agreements and generate LaTeX output."""

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

def format_number(value):
    """Format large numbers with commas."""
    if isinstance(value, (int, float)) and value >= 1000:
        return f"{value:,.0f}"
    return str(value)

def escape_latex(text):
    """Escape special LaTeX characters."""
    if not isinstance(text, str):
        return str(text)
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extraction_to_latex(extraction, doc_name):
    """Convert extraction to LaTeX format with definitions highlighted."""
    
    latex = []
    latex.append(f"\\section{{{escape_latex(doc_name)}}}")
    latex.append("")
    
    # Document Overview
    latex.append("\\subsection{Document Overview}")
    latex.append("\\begin{itemize}")
    latex.append(f"\\item \\textbf{{Document Type:}} {extraction.get('document_type', 'N/A')}")
    latex.append(f"\\item \\textbf{{Effective Date:}} {extraction.get('effective_date', 'N/A')}")
    latex.append("\\end{itemize}")
    latex.append("")
    
    # Parties and Commitments
    if 'obligations' in extraction:
        latex.append("\\subsection{Parties and Commitments}")
        
        # Parties table
        if 'parties' in extraction['obligations']:
            latex.append("\\subsubsection{Parties}")
            latex.append("\\begin{tabular}{|l|l|l|}")
            latex.append("\\hline")
            latex.append("\\textbf{Role} & \\textbf{Name} & \\textbf{Jurisdiction} \\\\")
            latex.append("\\hline")
            for party in extraction['obligations']['parties']:
                latex.append(f"{escape_latex(party['role'])} & {escape_latex(party['name'])} & {escape_latex(party.get('jurisdiction', 'N/A'))} \\\\")
            latex.append("\\hline")
            latex.append("\\end{tabular}")
            latex.append("")
        
        # Commitments
        if 'commitments' in extraction['obligations']:
            latex.append("\\subsubsection{Credit Facilities}")
            latex.append("\\begin{itemize}")
            for commit in extraction['obligations']['commitments']:
                latex.append(f"\\item \\textbf{{{escape_latex(commit['facility_type'].upper())}:}} \\${format_number(commit['amount'])} {commit.get('currency', 'USD')}")
                latex.append(f"  \\begin{{itemize}}")
                latex.append(f"  \\item Purpose: {escape_latex(commit.get('purpose', 'N/A'))}")
                latex.append(f"  \\end{{itemize}}")
            latex.append("\\end{itemize}")
            latex.append("")
    
    # Pricing with Definitions
    if 'pricing' in extraction:
        latex.append("\\subsection{Pricing Terms}")
        
        if 'base_interest_rate' in extraction['pricing']:
            rate = extraction['pricing']['base_interest_rate']
            latex.append("\\subsubsection{Base Interest Rate}")
            latex.append("\\begin{itemize}")
            latex.append(f"\\item \\textbf{{Rate Type:}} {rate.get('rate_type', 'N/A')}")
            latex.append(f"\\item \\textbf{{Benchmark:}} {rate.get('benchmark', 'N/A')}")
            
            # Highlight definition if present
            if 'benchmark_definition' in rate and rate['benchmark_definition']:
                latex.append(f"\\item \\textbf{{\\colorbox{{yellow}}{{Benchmark Definition:}}}} \\textit{{{escape_latex(rate['benchmark_definition'])}}}")
            
            latex.append(f"\\item \\textbf{{Spread:}} {rate.get('spread_bps', 0)} basis points")
            latex.append("\\end{itemize}")
            latex.append("")
        
        if 'performance_pricing' in extraction['pricing']:
            latex.append("\\subsubsection{Performance-Based Pricing}")
            for perf in extraction['pricing']['performance_pricing']:
                latex.append(f"\\textbf{{Metric:}} {escape_latex(perf['metric'])}\\\\")
                
                # Highlight definition if present
                if 'definition' in perf and perf['definition']:
                    latex.append(f"\\textbf{{\\colorbox{{yellow}}{{Definition:}}}} \\textit{{{escape_latex(perf['definition'])}}}\\\\")
                
                latex.append(f"\\textbf{{Test Frequency:}} {perf.get('test_frequency', 'N/A')}\\\\")
                
                if 'pricing_grid' in perf:
                    latex.append("\\begin{center}")
                    latex.append("\\begin{tabular}{|l|r|}")
                    latex.append("\\hline")
                    latex.append("\\textbf{Condition} & \\textbf{Spread Adjustment (bps)} \\\\")
                    latex.append("\\hline")
                    for grid in perf['pricing_grid']:
                        latex.append(f"{escape_latex(grid['condition'])} & {grid.get('spread_adjustment_bps', 0)} \\\\")
                    latex.append("\\hline")
                    latex.append("\\end{tabular}")
                    latex.append("\\end{center}")
                latex.append("")
    
    # Financial Covenants with Definitions
    if 'conditions' in extraction and extraction['conditions'] and 'financial_covenants' in extraction['conditions']:
        latex.append("\\subsection{Financial Covenants}")
        latex.append("\\begin{itemize}")
        for cov in extraction['conditions']['financial_covenants']:
            latex.append(f"\\item \\textbf{{{escape_latex(cov['metric'])}:}} {cov['requirement']} {cov.get('threshold_value', 'N/A')}")
            
            # Highlight definition if present
            if 'definition' in cov and cov['definition']:
                latex.append(f"  \\begin{{itemize}}")
                latex.append(f"  \\item \\textbf{{\\colorbox{{yellow}}{{Definition:}}}} \\textit{{{escape_latex(cov['definition'])}}}")
                latex.append(f"  \\end{{itemize}}")
            
            latex.append(f"  \\begin{{itemize}}")
            latex.append(f"  \\item Test Frequency: {cov.get('test_frequency', 'N/A')}")
            latex.append(f"  \\end{{itemize}}")
        latex.append("\\end{itemize}")
        latex.append("")
    
    # Mandatory Prepayments with Definitions
    if 'repayment' in extraction and extraction['repayment'] and 'mandatory_prepayments' in extraction['repayment']:
        latex.append("\\subsection{Mandatory Prepayments}")
        for prep in extraction['repayment']['mandatory_prepayments']:
            latex.append(f"\\subsubsection{{{escape_latex(prep['trigger'])}}}")
            latex.append("\\begin{itemize}")
            
            # Highlight definition if present
            if 'definition' in prep and prep['definition']:
                latex.append(f"\\item \\textbf{{\\colorbox{{yellow}}{{Definition:}}}} \\textit{{{escape_latex(prep['definition'])}}}")
            
            latex.append(f"\\item \\textbf{{Percentage:}} {prep.get('percentage', 0) * 100:.0f}\\%")
            latex.append(f"\\item \\textbf{{Application:}} {escape_latex(prep.get('application', 'N/A'))}")
            latex.append("\\end{itemize}")
        latex.append("")
    
    # Fees with Definitions
    if 'fees_and_costs' in extraction and extraction['fees_and_costs'] and 'fees' in extraction['fees_and_costs']:
        latex.append("\\subsection{Fees}")
        latex.append("\\begin{itemize}")
        for fee in extraction['fees_and_costs']['fees']:
            latex.append(f"\\item \\textbf{{{escape_latex(fee['fee_type'].title())} Fee:}} {fee.get('amount_or_rate', 'N/A')} {escape_latex(fee.get('rate_basis', ''))}")
            
            # Check for any definition fields
            for key in fee:
                if 'definition' in key.lower() and fee[key]:
                    latex.append(f"  \\begin{{itemize}}")
                    latex.append(f"  \\item \\textbf{{\\colorbox{{yellow}}{{{escape_latex(key.replace('_', ' ').title())}:}}}} \\textit{{{escape_latex(fee[key])}}}")
                    latex.append(f"  \\end{{itemize}}")
        latex.append("\\end{itemize}")
        latex.append("")
    
    # Administrative Terms with Definitions
    if 'administrative' in extraction and extraction['administrative'] and 'governing_terms' in extraction['administrative']:
        terms = extraction['administrative']['governing_terms']
        latex.append("\\subsection{Administrative Terms}")
        latex.append("\\begin{itemize}")
        latex.append(f"\\item \\textbf{{Governing Law:}} {terms.get('governing_law', 'N/A')}")
        latex.append(f"\\item \\textbf{{Amendment Threshold:}} {terms.get('amendment_threshold', 'N/A')}")
        
        if 'required_lenders_definition' in terms and terms['required_lenders_definition']:
            latex.append(f"  \\begin{{itemize}}")
            latex.append(f"  \\item \\textbf{{\\colorbox{{yellow}}{{Definition:}}}} \\textit{{{escape_latex(terms['required_lenders_definition'])}}}")
            latex.append(f"  \\end{{itemize}}")
        
        latex.append("\\end{itemize}")
        latex.append("")
    
    return '\n'.join(latex)

def create_full_latex_document(extractions):
    """Create a complete LaTeX document with all extractions."""
    
    latex = []
    
    # Document preamble
    latex.append("\\documentclass[11pt]{article}")
    latex.append("\\usepackage[margin=1in]{geometry}")
    latex.append("\\usepackage{booktabs}")
    latex.append("\\usepackage{longtable}")
    latex.append("\\usepackage{array}")
    latex.append("\\usepackage{xcolor}")
    latex.append("\\usepackage{colortbl}")
    latex.append("\\usepackage{hyperref}")
    latex.append("")
    latex.append("\\title{Credit Agreement Extractions with Definitions}")
    latex.append(f"\\date{{\\today}}")
    latex.append("")
    latex.append("\\begin{document}")
    latex.append("\\maketitle")
    latex.append("")
    latex.append("\\tableofcontents")
    latex.append("\\newpage")
    latex.append("")
    latex.append("\\section*{Overview}")
    latex.append("This document presents structured extractions from credit agreements using an enhanced prompt that captures definitions alongside economic terms. Definitions are \\colorbox{yellow}{highlighted in yellow} throughout the document.")
    latex.append("")
    latex.append("\\newpage")
    latex.append("")
    
    # Add each extraction
    for doc_name, extraction in extractions.items():
        latex.append(extraction_to_latex(extraction, doc_name))
        latex.append("\\newpage")
        latex.append("")
    
    # Close document
    latex.append("\\end{document}")
    
    return '\n'.join(latex)

def main():
    print("Loading enhanced extraction prompt...")
    prompt = load_prompt()
    
    # Test documents
    test_docs = [
        ("Simple Credit Agreement", "tests/fixtures/credit_agreement.txt"),
        ("Syndicated Credit Agreement - Weekly Reader Corp", "tests/fixtures/credit-agreement-2.txt")
    ]
    
    extractions = {}
    
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
            extractions[doc_name] = extraction
            
            # Save JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_dir = Path(f"latex_output_{timestamp}")
            json_dir.mkdir(exist_ok=True)
            
            json_file = json_dir / f"{doc_name.replace(' ', '_').lower()}.json"
            with open(json_file, "w") as f:
                json.dump(extraction, f, indent=2)
            print(f"JSON saved to: {json_file}")
            
        except Exception as e:
            print(f"Error processing {doc_name}: {e}")
            continue
    
    if extractions:
        # Create LaTeX document
        print("\n" + "="*60)
        print("Creating LaTeX document...")
        print("="*60)
        
        latex_content = create_full_latex_document(extractions)
        
        # Save LaTeX file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        latex_file = Path(f"credit_agreements_extraction_{timestamp}.tex")
        with open(latex_file, "w") as f:
            f.write(latex_content)
        
        print(f"\n✓ LaTeX document created: {latex_file}")
        print(f"\nTo compile to PDF:")
        print(f"  pdflatex {latex_file}")
        print(f"  pdflatex {latex_file}  # Run twice for TOC")

if __name__ == "__main__":
    main()
