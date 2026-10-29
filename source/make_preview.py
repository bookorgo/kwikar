#!/usr/bin/env python3
"""Make a browsable copy of public_html with relative links (for previews without a server)."""
import os, re, shutil, sys
SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public_html'))
DST = sys.argv[1]
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('api', '.htaccess', 'robots.txt', 'sitemap.xml'))

JS = r"""<script>window.KW_LINK=function(p){var P='%s';if(/^[a-z]+:/i.test(p))return p;var m=p.match(/^\/tour\/(\d+)/);if(m)return P+'tour/index.html?id='+m[1];var h='',q='',i=p.indexOf('#');if(i>-1){h=p.slice(i);p=p.slice(0,i)}i=p.indexOf('?');if(i>-1){q=p.slice(i);p=p.slice(0,i)}if(p==='/'||p==='')return P+'index.html'+q+h;if(/^\/(assets|api)\//.test(p)||/\.[a-z0-9]+$/i.test(p))return P+p.slice(1)+q+h;return P+p.replace(/^\/|\/$/g,'')+'/index.html'+q+h};</script>"""

def mapper(prefix):
    def m(p):
        if p.startswith('//'):
            return p
        t = re.match(r'^/tour/(\d+)', p)
        if t:
            return f'{prefix}tour/index.html?id={t.group(1)}'
        k = re.search(r'[?#]', p)
        path, rest = (p[:k.start()], p[k.start():]) if k else (p, '')
        if path in ('/', ''):
            return prefix + 'index.html' + rest
        if path.startswith('/assets/') or re.search(r'\.[a-z0-9]+$', path, re.I):
            return prefix + path[1:] + rest
        return prefix + path.strip('/') + '/index.html' + rest
    return m

for dirpath, _, files in os.walk(DST):
    for f in files:
        if not f.endswith('.html'):
            continue
        full = os.path.join(dirpath, f)
        depth = os.path.relpath(full, DST).count(os.sep)
        prefix = '../' * depth
        m = mapper(prefix)
        s = open(full, encoding='utf-8').read()
        s = re.sub(r'(href|src|action)="(/[^"]*)"', lambda x: f'{x.group(1)}="{m(x.group(2))}"', s)
        s = re.sub(r'srcset="([^"]*)"', lambda x: 'srcset="' + re.sub(r'(^|,\s*)(/[^\s,]+)', lambda y: y.group(1) + m(y.group(2)), x.group(1)) + '"', s)
        s = re.sub(r"url\('(/[^']*)'\)", lambda x: f"url('{m(x.group(1))}')", s)
        s = s.replace('</head>', (JS % prefix) + '\n</head>', 1)
        if full == os.path.join(DST, 'index.html'):
            # the artifact host adds its own document wrapper to the main page
            s = re.sub(r'<!doctype html>\s*<html[^>]*>\s*<head>', '', s, flags=re.I)
            s = s.replace('</head>', '').replace('</body>', '').replace('</html>', '')
            s = re.sub(r'<body[^>]*>', '', s)
        open(full, 'w', encoding='utf-8').write(s)
print('preview written to', DST)
