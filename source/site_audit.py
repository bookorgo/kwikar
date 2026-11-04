#!/usr/bin/env python3
"""
Visitor-eye audit of the built site (public_html) for the KWIKAR Auditor role.

Serves public_html locally, opens EVERY page in Chromium (Playwright) on mobile (390 px) and
desktop (1300 px) and records problems a visitor or Google would notice:
  - JavaScript errors and failed/404 requests for our own files
  - horizontal scrolling (layout wider than the screen) and which elements cause it
  - broken local images, images without an alt attribute, very large image files
  - leftover template text: undefined, NaN, None, null, {placeholder}, "AED 0", empty prices
  - bad WhatsApp / phone links, empty links, links to missing pages
  - empty or duplicate titles, H1s and meta descriptions across the site
Writes audit-report.md and audit.json to the folder given as the first argument (default .).
Usage: python3 site_audit.py [out_dir] [--only path-substring]
"""
import functools, http.server, json, os, re, socketserver, sys, threading
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public_html')
ROOT = os.path.abspath(ROOT)
OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
ONLY = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''
PORT = 8799
BIG_IMAGE = 350 * 1024
SKIP = re.compile(r'^(api|assets|google[0-9a-f]+\.html)')
BAD_TEXT = re.compile(r'\b(undefined|NaN|None|null)\b|\{[a-z_]+(:[0-9a-z_-]+)?\}|AED\s*0(?![\d.,])'
                      r'|AED[ \t]*(?=$|/|per\b|\|)|\bAED [\d,]+\.\d(?!\d)', re.M)
WA_OK = re.compile(r'^https://wa\.me/\d{9,15}(\?text=[^\s]+)?$')
TEL_OK = re.compile(r'^tel:\+?\d{7,15}$')

JS_PAGE = r"""
() => {
  const W = window.innerWidth, out = {};
  out.overflow = document.documentElement.scrollWidth > W + 1;
  out.wide = [];
  if (out.overflow) {
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.width && r.right > W + 1 && getComputedStyle(el).position !== 'fixed') {
        const p = el.parentElement && el.parentElement.getBoundingClientRect();
        if (!p || p.right <= W + 1) {
          out.wide.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
            (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : '') +
            ' (' + Math.round(r.right) + 'px)');
          if (out.wide.length >= 4) break;
        }
      }
    }
  }
  out.imgs = [...document.images].map(i => ({src: i.currentSrc || i.src, ok: i.complete && i.naturalWidth > 0,
                                          alt: i.hasAttribute('alt') ? i.getAttribute('alt') : null}));
  out.links = [...document.querySelectorAll('a')].map(a => ({href: a.getAttribute('href') || '',
                                          text: (a.innerText || a.getAttribute('aria-label') || '').trim()}));
  out.text = document.body.innerText;
  out.title = document.title;
  out.h1 = [...document.querySelectorAll('h1')].map(h => h.innerText.trim());
  const m = document.querySelector('meta[name=description]');
  out.desc = m ? m.content : '';
  out.robots = (document.querySelector('meta[name=robots]') || {}).content || '';
  return out;
}
"""


def pages():
    for dp, _, files in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace(os.sep, '/')
        rel = '' if rel == '.' else rel + '/'
        if SKIP.match(rel):
            continue
        for f in files:
            if f.endswith('.html') and not SKIP.match(f):
                path = rel + ('' if f == 'index.html' else f)
                if ONLY in path:
                    yield '/' + path


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    handler.log_message = lambda *a: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def local_file(href, base):
    """Resolve an internal link to a file in public_html (clean URLs = folder/index.html)."""
    href = href.split('#')[0].split('?')[0]
    if not href:
        return True
    if not href.startswith('/'):
        href = os.path.normpath(os.path.join(os.path.dirname(base), href)).replace(os.sep, '/')
    p = os.path.join(ROOT, href.lstrip('/'))
    return (os.path.isfile(p) or os.path.isfile(os.path.join(p, 'index.html'))
            or os.path.isfile(p.rstrip('/') + '.html') or href.startswith('/api/'))


