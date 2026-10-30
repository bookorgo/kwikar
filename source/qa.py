#!/usr/bin/env python3
"""QA for the built site (run after build.py): internal links, JSON-LD, one H1, no unfilled placeholders,
title and meta description present. Exit 1 on any problem."""
import glob, json, os, re, sys
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public_html'))
os.chdir(OUT)
problems = []
for f in [x for x in glob.glob('**/*.html', recursive=True) if not re.match(r'google[0-9a-f]+\.html$', x)]:
    s = open(f, encoding='utf-8').read()
    for h in re.findall(r'href="(/[^"#?]*)', s):
        if h != '/' and not (os.path.exists(h.strip('/') + '/index.html') or os.path.exists(h.strip('/'))):
            problems.append(f'{f}: broken link {h}')
    for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(j)
        except Exception:
            problems.append(f'{f}: invalid JSON-LD')
    if f.endswith('index.html') and s.count('<h1') != 1:
        problems.append(f'{f}: {s.count("<h1")} h1 tags')
    for ph in ('{from}', '{price:', '{link:', '{money', '{tour}'):
        if ph in s:
            problems.append(f'{f}: unfilled placeholder {ph}')
    if not re.search(r'<title>[^<]+</title>', s) or 'name="description"' not in s:
        problems.append(f'{f}: missing title or description')
print('\n'.join(problems[:50]) or 'QA OK')
sys.exit(1 if problems else 0)
