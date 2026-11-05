#!/usr/bin/env python3
"""
Tell Bing (and other IndexNow engines) which kwikar.com pages changed.

Usage (from the repo root, in a GitHub Action after the deploy branch was pushed):
    python3 source/indexnow.py <old-commit> <new-commit>

Takes the pages under public_html that changed between the two commits, keeps only
URLs that are in our sitemaps (indexable pages), waits until the key file is live,
then POSTs them to https://api.indexnow.org/indexnow. Never fails the workflow:
problems are printed and the script exits 0.

The key is public by design (IndexNow checks https://kwikar.com/<key>.txt); it is not a secret.
"""
import glob, json, os, re, subprocess, sys, time, urllib.error, urllib.request

SITE = 'https://kwikar.com'
HOST = 'kwikar.com'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public_html')
UA = {'User-Agent': 'KWIKAR-IndexNow/1.0 (+https://kwikar.com)'}


def find_key():
    for path in glob.glob(os.path.join(PUB, '*.txt')):
        name = os.path.basename(path)[:-4]
        if re.fullmatch(r'[0-9a-f]{32}', name) and open(path).read().strip() == name:
            return name
    return None


def sitemap_urls():
    urls = set()
    for path in glob.glob(os.path.join(PUB, 'sitemap*.xml')):
        for loc in re.findall(r'<loc>(.*?)</loc>', open(path, encoding='utf-8').read()):
            if not loc.endswith('.xml'):
                urls.add(loc.rstrip('/') or SITE)
    return urls


def file_to_url(path):
    rel = path[len('public_html/'):]
    if rel == 'index.html':
        return SITE + '/'
    if rel.endswith('/index.html'):
        return f'{SITE}/{rel[:-len("/index.html")]}'
    return None


def changed_urls(old, new):
    try:
        out = subprocess.run(['git', '-C', ROOT, 'diff', '--name-only', '--diff-filter=AM', old, new, '--', 'public_html'],
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as err:
        print('git diff failed:', err.stderr.strip())
        return []
    allowed = sitemap_urls()
    urls = []
    for f in out.split():
        u = file_to_url(f)
        if u and (u.rstrip('/') or SITE) in allowed | {SITE}:
            urls.append(u)
    return sorted(set(urls))


def key_is_live(key, tries=10, wait=30):
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f'{SITE}/{key}.txt', headers=UA), timeout=20)
            if r.read().decode().strip() == key:
                return True
        except Exception as err:
            print(f'key file not live yet ({err})')
        time.sleep(wait)
    return False


def main():
    if len(sys.argv) != 3 or set(sys.argv[1]) <= {'0'}:
        print('IndexNow: no usable commit range, skipped')
        return
    key = find_key()
    if not key:
        print('IndexNow: no key file in public_html, skipped')
        return
    urls = changed_urls(sys.argv[1], sys.argv[2])
    if not urls:
        print('IndexNow: no indexable pages changed')
        return
    if not key_is_live(key):
        print('IndexNow: key file is not live on kwikar.com yet, skipped this time')
        return
    body = json.dumps({'host': HOST, 'key': key, 'keyLocation': f'{SITE}/{key}.txt', 'urlList': urls[:10000]}).encode()
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, method='POST',
                                 headers={**UA, 'Content-Type': 'application/json; charset=utf-8'})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        print(f'IndexNow: HTTP {r.status} for {len(urls)} URLs')
    except urllib.error.HTTPError as err:
        print(f'IndexNow: HTTP {err.code} {err.read()[:300]!r} for {len(urls)} URLs')
    except Exception as err:
        print(f'IndexNow: failed ({err})')
    for u in urls[:50]:
        print(' ', u)


if __name__ == '__main__':
    main()
