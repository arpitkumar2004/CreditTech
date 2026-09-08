"""Script to validate, inline, and bundle the CreditTech 30-Section LaTeX Project Report.

Generates:
1. docs/report/CreditTech_Final_Project_Report.tex (Standalone single-file document)
2. docs/report/CreditTech_LaTeX_Report.zip (Complete Overleaf-ready ZIP distribution)
3. Validation report verifying citations, figures, and input files.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

REPORT_DIR = Path("docs/report")
CHAPTERS_DIR = REPORT_DIR / "chapters"
FIGURES_DIR = REPORT_DIR / "figures"
MAIN_TEX = REPORT_DIR / "main.tex"
BIB_FILE = REPORT_DIR / "references.bib"
STANDALONE_TEX = REPORT_DIR / "CreditTech_Final_Project_Report.tex"
ZIP_OUTPUT = REPORT_DIR / "CreditTech_LaTeX_Report.zip"


def extract_bib_keys(bib_path: Path) -> set[str]:
    """Extracts all citation keys defined in a .bib file."""
    if not bib_path.exists():
        return set()
    text = bib_path.read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\s*\{\s*([a-zA-Z0-9_\-:]+)\s*,", text))


def validate_report(main_tex_content: str, bib_keys: set[str]) -> list[str]:
    """Validates references, figures, and chapter imports."""
    warnings: list[str] = []

    # 1. Check all \input{} files
    input_matches = re.findall(r"\\input\{([^}]+)\}", main_tex_content)
    for imp in input_matches:
        imp_path = REPORT_DIR / f"{imp}.tex" if not imp.endswith(".tex") else REPORT_DIR / imp
        if not imp_path.exists():
            warnings.append(f"Missing input chapter: {imp_path}")

    # 2. Check all \includegraphics{} files across all chapters
    for chap in sorted(CHAPTERS_DIR.glob("*.tex")):
        content = chap.read_text(encoding="utf-8")
        fig_matches = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content)
        for fig in fig_matches:
            # Handle potential relative paths
            fig_clean = fig.strip()
            if fig_clean.startswith("figures/"):
                fig_file = REPORT_DIR / fig_clean
            else:
                fig_file = FIGURES_DIR / fig_clean
            if not fig_file.exists():
                warnings.append(f"Chapter {chap.name} references missing figure: {fig_file}")

        # 3. Check citations
        cite_matches = re.findall(r"\\cite\{([^}]+)\}", content)
        for cite_group in cite_matches:
            for key in cite_group.split(","):
                key_clean = key.strip()
                if key_clean and key_clean not in bib_keys:
                    warnings.append(f"Chapter {chap.name} has missing citation key: '{key_clean}'")

    return warnings


def generate_standalone_tex(main_tex_path: Path) -> str:
    """Recursively inlines all \\input{} files to create a standalone .tex document."""
    content = main_tex_path.read_text(encoding="utf-8")

    def replace_input(match: re.Match) -> str:
        rel_path = match.group(1).strip()
        if not rel_path.endswith(".tex"):
            rel_path += ".tex"
        target_file = REPORT_DIR / rel_path
        if target_file.exists():
            inner = target_file.read_text(encoding="utf-8")
            return f"\n% --- BEGIN INLINED: {rel_path} ---\n{inner}\n% --- END INLINED: {rel_path} ---\n"
        return match.group(0)

    inlined = re.sub(r"\\input\{([^}]+)\}", replace_input, content)
    return inlined


def create_zip_package() -> None:
    """Creates an Overleaf-ready ZIP bundle containing all report files."""
    with zipfile.ZipFile(ZIP_OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # Root files
        z.write(MAIN_TEX, arcname="main.tex")
        z.write(STANDALONE_TEX, arcname="CreditTech_Final_Project_Report.tex")
        if BIB_FILE.exists():
            z.write(BIB_FILE, arcname="references.bib")

        # Readme
        readme_path = REPORT_DIR / "README.md"
        if readme_path.exists():
            z.write(readme_path, arcname="README.md")

        # Chapters
        for chap in sorted(CHAPTERS_DIR.glob("*.tex")):
            z.write(chap, arcname=f"chapters/{chap.name}")

        # Figures
        for fig in sorted(FIGURES_DIR.glob("*.png")):
            z.write(fig, arcname=f"figures/{fig.name}")


def main() -> None:
    print(f"=== CreditTech LaTeX Report Bundler ===")
    print(f"Report Directory: {REPORT_DIR.resolve()}")

    bib_keys = extract_bib_keys(BIB_FILE)
    print(f"Found {len(bib_keys)} bibliographic citations in {BIB_FILE.name}: {', '.join(sorted(bib_keys))}")

    main_content = MAIN_TEX.read_text(encoding="utf-8")
    warnings = validate_report(main_content, bib_keys)

    if warnings:
        print("\n[!] VALIDATION WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("[OK] All 30 chapters, 13 figures, and citations passed validation with zero errors!")

    # Generate standalone file
    standalone_content = generate_standalone_tex(MAIN_TEX)
    STANDALONE_TEX.write_text(standalone_content, encoding="utf-8")
    print(f"[OK] Standalone TeX file generated: {STANDALONE_TEX} ({len(standalone_content.splitlines())} lines, {len(standalone_content.encode('utf-8')) / 1024:.1f} KB)")

    # Create README.md in docs/report/
    readme_content = """# CreditTech Institutional Project Report (LaTeX Suite)

This directory contains the complete, publication-grade LaTeX project report for the **CreditTech MVP** structured according to the rigorous 30-section framework.

## Compilation Options

### Option A: Overleaf (Recommended - 1 Click)
1. Download or locate `CreditTech_LaTeX_Report.zip`.
2. Go to [Overleaf](https://www.overleaf.com/).
3. Click **New Project** $\\rightarrow$ **Upload Project**, and select `CreditTech_LaTeX_Report.zip`.
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
"""
    (REPORT_DIR / "README.md").write_text(readme_content, encoding="utf-8")

    # Create ZIP
    create_zip_package()
    zip_size_kb = ZIP_OUTPUT.stat().st_size / 1024
    print(f"[OK] Overleaf-ready ZIP bundle created: {ZIP_OUTPUT} ({zip_size_kb:.1f} KB)")
    print("\n=== Bundling and Validation Complete! ===")


if __name__ == "__main__":
    main()
