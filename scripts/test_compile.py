import os
import subprocess
import sys
from pathlib import Path

miktex_bin = Path(r"C:\Users\RDRL\AppData\Local\Programs\MiKTeX\miktex\bin\x64")
env = os.environ.copy()
paths = env.get("PATH", "").split(";")
clean = [p.strip() for p in paths if p.strip() and not p.strip().lower().endswith(".exe") and not p.strip().lower().endswith(".exe\\")]
clean.insert(0, str(miktex_bin))
env["PATH"] = ";".join(clean)

cmd = [
    str(miktex_bin / "pdflatex.exe"),
    "-interaction=nonstopmode",
    "--enable-installer",
    "CreditTech_Final_Project_Report.tex"
]

print(f"Running: {' '.join(cmd)}")
proc = subprocess.run(cmd, cwd="docs/report", env=env, capture_output=True, text=True, errors="replace")

print(f"Return code: {proc.returncode}")
print("--- STDOUT (last 50 lines) ---")
print("\n".join(proc.stdout.splitlines()[-50:]))
if proc.stderr:
    print("--- STDERR ---")
    print(proc.stderr[-1000:])
