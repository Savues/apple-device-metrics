#!/usr/bin/env python3
"""Compare every English Markdown file with its .zh.md translation.

Usage: python3 scripts/check_i18n.py [file.md ...]
       (no arguments: every *.zh.md in the repo, found by walking from the root)

Checks that the translation keeps the numbers, the fenced code blocks, the
inline code spans, the table rows, the heading count, the relative links and
the language switch line. Run inside verify.py, so a drift fails CI.
"""
import os
import re
import sys
from collections import Counter

NUM = re.compile(r"(?<![A-Za-z])[-−+]?\d[\d,]*(?:\.\d+)?")
CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")


def zh_path(p):
    d, f = os.path.split(p)
    return os.path.join(d, f[:-3] + ".zh.md")


def strip_header(text):
    # drop the language switch + translation note added at the top
    lines = [l for l in text.splitlines()
             if not l.startswith("[English]") and "本文为英文原文的中文翻译" not in l]
    return "\n".join(lines)


def nums(t):
    return Counter(n.replace(",", "").replace("−", "-") for n in NUM.findall(t))


def fenced(t):
    return re.findall(r"```.*?```", t, re.S)


def table_rows(t):
    return sum(1 for l in t.splitlines() if l.lstrip().startswith("|"))


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) > 1:
    targets = sys.argv[1:]
else:
    targets = []
    for dirpath, skip, files in os.walk(ROOT):
        if any(x in dirpath for x in (".git", "_site", "__pycache__")):
            continue
        for f in sorted(files):
            if f.endswith(".md") and not f.endswith(".zh.md"):
                p = os.path.relpath(os.path.join(dirpath, f), ROOT)
                if os.path.exists(zh_path(os.path.join(ROOT, p))):
                    targets.append(p)
    targets.sort()

bad = 0
for en in targets:
    en = os.path.join(ROOT, en) if not os.path.isabs(en) else en
    zh = zh_path(en)
    if not os.path.exists(zh):
        print(f"FAIL {zh}: missing"); bad += 1; continue
    a = open(en, encoding="utf-8").read()
    b = strip_header(open(zh, encoding="utf-8").read())
    res = []
    na, nb = nums(a), nums(b)
    miss = na - nb
    extra = nb - na
    res.append(("numbers", not miss,
                f"missing in zh: {dict(list(miss.items())[:12])}" if miss else ""))
    if extra:
        print(f"  note {zh}: extra numbers in zh (check): {dict(list(extra.items())[:12])}")
    fa, fb = fenced(a), fenced(b)
    res.append(("code blocks identical", fa == fb, f"{len(fa)} vs {len(fb)}"))
    ca = Counter(" ".join(x.split()) for x in CODE.findall(re.sub(r"```.*?```", "", a, flags=re.S)))
    cb = Counter(" ".join(x.split()) for x in CODE.findall(re.sub(r"```.*?```", "", b, flags=re.S)))
    cm = ca - cb
    res.append(("inline code kept", not cm, f"missing: {list(cm)[:10]}" if cm else ""))
    res.append(("table rows", table_rows(a) == table_rows(b),
                f"{table_rows(a)} vs {table_rows(b)}"))
    head_a = sum(1 for l in a.splitlines() if l.startswith("#"))
    head_b = sum(1 for l in b.splitlines() if l.startswith("#"))
    res.append(("heading count", head_a == head_b, f"{head_a} vs {head_b}"))
    broken = []
    for t in LINK.findall(open(zh, encoding="utf-8").read()):
        if re.match(r"[a-z]+:", t) or t.startswith("#"):
            continue
        full = os.path.normpath(os.path.join(os.path.dirname(zh), t.split("#")[0]))
        if not os.path.exists(full) and not os.path.exists(full.replace(".zh.md", ".md")):
            broken.append(t)
    res.append(("relative links resolve", not broken, str(broken[:5])))
    head = open(zh, encoding="utf-8").read().splitlines()[:10]
    res.append(("language switch at top",
                any(l.startswith("[English](") for l in head), ""))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", b))
    res.append(("is Chinese", cjk > len(b) * 0.08, f"{cjk} CJK chars"))
    for name, ok, det in res:
        print(f"{'PASS' if ok else 'FAIL'} {zh}: {name}" + (f" — {det}" if det and not ok else ""))
        bad += not ok
print(f"{len(targets)} pairs checked — " +
      ("ALL PASS" if not bad else f"{bad} FAIL"))
sys.exit(1 if bad else 0)
