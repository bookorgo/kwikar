#!/usr/bin/env python3
"""
Weekly SEO health check for kwikar.com (run by .github/workflows/seo-check.yml).

Reads the live sitemaps and checks every URL: status 200, one <title>, one <h1>,
self canonical, meta description length, valid JSON-LD, no noindex on sitemap pages.
Also checks robots.txt and that old URLs still redirect. Writes a Markdown report
to seo-report.md and exits 1 when something is wrong (the workflow then opens an issue).
"""
import json, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

SITE = 'https://kwikar.com'
UA = {'User-Agent': 'KWIKAR-SEO-check/1.0 (+https://kwikar.com)'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def get(url, follow=True):
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(urllib.request.Request(url, headers=UA), timeout=30)
        return r.status, r.read().decode('utf-8', 'replace'), r.headers
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode('utf-8', 'replace') if err.fp else '', err.headers
    except Exception as err:
        return 0, str(err), {}


def sitemap_urls():
    status, body, _ = get(SITE + '/sitemap.xml')
    if status != 200:
        return None
    urls = []
    for sm in re.findall(r'<loc>(.*?)</loc>', body):
        _, sub, _ = get(sm)
        urls += re.findall(r'<loc>(.*?)</loc>', sub)
    return urls


def check_page(url):
    problems = []
    status, html, _ = get(url)
    if status != 200:
        return url, [f'HTTP {status}']
    titles = re.findall(r'<title>(.*?)</title>', html, re.S)
    if len(titles) != 1 or not titles[0].strip():
        problems.append(f'{len(titles)} <title> tags')
    h1 = len(re.findall(r'<h1[\s>]', html))
    if h1 != 1:
        problems.append(f'{h1} <h1> tags')
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not canon or canon.group(1).rstrip('/') != url.rstrip('/'):
        problems.append('canonical is ' + (canon.group(1) if canon else 'missing'))
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    if not desc:
        problems.append('meta description missing')
    elif not 50 <= len(desc.group(1)) <= 170:
        problems.append(f'meta description {len(desc.group(1))} chars')
    if re.search(r'<meta name="robots" content="[^"]*noindex', html):
        problems.append('noindex on a sitemap URL')
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(block)
        except Exception:
            problems.append('invalid JSON-LD')
    if '{from}' in html:
        problems.append('unfilled {from} placeholder')
    return url, problems


def main():
    report, failed = ['# KWIKAR weekly SEO check', ''], False
    urls = sitemap_urls()
    if urls is None:
        print('# KWIKAR weekly SEO check\n\nsitemap.xml could not be fetched.')
        open('seo-report.md', 'w').write('sitemap.xml could not be fetched.\n')
        sys.exit(1)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(check_page, urls))
    bad = [(u, p) for u, p in results if p]
    report.append(f'Checked {len(urls)} sitemap URLs: {len(urls) - len(bad)} OK, {len(bad)} with problems.')
    if bad:
        failed = True
        report += ['', '## Pages with problems', ''] + [f'- {u}: {"; ".join(p)}' for u, p in bad]

    status, robots, _ = get(SITE + '/robots.txt')
    robot_issues = []
    if status != 200:
        robot_issues.append(f'robots.txt HTTP {status}')
    else:
        if 'Sitemap: https://kwikar.com/sitemap.xml' not in robots:
            robot_issues.append('robots.txt has no sitemap line')
        if re.search(r'User-agent: \*\s*\nDisallow: /\s*$', robots, re.M):
            robot_issues.append('robots.txt blocks the whole site')
    redirects = [('/tour/136', '/activities/dubai/burj-khalifa-at-the-top-tickets'), ('/attractions', '/destinations'), ('/home.html', '/')]
    for old, new in redirects:
        s, _, h = get(SITE + old, follow=False)
        loc = (h.get('Location') if h else '') or ''
        if s != 301 or not loc.rstrip('/').endswith(new.rstrip('/') if new != '/' else 'kwikar.com'):
            robot_issues.append(f'{old} should 301 to {new} (got {s} {loc})')
    if robot_issues:
        failed = True
        report += ['', '## Site-wide problems', ''] + [f'- {x}' for x in robot_issues]
    report += ['', 'Nothing was changed on the site. Fix the items above, or ask Claude to fix them.']
    text = '\n'.join(report)
    open('seo-report.md', 'w').write(text + '\n')
    print(text)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
