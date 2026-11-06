#!/usr/bin/env python3
"""
Finds freely licensed photos of the KWIKAR fleet models on Wikimedia Commons
(run by .github/workflows/fleet-photos.yml; the build container cannot reach Commons).

  python3 source/fleet_photos.py search OUTDIR   -> candidates/<car>/<n>.jpg + candidates.json
  python3 source/fleet_photos.py fetch OUTDIR    -> full-size copies of the picks in source/data/fleet-photos.json

Only files whose licence allows commercial use are kept (CC0, public domain, CC BY, CC BY-SA).
"""
import json, os, re, sys, time, urllib.parse, urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'KWIKAR-fleet-photos/1.0 (https://kwikar.com; contact via website)'}
HERE = os.path.dirname(os.path.abspath(__file__))
QUERIES = {
    'mercedes-e-class': ['Mercedes-Benz W214 black', 'Mercedes-Benz W214 schwarz', 'Mercedes-Benz W214 grey', 'Mercedes-Benz E 220 d W214'],
    'lexus-es-300h': ['Lexus ES 300h 2022 black', 'Lexus ES 300h facelift', 'Lexus ES XZ10 facelift black'],
    'bmw-530i': ['BMW G60 black', 'BMW G60 schwarz', 'BMW G60 520d', 'BMW i5 G60 black'],
    'byd-han-flagship': ['BYD Han EV black', 'BYD Han 2022', 'BYD Han DM-i'],
    'tesla-model-y': ['Tesla Model Y Juniper black', 'Tesla Model Y black', 'Tesla Model Y 2025'],
    'byd-song-flagship': ['BYD Song Plus black', 'BYD Seal U black', 'BYD Seal U DM-i', 'BYD Song Plus DM-i'],
    'exeed-vx-flagship': ['Exeed VX', 'Exeed VX black', 'Chery Exeed VX'],
    'bmw-7-series': ['BMW G70 black', 'BMW G70 schwarz', 'BMW i7 G70 black', 'BMW 740d G70'],
    'mercedes-s-class': ['Mercedes-Benz W223 black', 'Mercedes-Benz W223 schwarz', 'Mercedes-Benz S 580 W223', 'Mercedes-Benz W223 grey'],
    'mercedes-v-class': ['Mercedes-Benz V-Klasse 2024 schwarz', 'Mercedes-Benz W447 facelift 2024 black', 'Mercedes-Benz V 300 d 2024', 'Mercedes-Benz V-Class 2024'],
    'gmc-yukon-xl': ['GMC Yukon 2021 black', 'GMC Yukon Denali 2021 black', 'GMC Yukon XL 2021', 'GMC Yukon 2025'],
    'cadillac-escalade': ['Cadillac Escalade 2021 black', 'Cadillac Escalade fifth generation black', 'Cadillac Escalade 2023', 'Cadillac Escalade V'],
}
GOOD_LIC = re.compile(r'^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?)', re.I)
DARK = re.compile(r'black|schwarz|noir|nero|negro|grey|gray|grau|obsidian|graphite|anthracite|dark', re.I)
BAD = re.compile(r'interior|innen|cockpit|dashboard|engine|motor|rear|heck|back|seat|wheel|rim|logo|badge|emblem|detail|light', re.I)


def api(params):
    q = API + '?' + urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=40))
        except Exception as err:
            time.sleep(3 * (i + 1))
            last = err
    raise last


def strip(html):
    return re.sub(r'<[^>]+>', '', html or '').strip()


def info(titles, width):
    out = {}
    for i in range(0, len(titles), 40):
        d = api({'action': 'query', 'titles': '|'.join(titles[i:i + 40]), 'prop': 'imageinfo',
                 'iiprop': 'url|size|extmetadata|mime', 'iiurlwidth': width})
        for p in d['query']['pages']:
            ii = (p.get('imageinfo') or [{}])[0]
            md = ii.get('extmetadata', {})
            out[p['title']] = {'title': p['title'], 'thumb': ii.get('thumburl'), 'url': ii.get('url'), 'w': ii.get('width'), 'h': ii.get('height'),
                               'mime': ii.get('mime'), 'license': strip(md.get('LicenseShortName', {}).get('value')),
                               'license_url': strip(md.get('LicenseUrl', {}).get('value')),
                               'artist': strip(md.get('Artist', {}).get('value')), 'desc': strip(md.get('ImageDescription', {}).get('value'))[:300],
                               'page': p.get('fullurl') or 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(p['title'].replace(' ', '_'))}
        time.sleep(1)
    return out


def download(url, dest):
    for i in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            open(dest, 'wb').write(data)
            return True
        except Exception:
            time.sleep(4 * (i + 1))
    return False


def search(out):
    allc = {}
    for car, qs in QUERIES.items():
        seen = []
        for q in qs:
            d = api({'action': 'query', 'list': 'search', 'srsearch': q + ' filetype:bitmap', 'srnamespace': 6, 'srlimit': 30})
            seen += [r['title'] for r in d['query']['search'] if r['title'] not in seen]
            time.sleep(1)
        meta = info(seen, 900)
        cands = []
        for t in seen:
            m = meta.get(t)
            if not m or m['mime'] != 'image/jpeg' or (m['w'] or 0) < 1400 or not GOOD_LIC.match(m['license'] or ''):
                continue
            if BAD.search(t):
                continue
            m['score'] = (3 if DARK.search(t + ' ' + m['desc']) else 0) + (1 if (m['w'] or 0) >= 2500 else 0) + (1 if re.search(r'front|vorne|IMG_', t, re.I) else 0)
            cands.append(m)
        cands.sort(key=lambda m: -m['score'])
        cands = cands[:12]
        os.makedirs(os.path.join(out, car), exist_ok=True)
        for i, m in enumerate(cands):
            m['file'] = f'{car}/{i:02d}.jpg'
            download(m['thumb'], os.path.join(out, m['file']))
            time.sleep(0.5)
        allc[car] = cands
        print(car, len(seen), 'found,', len(cands), 'kept')
    json.dump(allc, open(os.path.join(out, 'candidates.json'), 'w'), indent=1, ensure_ascii=False)


def fetch(out):
    picks = json.load(open(os.path.join(HERE, 'data', 'fleet-photos.json'), encoding='utf-8'))
    meta = info([p['title'] for p in picks.values()], 2400)
    os.makedirs(out, exist_ok=True)
    credits = {}
    for car, p in picks.items():
        m = meta[p['title']]
        ok = download(m['thumb'] or m['url'], os.path.join(out, car + '.jpg'))
        credits[car] = {k: m[k] for k in ('title', 'artist', 'license', 'license_url', 'page')}
        print(car, 'ok' if ok else 'FAILED')
        time.sleep(1)
    json.dump(credits, open(os.path.join(out, 'credits.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    {'search': search, 'fetch': fetch}[sys.argv[1]](sys.argv[2])
