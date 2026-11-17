#!/usr/bin/env python3
"""Assemble the GitHub Pages site into _site/ (not committed).

Copies site/ plus the published data files the page reads, so the page always
shows the repository's current numbers.
    python3 scripts/build_site.py && python3 -m http.server -d _site
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
DATA = [
    "docs/iphone17-forecast.json", "docs/iphone17-forecast.csv",
    "docs/predictions.json", "docs/charging-summary.json",
    "devices/iphone-01/analytics-timeline.csv",
    "devices/iphone-01/health-samples.csv",
    "devices/iphone-01/charging-sessions.csv",
]

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
shutil.copytree(os.path.join(ROOT, "site"), OUT)
os.makedirs(os.path.join(OUT, "data"))
for p in DATA:
    shutil.copy(os.path.join(ROOT, p), os.path.join(OUT, "data"))
# Cache-bust static assets with a content hash so updates show immediately.
import hashlib  # noqa: E402
html = os.path.join(OUT, "index.html")
text = open(html, encoding="utf-8").read()
for asset in ("style.css", "i18n.js", "app.js"):
    h = hashlib.sha1(open(os.path.join(OUT, asset), "rb").read()).hexdigest()[:8]
    text = text.replace(f'"{asset}"', f'"{asset}?v={h}"')
open(html, "w", encoding="utf-8").write(text)
open(os.path.join(OUT, ".nojekyll"), "w").close()
print(f"built {os.path.relpath(OUT, ROOT)}/ with {len(DATA)} data files")
