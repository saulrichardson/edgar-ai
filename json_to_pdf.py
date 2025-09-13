#!/usr/bin/env python3
"""Convert raw JSON extractions to PDF."""

import json
from pathlib import Path
from datetime import datetime

def create_json_latex(extractions):
    """Create LaTeX document with raw JSON."""
    
    latex = []
    
    # Document preamble
    latex.append("\\documentclass[10pt]{article}")
    latex.append("\\usepackage[margin=0.75in]{geometry}")
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
    latex.append("    basicstyle=\\footnotesize\\ttfamily,")
    latex.append("    numbers=left,")
    latex.append("    numberstyle=\\scriptsize,")
    latex.append("    stepnumber=1,")
    latex.append("    numbersep=8pt,")
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
    
    latex.append("\\title{Credit Agreement Extractions - Raw JSON}")
    latex.append("\\date{\\today}")
    latex.append("")
    latex.append("\\begin{document}")
    latex.append("\\maketitle")
    latex.append("")
    
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
    # Load the existing extractions
    extractions = {}
    
    # RF Monolithics
    rf_file = Path("correct_agreements_20250806_143934/rf_monolithics_term_loan.json")
    if rf_file.exists():
        with open(rf_file, "r") as f:
            extractions["RF Monolithics Term Loan"] = json.load(f)
        print(f"Loaded: RF Monolithics Term Loan")
    
    # Syndicated Agreement
    synd_file = Path("correct_agreements_20250806_144033/syndicated_credit_agreement.json")
    if synd_file.exists():
        with open(synd_file, "r") as f:
            extractions["Syndicated Credit Agreement"] = json.load(f)
        print(f"Loaded: Syndicated Credit Agreement")
    
    if extractions:
        # Create LaTeX document
        print("\nCreating LaTeX document with raw JSON...")
        
        latex_content = create_json_latex(extractions)
        
        # Save LaTeX file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        latex_file = Path(f"raw_json_extractions_{timestamp}.tex")
        with open(latex_file, "w") as f:
            f.write(latex_content)
        
        print(f"✓ LaTeX document created: {latex_file}")
        print(f"\nTo compile to PDF:")
        print(f"  pdflatex {latex_file}")

if __name__ == "__main__":
    main()