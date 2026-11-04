#!/usr/bin/env python3
"""
Free SEO data for the KWIKAR team (run by .github/workflows/seo-data.yml).

Collects, with free sources only:
  1. Keyword ideas: Google and Bing autocomplete (UAE, English) for every seed in
     source/seo/keyword-seeds.txt plus common modifiers. Suggestions that appear in
     both engines and for several modifiers are the strongest demand signals.
  2. Google Search Console (only when the GSC_SA_JSON secret is set): queries and
     pages for the last 28 days, "quick win" queries (position 4-20, low CTR), and a
     history file so rankings can be tracked over time.
  3. Bing Webmaster (only when the BING_API_KEY secret is set): query stats.
  4. PageSpeed Insights (mobile) for a few key pages (free PAGESPEED_API_KEY secret recommended;
     without it Google usually answers 429 to GitHub runners).

Writes everything into the folder given as the first argument (default ./seo-data).
Never fails the workflow because one source is down: each source writes its own error.
"""
import csv, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else 'seo-data'
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://kwikar.com/'
UA = {'User-Agent': 'Mozilla/5.0 (KWIKAR keyword research; +https://kwikar.com)'}
MODIFIERS = ['', 'price', 'tickets', 'timings', 'best', 'for kids', 'vs', 'how']
TODAY = dt.date.today().isoformat()
os.makedirs(OUT, exist_ok=True)


def get_json(url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})}, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def save(name, obj):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def seeds():
    with open(os.path.join(HERE, 'seo', 'keyword-seeds.txt'), encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]


# ---------- 1. autocomplete ----------
def google_suggest(q):
    u = 'https://suggestqueries.google.com/complete/search?' + urllib.parse.urlencode(
        {'client': 'firefox', 'hl': 'en', 'gl': 'ae', 'q': q})
    return get_json(u)[1]


def bing_suggest(q):
    u = 'https://api.bing.com/osjson.aspx?' + urllib.parse.urlencode({'query': q, 'market': 'en-AE'})
    return get_json(u)[1]


