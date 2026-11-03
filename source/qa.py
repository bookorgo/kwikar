#!/usr/bin/env python3
"""QA for the built site (run after build.py): internal links, JSON-LD, one H1, no unfilled placeholders,
title and meta description present; on indexable pages title <= 60 and meta description 120-160 chars;
no online-checkout wording in visible text. Exit 1 on any problem."""
import glob, html, json, os, re, sys
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
    elif f.endswith('index.html') and not re.search(r'<meta name="robots" content="[^"]*noindex', s):
        t = html.unescape(re.search(r'<title>([^<]+)</title>', s).group(1))
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        d = html.unescape(m.group(1)) if m else ''
        if len(t) > 60:
            problems.append(f'{f}: title {len(t)} chars (max 60)')
        if not 120 <= len(d) <= 160:
            problems.append(f'{f}: meta description {len(d)} chars (120-160)')
    text = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', s, flags=re.S))
    for w in re.findall(r'\b(book now|checkout|pay online|instant confirmation)\b', text, re.I):
        problems.append(f'{f}: banned wording "{w}"')
print('\n'.join(problems[:50]) or 'QA OK')
sys.exit(1 if problems else 0)
