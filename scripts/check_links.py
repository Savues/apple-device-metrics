#!/usr/bin/env python3
"""Fail if any relative Markdown link points to a file that does not exist."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"\]\(([^)\s]+)\)")

files = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, check=True,
                       capture_output=True, text=True).stdout.split()
broken = []
for md in files:
    text = open(os.path.join(ROOT, md), encoding="utf-8").read()
    for target in LINK.findall(text):
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        full = os.path.normpath(os.path.join(ROOT, os.path.dirname(md), path))
        if not os.path.exists(full):
            broken.append(f"{md}: {target}")

for b in broken:
    print("BROKEN", b)
print(f"{len(files)} files checked, {len(broken)} broken links")
sys.exit(1 if broken else 0)