def keywords():
    result, errors = {}, []
    for seed in seeds():
        found = {}
        for mod in MODIFIERS:
            q = f'{seed} {mod}'.strip()
            for engine, fn in (('google', google_suggest), ('bing', bing_suggest)):
                try:
                    for s in fn(q):
                        s = s.strip().lower()
                        e = found.setdefault(s, {'google': 0, 'bing': 0})
                        e[engine] += 1
                except Exception as err:
                    errors.append(f'{engine} "{q}": {err}')
                time.sleep(0.6)
        ranked = sorted(found.items(), key=lambda kv: (-(kv[1]['google'] > 0 and kv[1]['bing'] > 0),
                                                       -(kv[1]['google'] + kv[1]['bing']), kv[0]))
        result[seed] = [{'q': k, **v} for k, v in ranked]
    save('keywords.json', {'date': TODAY, 'market': 'UAE / English', 'seeds': result, 'errors': errors[:50]})
    lines = [f'# Keyword ideas ({TODAY})', '',
             'From Google and Bing autocomplete (UAE, English). "G/B" = how many modifier searches '
             'showed the suggestion in Google / Bing. Suggestions in both engines are the strongest signals. '
             'Autocomplete shows what people type, not exact search volumes.', '']
    for seed, rows in result.items():
        lines.append(f'## {seed}')
        for r in rows[:15]:
            lines.append(f"- {r['q']}  (G{r['google']}/B{r['bing']})")
        lines.append('')
    if errors:
        lines += ['## Errors', *[f'- {e}' for e in errors[:20]]]
    open(os.path.join(OUT, 'keywords.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    return f'keywords: {len(result)} seeds, {sum(len(v) for v in result.values())} ideas, {len(errors)} errors'


# ---------- 2. Google Search Console ----------
def gsc():
    raw = os.environ.get('GSC_SA_JSON', '').strip()
    if not raw:
        return 'gsc: skipped (GSC_SA_JSON secret not set)'
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    creds = service_account.Credentials.from_service_account_info(
        json.loads(raw), scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
    creds.refresh(Request())
    site = os.environ.get('GSC_SITE', SITE)
    api = ('https://searchconsole.googleapis.com/webmasters/v3/sites/'
           + urllib.parse.quote(site, safe='') + '/searchAnalytics/query')
    end = dt.date.today() - dt.timedelta(days=3)
    start = end - dt.timedelta(days=27)

    def query(dims, limit=1000):
        body = json.dumps({'startDate': start.isoformat(), 'endDate': end.isoformat(),
                           'dimensions': dims, 'rowLimit': limit}).encode()
        return get_json(api, {'Authorization': f'Bearer {creds.token}',
                              'Content-Type': 'application/json'}, body).get('rows', [])

    rows = query(['query', 'page'])
    pages = query(['page'])
    data = [{'query': r['keys'][0], 'page': r['keys'][1], 'clicks': r['clicks'],
             'impressions': r['impressions'], 'ctr': round(r['ctr'], 4),
             'position': round(r['position'], 1)} for r in rows]
    save('gsc-queries.json', {'date': TODAY, 'range': [start.isoformat(), end.isoformat()], 'rows': data})
    save('gsc-pages.json', [{'page': r['keys'][0], 'clicks': r['clicks'], 'impressions': r['impressions'],
                             'ctr': round(r['ctr'], 4), 'position': round(r['position'], 1)} for r in pages])
    wins = sorted([d for d in data if 4 <= d['position'] <= 20 and d['impressions'] >= 10],
                  key=lambda d: -d['impressions'])
    hist = os.path.join(OUT, 'gsc-history.csv')
    new = not os.path.exists(hist)
    with open(hist, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['date', 'query', 'page', 'clicks', 'impressions', 'ctr', 'position'])
        for d in sorted(data, key=lambda d: -d['impressions'])[:300]:
            w.writerow([TODAY, d['query'], d['page'], d['clicks'], d['impressions'], d['ctr'], d['position']])
    lines = [f'# Search Console ({start} to {end})', '',
             f"Total: {sum(d['clicks'] for d in data)} clicks, {sum(d['impressions'] for d in data)} impressions, "
             f'{len(data)} query/page rows.', '', '## Quick wins (position 4–20, 10+ impressions)',
             'Improve title/meta, add the query to the page (H2/FAQ) and add internal links.', '']
    lines += [f"- \"{d['query']}\" → {d['page']} — pos {d['position']}, {d['impressions']} impr, "
              f"CTR {d['ctr']:.1%}" for d in wins[:40]] or ['- none yet']
    lines += ['', '## Top queries', '']
    lines += [f"- \"{d['query']}\" → {d['page']} — {d['clicks']} clicks, {d['impressions']} impr, pos {d['position']}"
              for d in sorted(data, key=lambda d: -d['impressions'])[:40]] or ['- no data yet']
    open(os.path.join(OUT, 'gsc.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    return f'gsc: {len(data)} rows, {len(wins)} quick wins'


# ---------- 3. Bing Webmaster ----------
def bing():
    key = os.environ.get('BING_API_KEY', '').strip()
    if not key:
        return 'bing: skipped (BING_API_KEY secret not set)'
    base = 'https://ssl.bing.com/webmaster/api.svc/json/'
    out = {'date': TODAY}
    for name, params in (('GetQueryStats', {'siteUrl': SITE}), ('GetPageStats', {'siteUrl': SITE})):
        try:
            out[name] = get_json(base + name + '?' + urllib.parse.urlencode({**params, 'apikey': key})).get('d')
        except Exception as err:
            out[name] = f'error: {err}'
    save('bing.json', out)
    q = out.get('GetQueryStats')
    return f"bing: {len(q) if isinstance(q, list) else q} query rows"


# ---------- 4. PageSpeed ----------
def pagespeed():
    pages = ['', 'activities/dubai/burj-khalifa-at-the-top-tickets/', 'blog/dubai/3-days-in-dubai-itinerary/']
    res = {'date': TODAY, 'pages': {}}
    for p in pages:
        url = SITE + p
        try:
            key = os.environ.get('PAGESPEED_API_KEY', '').strip()
            d = get_json('https://www.googleapis.com/pagespeedonline/v5/runPagespeed?' + urllib.parse.urlencode(
                ([('key', key)] if key else []) + [('url', url), ('strategy', 'mobile'), ('category', 'performance'), ('category', 'seo'),
                 ('category', 'accessibility'), ('category', 'best-practices')]), timeout=120)
            lh = d['lighthouseResult']
            res['pages'][url] = {
                'scores': {k: round(v['score'] * 100) for k, v in lh['categories'].items()},
                'lcp': lh['audits']['largest-contentful-paint']['displayValue'],
                'cls': lh['audits']['cumulative-layout-shift']['displayValue'],
                'tbt': lh['audits']['total-blocking-time']['displayValue'],
                'top_fixes': [a['title'] for a in sorted(
                    (a for a in lh['audits'].values() if a.get('details', {}).get('type') == 'opportunity'
                     and (a.get('numericValue') or 0) > 100), key=lambda a: -(a.get('numericValue') or 0))][:5]}
        except Exception as err:
            res['pages'][url] = {'error': 'PageSpeed API: ' + str(err)[:200] + (
                '' if os.environ.get('PAGESPEED_API_KEY') else ' (add the free PAGESPEED_API_KEY secret)')}
    save('pagespeed.json', res)
    return 'pagespeed: ' + ', '.join(f"{u.replace(SITE, '/')}={v.get('scores', {}).get('performance', 'err')}"
                                     for u, v in res['pages'].items())


if __name__ == '__main__':
    summary = [f'# SEO data run {TODAY}', '']
    only = os.environ.get('SEO_DATA_ONLY', '')
    for fn in (keywords, gsc, bing, pagespeed):
        if only and fn.__name__ != only:
            continue
        try:
            summary.append('- ' + fn())
        except Exception as err:
            summary.append(f'- {fn.__name__}: FAILED {err}')
    text = '\n'.join(summary) + '\n'
    open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write(
        text + '\nFiles: keywords.md/json, gsc.md, gsc-queries.json, gsc-pages.json, gsc-history.csv, '
               'bing.json, pagespeed.json. Made by source/seo_data.py.\n')
    print(text)
