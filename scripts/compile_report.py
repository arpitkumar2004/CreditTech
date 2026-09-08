"""Script to compile the CreditTech LaTeX Report using local MiKTeX.

Handles:
1. Locating MiKTeX binary directory automatically.
2. Sanitizing PATH (removing invalid file entries like python.exe).
3. Compiling the report with --enable-installer (auto-downloading any needed packages).
4. Running bibtex and multi-pass pdflatex to resolve all citations and cross-references.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPORT_DIR = Path("docs/report")
TEX_FILE = "CreditTech_Final_Project_Report.tex"
JOB_NAME = "CreditTech_Final_Project_Report"

POSSIBLE_MIKTEX_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
    Path(r"C:\Program Files\MiKTeX\miktex\bin\x64"),
]


def find_miktex_bin() -> Path | None:
    # Check if already in PATH
    which_pdf = shutil.which("pdflatex")
    if which_pdf:
        return Path(which_pdf).parent

    # Check common installation locations
    for p in POSSIBLE_MIKTEX_PATHS:
        if (p / "pdflatex.exe").exists():
            return p

    return None


def get_sanitized_env(miktex_bin: Path) -> dict[str, str]:
    env = os.environ.copy()
    raw_path = env.get("PATH", "")
    paths = raw_path.split(";")

    # Remove entries that point directly to files (e.g. python.exe)
    clean_paths = [
        p.strip() for p in paths
        if p.strip() and not p.strip().lower().endswith(".exe") and not p.strip().lower().endswith(".exe\\")
    ]

    # Prepend MiKTeX bin directory
    clean_paths.insert(0, str(miktex_bin.resolve()))
    env["PATH"] = ";".join(clean_paths)
    return env


def run_command(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
    print(f"Executing: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert process.stdout is not None
    for line in process.stdout:
        # Print important lines
        if any(keyword in line for keyword in [
            "Output written on", "Error", "Fatal", "warning", "Warning", "Entering", "Transcript", "bytes"
        ]):
            print(f"  [TeX] {line.strip()}")
    return process.wait()


def main() -> int:
    print("=== CreditTech Automated Local LaTeX Compiler ===")
    miktex_bin = find_miktex_bin()

    if not miktex_bin:
        print("[ERROR] MiKTeX was not found on your system.")
        print("Please install it via: winget install MiKTeX.MiKTeX")
        return 1

    print(f"[OK] Found MiKTeX at: {miktex_bin}")
    pdflatex_exe = str(miktex_bin / "pdflatex.exe")
    bibtex_exe = str(miktex_bin / "bibtex.exe")
    env = get_sanitized_env(miktex_bin)

    print(f"[1/3] Running initial pdflatex pass on {TEX_FILE}...")
    code = run_command([
        pdflatex_exe,
        "-interaction=nonstopmode",
        "--enable-installer",
        TEX_FILE
    ], env, REPORT_DIR)

    print(f"[2/3] Running bibtex to resolve citations...")
    run_command([
        bibtex_exe,
        JOB_NAME
    ], env, REPORT_DIR)

    print(f"[3/3] Running final pdflatex pass to resolve references & cross-links...")
    code = run_command([
        pdflatex_exe,
        "-interaction=nonstopmode",
        "--enable-installer",
        TEX_FILE
    ], env, REPORT_DIR)

    pdf_output = REPORT_DIR / f"{JOB_NAME}.pdf"
    if pdf_output.exists():
        pdf_size_mb = pdf_output.stat().st_size / (1024 * 1024)
        print("\n=======================================================")
        print(f"SUCCESS! PDF compiled successfully:")
        print(f"Path: {pdf_output.resolve()}")
        print(f"Size: {pdf_size_mb:.2f} MB")
        print("=======================================================")
        return 0
    else:
        print("\n[ERROR] PDF generation did not complete. Check log in docs/report/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
