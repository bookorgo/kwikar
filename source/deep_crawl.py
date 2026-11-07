#!/usr/bin/env python3
"""
Deep live crawl of kwikar.com for indexing problems (run by .github/workflows/deep-crawl.yml).

Finds what Search Console reports as indexing issues, before Google does:
  - sitemap URLs that redirect, 404, are noindex, or have a canonical pointing elsewhere
  - internal links that point to redirects or broken pages (and on which pages)
  - indexable pages that are missing from the sitemap, sitemap pages nobody links to
  - broken local images, X-Robots-Tag headers, slow or very large pages
  - duplicate titles / meta descriptions across indexable pages
Writes crawl-report.md and crawl.json into the folder given as the first argument.
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

SITE = 'https://kwikar.com'
HOST = 'kwikar.com'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; KWIKAR-deep-crawl/1.0; +https://kwikar.com)'}
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
SKIP = re.compile(r'^/(api|search)(/|$)|^/assets/|\.(webp|jpg|jpeg|png|svg|css|js|xml|txt|php|ico|pdf)$', re.I)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url, body=True):
    t = time.time()
    try:
        r = OPENER.open(urllib.request.Request(url, headers=UA, method='GET' if body else 'HEAD'), timeout=40)
        data = r.read() if body else b''
        return r.status, dict(r.headers), data.decode('utf-8', 'replace'), time.time() - t, len(data)
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers or {}), '', time.time() - t, 0
    except Exception as err:
        return 0, {}, str(err), time.time() - t, 0


def norm(href, base):
    if not href or href.startswith(('mailto:', 'tel:', 'javascript:', '#', 'data:', 'whatsapp:')):
        return None
    u = urllib.parse.urljoin(base, href)
    p = urllib.parse.urlsplit(u)
    if p.netloc not in (HOST, 'www.' + HOST):
        return None
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, ''))


def main():
    os.makedirs(OUT, exist_ok=True)
    st, _, idx, _, _ = fetch(SITE + '/sitemap.xml')
    sitemap = []
    for sm in re.findall(r'<loc>(.*?)</loc>', idx):
        _, _, sub, _, _ = fetch(sm)
        sitemap += re.findall(r'<loc>(.*?)</loc>', sub)
    sm_set = set(sitemap)
    pages, links_from, images = {}, defaultdict(set), defaultdict(set)
    queue, seen = list(dict.fromkeys([SITE + '/'] + sitemap)), set()

    def crawl(url):
        s, h, html, dt, size = fetch(url)
        info = {'status': s, 'location': h.get('Location') or h.get('location'), 'time': round(dt, 2), 'size': size,
                'xrobots': h.get('X-Robots-Tag') or h.get('x-robots-tag')}
        out_links, imgs = [], []
        if s == 200 and 'html' in (h.get('Content-Type') or h.get('content-type') or ''):
            info['title'] = (re.search(r'<title>(.*?)</title>', html, re.S) or [None, ''])[1].strip()
            m = re.search(r'<meta name="description" content="([^"]*)"', html)
            info['desc'] = m.group(1) if m else ''
            m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
            info['canonical'] = m.group(1) if m else None
            info['noindex'] = bool(re.search(r'<meta name="robots" content="[^"]*noindex', html))
            info['h1'] = len(re.findall(r'<h1[\s>]', html))
            for href in re.findall(r'<a\s[^>]*href="([^"]+)"', html):
                u = norm(href.replace('&amp;', '&'), url)
                if u:
                    out_links.append(u)
            for src in re.findall(r'<img\s[^>]*src="([^"]+)"', html):
                u = norm(src.replace('&amp;', '&'), url)
                if u:
                    imgs.append(u)
        return url, info, out_links, imgs

    with ThreadPoolExecutor(8) as pool:
        while queue:
            batch = [u for u in queue if u not in seen][:64]
            queue = [u for u in queue if u not in seen and u not in batch]
            if not batch:
                break
            seen.update(batch)
            for url, info, outs, imgs in pool.map(crawl, batch):
                pages[url] = info
                for u in outs:
                    links_from[u].add(url)
                    path = urllib.parse.urlsplit(u).path
                    if u not in seen and not SKIP.search(path) and len(seen) + len(queue) < 1500:
                        queue.append(u)
                for u in imgs:
                    images[u].add(url)
            queue = list(dict.fromkeys(queue))

    # link targets that were not crawled as pages (assets etc.) -> HEAD check
    others = [u for u in links_from if u not in pages and not urllib.parse.urlsplit(u).path.startswith('/api/')]
    with ThreadPoolExecutor(8) as pool:
        for u, r in zip(others, pool.map(lambda u: fetch(u, body=False), others)):
            pages[u] = {'status': r[0], 'location': r[1].get('Location') or r[1].get('location'), 'asset': True}
    imgs = [u for u in images if '/assets/' in u]
    img_status = {}
    with ThreadPoolExecutor(8) as pool:
        for u, r in zip(imgs, pool.map(lambda u: fetch(u, body=False), imgs)):
            img_status[u] = r[0]

    issues = defaultdict(list)
    for u in sitemap:
        p = pages.get(u, {})
        if p.get('status') != 200:
            issues['Sitemap URL does not return 200 (redirect or error)'].append(f'{u} → {p.get("status")} {p.get("location") or ""}')
        elif p.get('noindex'):
            issues['Sitemap URL has noindex'].append(u)
        elif p.get('canonical') and p['canonical'] != u:
            issues['Sitemap URL canonical points to a different URL'].append(f'{u} → canonical {p["canonical"]}')
        if p.get('xrobots'):
            issues['X-Robots-Tag header on a sitemap URL'].append(f'{u}: {p["xrobots"]}')
    for u, srcs in links_from.items():
        p = pages.get(u, {})
        s = p.get('status')
        ex = ', '.join(sorted(srcs)[:3]) + (f' (+{len(srcs) - 3} more)' if len(srcs) > 3 else '')
        if s in (301, 302, 307, 308):
            issues['Internal links to a redirect'].append(f'{u} → {p.get("location")} — linked from {ex}')
        elif s and s >= 400 or s == 0:
            issues['Internal links to a broken page'].append(f'{u} → {s} — linked from {ex}')
    indexable = [u for u, p in pages.items() if p.get('status') == 200 and not p.get('asset') and not p.get('noindex')
                 and p.get('canonical') == u and '?' not in u]
    for u in indexable:
        if u not in sm_set:
            issues['Indexable page missing from the sitemap'].append(u)
    for u in sitemap:
        if u != SITE + '/' and not (links_from.get(u, set()) - {u}):
            issues['Sitemap page with no internal links to it (orphan)'].append(u)
    for u, s in img_status.items():
        if s != 200:
            issues['Broken image'].append(f'{u} → {s} — on {", ".join(sorted(images[u])[:2])}')
    for u in indexable:
        p = pages[u]
        if p.get('time', 0) > 3:
            issues['Slow page (over 3 s to download)'].append(f'{u}: {p["time"]} s')
        if p.get('size', 0) > 600_000:
            issues['Large HTML (over 600 KB)'].append(f'{u}: {p["size"] // 1024} KB')
        if p.get('h1') != 1:
            issues['Not exactly one H1'].append(f'{u}: {p.get("h1")}')
    for field, label in (('title', 'Duplicate title'), ('desc', 'Duplicate meta description')):
        groups = defaultdict(list)
        for u in indexable:
            if pages[u].get(field):
                groups[pages[u][field]].append(u)
        for v, us in groups.items():
            if len(us) > 1:
                issues[label].append(f'"{v[:70]}" on {len(us)} pages: ' + ', '.join(us[:4]))

    report = [f'# Deep crawl of {SITE}', '',
              f'Sitemap URLs: {len(sitemap)}. Pages crawled: {sum(1 for p in pages.values() if not p.get("asset"))}. '
              f'Indexable pages found: {len(indexable)}. Total issues: {sum(len(v) for v in issues.values())}.', '']
    for k, v in sorted(issues.items(), key=lambda kv: -len(kv[1])):
        report += [f'## {k} ({len(v)})', ''] + [f'- {x}' for x in v[:60]] + ([f'- … {len(v) - 60} more'] if len(v) > 60 else []) + ['']
    if not issues:
        report.append('No issues found.')
    open(os.path.join(OUT, 'crawl-report.md'), 'w').write('\n'.join(report) + '\n')
    json.dump({'sitemap': sitemap, 'pages': pages, 'issues': issues}, open(os.path.join(OUT, 'crawl.json'), 'w'), indent=1, default=list)
    print('\n'.join(report[:6]))


if __name__ == '__main__':
    main()