def main():
    from playwright.sync_api import sync_playwright
    srv = serve()
    issues = defaultdict(list)          # page -> list of problems
    seen_titles, seen_desc, seen_h1 = defaultdict(list), defaultdict(list), defaultdict(list)
    external_imgs = set()
    all_pages = sorted(pages())
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        views = {'mobile': dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True),
                 'desktop': dict(viewport={'width': 1300, 'height': 900})}
        ctxs = {k: browser.new_context(**v) for k, v in views.items()}
        for path in all_pages:
            for view, ctx in ctxs.items():
                page = ctx.new_page()
                errs, bad_req = [], []
                page.on('pageerror', lambda e: errs.append(str(e)[:160]))
                page.on('console', lambda m: m.type == 'error' and errs.append(m.text[:160]))
                page.on('response', lambda r: r.status >= 400 and f'127.0.0.1:{PORT}' in r.url
                        and bad_req.append(f'{r.status} {r.url.split(str(PORT))[1]}'))
                page.on('requestfailed', lambda r: f'127.0.0.1:{PORT}' in r.url
                        and bad_req.append(f'failed {r.url.split(str(PORT))[1]}'))
                try:
                    page.goto(f'http://127.0.0.1:{PORT}{path}', wait_until='load', timeout=30000)
                    page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                    page.wait_for_timeout(400)
                    d = page.evaluate(JS_PAGE)
                except Exception as e:
                    issues[path].append(f'[{view}] page did not load: {str(e)[:120]}')
                    page.close()
                    continue
                page.close()
                # JS errors: ignore errors caused by blocked external resources
                for e in sorted(set(errs)):
                    if 'net::ERR' in e or 'Failed to load resource' in e and 'kwikar' not in e:
                        continue
                    issues[path].append(f'[{view}] JavaScript error: {e}')
                for r in sorted(set(bad_req)):
                    issues[path].append(f'[{view}] missing file: {r}')
                if d['overflow']:
                    issues[path].append(f'[{view}] page scrolls sideways; too wide: ' + ', '.join(d['wide'] or ['?']))
                if view != 'mobile':
                    continue
                # checks that don't depend on screen size: run once
                for img in d['imgs']:
                    src = img['src']
                    if f'127.0.0.1:{PORT}' in src:
                        if not img['ok']:
                            issues[path].append(f'broken image: {src.split(str(PORT))[1]}')
                        f = os.path.join(ROOT, src.split(str(PORT))[1].split('?')[0].lstrip('/'))
                        if os.path.isfile(f) and os.path.getsize(f) > BIG_IMAGE:
                            issues[path].append(f'large image ({os.path.getsize(f)//1024} KB): {src.split(str(PORT))[1]}')
                    elif src.startswith('http'):
                        external_imgs.add(src)
                    if img['alt'] is None:
                        issues[path].append(f'image without alt attribute: {src[-60:]}')
                for m in sorted(set(x.group(0) for x in BAD_TEXT.finditer(d['text'])))[:5]:
                    i = d['text'].find(m)
                    ctx_line = d['text'][max(0, i - 40):i + len(m) + 30].replace('\n', ' / ')
                    issues[path].append(f'leftover/odd text "{m}": "{ctx_line}"')
                for a in d['links']:
                    h = a['href']
                    if not h or h == '#':
                        if not a['text']:
                            issues[path].append('empty link (no href and no text)')
                        continue
                    if 'wa.me' in h and not WA_OK.match(h):
                        issues[path].append(f'bad WhatsApp link: {h[:80]}')
                    elif h.startswith('tel:') and not TEL_OK.match(h.replace(' ', '')):
                        issues[path].append(f'bad phone link: {h}')
                    elif not re.match(r'^(https?:|mailto:|tel:|javascript:|#)', h) and not local_file(h, path):
                        issues[path].append(f'link to missing page: {h}')
                    if not a['text'] and h.startswith('/') and 'aria' not in a:
                        pass
                if 'noindex' in d['robots']:
                    continue
                if not d['title'].strip():
                    issues[path].append('empty <title>')
                if len(d['h1']) != 1 or not (d['h1'] or [''])[0]:
                    issues[path].append(f'H1 count {len(d["h1"])} (should be exactly 1, not empty)')
                if not d['desc']:
                    issues[path].append('no meta description')
                seen_titles[d['title'].strip()].append(path)
                seen_desc[d['desc'].strip()].append(path)
                if d['h1']:
                    seen_h1[d['h1'][0]].append(path)
        browser.close()
    srv.shutdown()

    site = []
    for label, seen in (('title', seen_titles), ('meta description', seen_desc), ('H1', seen_h1)):
        for val, ps in seen.items():
            if val and len(ps) > 1:
                site.append(f'duplicate {label} on {len(ps)} pages: "{val[:70]}" — ' + ', '.join(ps[:5]))
    for d in issues.values():
        d[:] = sorted(set(d))
    total = sum(len(v) for v in issues.values()) + len(site)
    report = {'pages_checked': len(all_pages), 'views': list(views), 'issues_total': total,
              'site_issues': site, 'page_issues': {k: v for k, v in sorted(issues.items()) if v},
              'external_images_not_checked': len(external_imgs)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(report, open(os.path.join(OUT, 'audit.json'), 'w'), indent=1, ensure_ascii=False)
    kinds = defaultdict(int)
    for v in report['page_issues'].values():
        for i in v:
            kinds[re.sub(r'^\[\w+\] ', '', i).split(':')[0].split(' (')[0]] += 1
    lines = [f'# Site audit — {len(all_pages)} pages, mobile + desktop', '',
             f'**{total} issues.** External (supplier) images are not checked here: '
             f'{len(external_imgs)} URLs.', '', '## By type', '']
    lines += [f'- {k}: {n}' for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])] or ['- none']
    lines += ['', '## Site-wide', ''] + ([f'- {s}' for s in site] or ['- none'])
    lines += ['', '## Per page', '']
    for p, v in report['page_issues'].items():
        lines.append(f'### {p}')
        lines += [f'- {i}' for i in v[:15]] + ([f'- … {len(v) - 15} more'] if len(v) > 15 else [])
    open(os.path.join(OUT, 'audit-report.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f'AUDIT: {len(all_pages)} pages, {total} issues -> {OUT}/audit-report.md')


if __name__ == '__main__':
    main()
