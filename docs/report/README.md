# CreditTech Institutional Project Report (LaTeX Suite)

This directory contains the complete, publication-grade LaTeX project report for the **CreditTech MVP** structured according to the rigorous 30-section framework.

## Compilation Options

### Option A: Overleaf (Recommended - 1 Click)
1. Download or locate `CreditTech_LaTeX_Report.zip`.
2. Go to [Overleaf](https://www.overleaf.com/).
3. Click **New Project** $\rightarrow$ **Upload Project**, and select `CreditTech_LaTeX_Report.zip`.
4. Click **Recompile** (ensure LaTeX engine is set to `pdfLaTeX`).

### Option B: Local TeX Live / MiKTeX
You can compile either the modular project or the standalone single file:

```bash
# Modular compilation
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Or standalone compilation
pdflatex CreditTech_Final_Project_Report.tex
bibtex CreditTech_Final_Project_Report
pdflatex CreditTech_Final_Project_Report.tex
```

## Directory Structure
- `main.tex`: Master modular LaTeX document.
- `CreditTech_Final_Project_Report.tex`: Inlined standalone single-file document.
- `references.bib`: BibTeX bibliography.
- `chapters/`: 30 individual chapters corresponding to the project sections.
- `figures/`: 13 publication-grade white-theme decision figures (300 DPI).
- `CreditTech_LaTeX_Report.zip`: Complete bundle for distribution or Overleaf.
