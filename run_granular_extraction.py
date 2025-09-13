#!/usr/bin/env python3
"""Run enhanced granular extraction on credit agreements and generate raw JSON PDF."""

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
    """Load the enhanced granular extraction prompt."""
    prompt_path = Path("ENHANCED_granular_debt_extraction_prompt.md")
    return prompt_path.read_text()

def load_document(path):
    """Load a credit agreement document."""
    return Path(path).read_text()

def extract_with_granular_definitions(document_text, prompt_text):
    """Run extraction using the enhanced granular prompt."""
    
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": f"Extract all economic terms from this credit agreement:\n\n{document_text}"}
    ]
    
    print("Calling OpenAI API with granular prompt...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def count_all_definitions(obj, count=0):
    """Recursively count all definition-related fields."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if 'definition' in key.lower() and value:
                count += 1
            count = count_all_definitions(value, count)
    elif isinstance(obj, list):
        for item in obj:
            count = count_all_definitions(item, count)
    return count

def create_json_latex(extractions):
    """Create LaTeX document with raw JSON."""
    
    latex = []
    
    # Document preamble
    latex.append("\\documentclass[10pt]{article}")
    latex.append("\\usepackage[margin=0.5in]{geometry}")
    latex.append("\\usepackage{listings}")
    latex.append("\\usepackage{xcolor}")
    latex.append("\\usepackage{courier}")
    latex.append("")
    
    # JSON syntax highlighting
    latex.append("\\definecolor{delim}{RGB}{20,105,176}")
    latex.append("\\definecolor{numb}{RGB}{106,109,32}")
    latex.append("\\definecolor{string}{RGB}{163,21,21}")
    latex.append("")
    latex.append("\\lstdefinelanguage{json}{")
    latex.append("    basicstyle=\\tiny\\ttfamily,")  # Even smaller font
    latex.append("    numbers=left,")
    latex.append("    numberstyle=\\tiny,")
    latex.append("    stepnumber=5,")
    latex.append("    numbersep=5pt,")
    latex.append("    showstringspaces=false,")
    latex.append("    breaklines=true,")
    latex.append("    frame=lines,")
    latex.append("    string=[s]{\"}{\"},")
    latex.append("    stringstyle=\\color{string},")
    latex.append("    comment=[l]{:},")
    latex.append("    commentstyle=\\color{black},")
    latex.append("    morecomment=[l]{,},")
    latex.append("    literate=")
    latex.append("        *{0}{{{\\color{numb}0}}}{1}")
    latex.append("        {1}{{{\\color{numb}1}}}{1}")
    latex.append("        {2}{{{\\color{numb}2}}}{1}")
    latex.append("        {3}{{{\\color{numb}3}}}{1}")
    latex.append("        {4}{{{\\color{numb}4}}}{1}")
    latex.append("        {5}{{{\\color{numb}5}}}{1}")
    latex.append("        {6}{{{\\color{numb}6}}}{1}")
    latex.append("        {7}{{{\\color{numb}7}}}{1}")
    latex.append("        {8}{{{\\color{numb}8}}}{1}")
    latex.append("        {9}{{{\\color{numb}9}}}{1}")
    latex.append("}")
    latex.append("")
    
    latex.append("\\title{Credit Agreement Extractions\\\\[0.5em]")
    latex.append("{\\large With Enhanced Granular Definitions}}")
    latex.append("\\date{\\today}")
    latex.append("")
    latex.append("\\begin{document}")
    latex.append("\\maketitle")
    latex.append("")
    
    # Summary section
    latex.append("\\section*{Extraction Summary}")
    for doc_name, extraction in extractions.items():
        def_count = count_all_definitions(extraction)
        latex.append(f"\\textbf{{{doc_name}:}} {def_count} definition fields captured\\\\")
    latex.append("")
    latex.append("\\clearpage")
    
    # Add each JSON extraction
    for doc_name, extraction in extractions.items():
        latex.append(f"\\section{{{doc_name}}}")
        latex.append("")
        latex.append("\\begin{lstlisting}[language=json]")
        latex.append(json.dumps(extraction, indent=2))
        latex.append("\\end{lstlisting}")
        latex.append("")
        latex.append("\\clearpage")
        latex.append("")
    
    latex.append("\\end{document}")
    
    return '\n'.join(latex)

def main():
    print("Loading enhanced granular extraction prompt...")
    prompt = load_prompt()
    
    # The test documents
    test_docs = [
        ("RF Monolithics Term Loan", "scratch/debt_extraction_testing/debt_agreements/rf_monolithics_loan.txt"),
        ("Syndicated Credit Agreement", "scratch/debt_extraction_testing/debt_agreements/syndicated_credit_agreement.txt")
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
        print("Running extraction with granular definition capture...")
        try:
            extraction = extract_with_granular_definitions(document, prompt)
            extractions[doc_name] = extraction
            
            # Save JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_dir = Path(f"granular_extractions_{timestamp}")
            json_dir.mkdir(exist_ok=True)
            
            json_file = json_dir / f"{doc_name.replace(' ', '_').lower()}.json"
            with open(json_file, "w") as f:
                json.dump(extraction, f, indent=2)
            print(f"JSON saved to: {json_file}")
            
            # Count definitions
            def_count = count_all_definitions(extraction)
            print(f"Total definition fields captured: {def_count}")
            
            # Show if we got granular components
            if 'key_definitions' in extraction:
                print(f"Key definitions section: {len(extraction['key_definitions'])} terms")
            
        except Exception as e:
            print(f"Error processing {doc_name}: {e}")
            continue
    
    if extractions:
        # Create LaTeX document
        print("\n" + "="*60)
        print("Creating LaTeX document with raw JSON...")
        print("="*60)
        
        latex_content = create_json_latex(extractions)
        
        # Save LaTeX file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        latex_file = Path(f"granular_json_extractions_{timestamp}.tex")
        with open(latex_file, "w") as f:
            f.write(latex_content)
        
        print(f"\n✓ LaTeX document created: {latex_file}")
        print(f"\nTo compile to PDF:")
        print(f"  pdflatex {latex_file}")

if __name__ == "__main__":
    main()
