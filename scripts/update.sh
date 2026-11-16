#!/bin/sh
# One-command refresh after receiving new iOS analytics files.
#
#   scripts/update.sh /path/Analytics-2026-11-17.ips [more.ips ...]
#   scripts/update.sh            # no files: just regenerate + verify
#
# Steps: whitelist-extract and archive each .ips -> rebuild timeline CSV ->
# regenerate forecast (base, rates, plateau all re-derived) -> run checks.
# Raw .ips files are never copied into the repository.
set -eu
cd "$(dirname "$0")/.."

if [ "$#" -gt 0 ]; then
    python3 scripts/extract_analytics.py --archive "$@"
else
    # Rebuild the timeline anyway, in case a snapshot JSON was edited by hand.
    python3 -c 'import sys; sys.path.insert(0, "scripts"); import extract_analytics as e; e.build_timeline(e.load_archive())'
fi
python3 scripts/forecast.py > /dev/null
echo "forecast regenerated: $(python3 -c 'import json;b=json.load(open("docs/iphone17-forecast.json"))["base"];print(b["date"], b["cycle"], "cycles", b["ncc_mah"], "mAh")')"
python3 scripts/verify.py > /tmp/adm-verify.$$ 2>&1 || {
    grep -E 'FAIL|FAILURES' /tmp/adm-verify.$$
    rm -f /tmp/adm-verify.$$
    exit 1
}
tail -n 1 /tmp/adm-verify.$$
rm -f /tmp/adm-verify.$$
git status --short
echo "Prose in docs/*.md that quotes the base (date / cycle / NCC) still needs a manual review."
