"""Regenerate every .rdlc in src/EOMPrinting/Reports from these scripts.

Run from anywhere:  python tools/rdlc/build_all.py
Order matters: gen_tps.py replaces the TotalPackedStock.rdlc written by gen_batch3.py.
"""
import os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.normpath(os.path.join(here, "..", "..", "src", "EOMPrinting", "Reports"))
steps = [("gen_posting.py", os.path.join(out, "PostingBlock.rdlc")),
         ("gen_reports.py", out), ("gen_batch3.py", out), ("gen_batch4.py", out), ("gen_tps.py", out)]
for script, arg in steps:
    print("running", script)
    subprocess.run([sys.executable, os.path.join(here, script), arg], check=True)
print("done:", out)
