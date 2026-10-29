"""
Live tours for the static build.

Reads the KWIKAR tours API (the same /api/tours.php the site uses, which
fetches from TravelDesk) so tour pages and listing cards are written into the
HTML itself. Search engines and AI tools can read them without JavaScript.

Nothing about tours is invented here: names, prices, options, photos, FAQs and
terms all come from the API. Blocks without data are left out.
"""
import json, os, re, time, urllib.request, html, concurrent.futures
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
API = os.environ.get('KWIKAR_API', 'https://kwikar.com/api/tours.php')
SLUG_FILE = os.path.join(ROOT, 'data', 'tour-slugs.json')


def e(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def _get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'KwikarBuild/1.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode('utf-8'))
            if data.get('ok'):
                return data
            last = RuntimeError(data.get('error') or 'not ok')
        except Exception as ex:  # network / SSL hiccups: retry
            last = ex
        time.sleep(2 + i * 3)
    raise RuntimeError(f'Could not load {url}: {last}')


def load_feed(with_details=True):
    """Returns (items, details_by_id, updated_iso). Raises if the API is unavailable."""
    lst = _get(API)
    updated = lst.get('updated') or ''
    if lst.get('stale'):
        raise RuntimeError('Tours feed is serving saved (stale) data — not building from it.')
    items = [t for t in lst.get('items', []) if t.get('id') and t.get('name') and t.get('loc')]
    details = {}
    if with_details:
        def one(t):
            try:
                return t['id'], _get(f"{API}?id={t['id']}", tries=3)
            except Exception:
                return t['id'], None
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            for tid, d in ex.map(one, items):
                if d:
                    details[tid] = d
    return items, details, updated


# ---------------------------------------------------------------- slugs / URLs
def slugify(name):
    s = name.lower()
    s = re.sub(r'&', ' and ', s)
    s = re.sub(r"[’'`]", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:80].rstrip('-') or 'experience'


def city_of(loc):
    return 'uae' if loc in (None, '', 'other') else loc


def assign_slugs(items):
    """Stable slugs: once a tour has a URL it keeps it (stored in data/tour-slugs.json)."""
    try:
        saved = json.load(open(SLUG_FILE, encoding='utf-8'))
    except Exception:
        saved = {}
    used = {v for v in saved.values()}
    for t in items:
        key = str(t['id'])
        if key in saved:
            continue
        path = f"/activities/{city_of(t['loc'])}/{slugify(t['name'])}"
        if path in used:
            path = f'{path}-{t["id"]}'
        saved[key] = path
        used.add(path)
    json.dump(saved, open(SLUG_FILE, 'w', encoding='utf-8'), indent=1, sort_keys=True)
    return saved


# ---------------------------------------------------------------- rules shared with tours.js
def matches_category(t, slug, term):
    name = t['name'].lower()
    if re.search(r'russian.speaking guide', name):
        return False
    tags = ' '.join(t.get('cats') or []).lower()
    if slug == 'yachts':
        return 'yacht' in name or 'yacht' in tags
    if slug == 'cruises':
        return 'yacht' not in name and bool(re.search(r'cruise|dhow', name))
    if slug == 'events':
        return bool(re.search(r'event|concert|festival|performance|live show', name)) or any(re.match(r'^events?$', c.strip(), re.I) for c in (t.get('cats') or []))
    return not term or any(w in f'{name} {tags}' for w in term.lower().split('|'))


def visible(t):
    return not re.search(r'russian.speaking guide', t['name'], re.I)


def popular(items):
    return sorted(items, key=lambda t: -(t.get('reviews') or 0))


def money(n):
    n = float(n)
    return f'AED {n:,.0f}' if n.is_integer() else f'AED {n:,.2f}'.rstrip('0').rstrip('.')


def price_html(t):
    if t.get('price'):
        unit = f' / {e(t["unit"])}' if t.get('unit') else ''
        return f'From <strong>{money(t["price"])}</strong>{unit}'
    return 'Price on request'


def card(t, place_name, href, short=False):
    """Same markup as KW.tourCard in tours.js (no supplier ratings)."""
    cats = t.get('cats') or []
    cat = ''
    if cats and not short:
        desert = next((c for c in cats if re.search('desert', c, re.I) and re.search('desert', t['name'], re.I)), None)
        cat = ' · ' + (desert or cats[0])
    img = t.get('img') or '/assets/img/hero-dubai-mobile.webp'
    return (f'<article class="exp-card"><a href="{e(href)}" class="media tall" aria-label="{e(t["name"])}">'
            f'<img src="{e(img)}" alt="{e(t["name"])}" loading="lazy" width="400" height="453"></a>'
            f'<p class="tag">{e(place_name)}{e(cat)}</p><h3><a href="{e(href)}">{e(t["name"])}</a></h3>'
            f'<p class="price">{price_html(t)}</p><a href="{e(href)}" class="link">View experience →</a></article>')
