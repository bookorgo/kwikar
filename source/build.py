#!/usr/bin/env python3
"""
KWIKAR static site generator.

Design: the same markup (kw-* classes) and stylesheet as the previous KWIKAR
site, so pages look the same. SEO: every tour, listing and hub is written into
the HTML from the live tours API, with clean URLs, schema and sitemaps.

Run:  python3 build.py                  (reads https://kwikar.com/api/tours.php)
      python3 build.py --feed FILE.json  (use a saved feed, for offline testing)

Holidays, cars, visas and destinations live in data/catalog.json.
"""
import json, html, os, re, sys, datetime, hashlib, shutil
from urllib.parse import quote
import tours_feed as tf

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, '..', 'public_html'))
SITE = 'https://kwikar.com'
PHONE = '971505599243'
PHONE_FMT = '+971 50 559 9243'
EMAIL = 'info@kwikar.com'

CONFIG = {}
try:
    CONFIG = json.load(open(os.path.join(ROOT, 'data', 'site-config.json'), encoding='utf-8'))
except Exception:
    pass
GA4_ID = (CONFIG.get('ga4_id') or '').strip()
GOOGLE_VERIFY = (CONFIG.get('google_site_verification') or '').strip()
BING_VERIFY = (CONFIG.get('bing_site_verification') or '').strip()
SOCIAL = [s for s in CONFIG.get('social_profiles', []) if isinstance(s, str) and s.startswith('https://')]

cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
LOCATIONS = cat['locations']                       # includes 'other' (shown as "More")
REAL_LOCATIONS = [l for l in LOCATIONS if l['id'] != 'other']
HOLIDAYS, CARS, VISAS = cat['holidays'], cat['cars'], cat['visas']
TR = json.load(open(os.path.join(ROOT, 'data', 'transfers.json'), encoding='utf-8'))
for _c in CARS:   # uniform fleet photo (assets/img/fleet) first, then the local copy made by fetch_images.py
    _slug = re.sub(r'[^a-z0-9]+', '-', _c['name'].lower()).strip('-')
    for _local in ('assets/img/fleet/' + _slug + '.webp', 'assets/img/cars/' + _slug + '.webp'):
        if os.path.exists(os.path.join(OUT, _local)):   # ?v= busts the 6-month image cache when a photo changes
            _c['img'] = '/' + _local + '?v=' + hashlib.md5(open(os.path.join(OUT, _local), 'rb').read()).hexdigest()[:8]
            break
CAT_DESC = {   # meta descriptions for category hubs (120–160 chars)
    'city-tours': 'City tours of Dubai, Abu Dhabi, Ras Al Khaimah and Fujairah, with guided day tours and private options. Compare current prices and ask us on WhatsApp.',
    'theme-parks': 'Theme park tickets for Dubai and Abu Dhabi, including Yas Island parks and waterparks. Compare current prices and send your request on WhatsApp.',
    'desert-adventures': 'Desert safaris from Dubai, Abu Dhabi and Ras Al Khaimah: morning, evening, overnight and heritage safaris. Compare options and current prices on KWIKAR.',
    'water-activities': 'Water activities in Dubai and the UAE: waterparks, speed boat tours, dolphin experiences, fishing trips and cruises. Compare current prices on KWIKAR.',
    'cultural-experiences': 'Museums, palaces and cultural experiences in Dubai and Abu Dhabi, including Louvre Abu Dhabi and Qasr Al Watan. Compare current prices and ask us on WhatsApp.',
    'family-activities': 'Family activities in Dubai and the UAE for all ages, from aquariums to theme parks. Compare current prices and send your request on WhatsApp.',
    'luxury-experiences': 'Luxury experiences in Dubai and the UAE, including yacht tours. Compare options and current prices, then send your request to our team on WhatsApp.',
    'attraction-tickets': 'Attraction tickets for Dubai, Abu Dhabi and the UAE. Compare ticket options and current prices, then send your request to our team on WhatsApp.',
    'cruises': 'Dhow cruises and dinner cruises in Dubai, from Dubai Marina to the Dubai Water Canal. Compare cruises and current prices, then send your request on WhatsApp.',
    'yachts': 'Shared and private yacht tours in Dubai. Compare yachts, what each trip includes and current prices, then send your request to our team on WhatsApp.',
    'events': 'Events, concerts and live shows in Dubai and the UAE. Compare dates, tickets and current prices, then send your request to our team on WhatsApp.',
}
CATEGORIES = [
    {'slug': 'city-tours', 'name': 'City tours', 'term': 'city tour'},
    {'slug': 'theme-parks', 'name': 'Theme parks', 'term': 'theme park'},
    {'slug': 'desert-adventures', 'name': 'Desert adventures', 'term': 'desert'},
    {'slug': 'water-activities', 'name': 'Water activities', 'term': 'water'},
    {'slug': 'cultural-experiences', 'name': 'Cultural experiences', 'term': 'museum'},
    {'slug': 'family-activities', 'name': 'Family activities', 'term': 'family'},
    {'slug': 'luxury-experiences', 'name': 'Luxury experiences', 'term': 'luxury'},
    {'slug': 'attraction-tickets', 'name': 'Attraction tickets', 'term': 'ticket'},
    {'slug': 'cruises', 'name': 'Cruises', 'term': 'cruise|dhow|boat'},
    {'slug': 'yachts', 'name': 'Yachts', 'term': 'yacht'},
    {'slug': 'events', 'name': 'Events', 'term': 'event|concert|festival|performance|live show'},
]


# ================================================================= live tours
def _load_tours():
    if '--feed' in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index('--feed') + 1], encoding='utf-8'))
        return data['items'], {int(k): v for k, v in data['details'].items()}, data.get('updated', '')
    return tf.load_feed()


ALL_TOURS, DETAILS, FEED_UPDATED = _load_tours()
if '--save-feed' in sys.argv:   # the GitHub Action keeps a copy so scheduled SEO runs can build offline
    json.dump({'items': ALL_TOURS, 'details': {str(k): v for k, v in DETAILS.items()}, 'updated': FEED_UPDATED},
              open(sys.argv[sys.argv.index('--save-feed') + 1], 'w', encoding='utf-8'), ensure_ascii=False)
TOURS = tf.popular([t for t in ALL_TOURS if tf.visible(t)])      # what listings show (most reviewed first)
if len(TOURS) < 10:
    raise SystemExit(f'Only {len(TOURS)} tours loaded — refusing to build a site without tours.')
SLUGS = tf.assign_slugs(ALL_TOURS)                                 # id -> /activities/{city}/{slug}
LIVE_IDS = {str(t['id']) for t in ALL_TOURS}
LIVE_LOCS = {t['loc'] for t in TOURS}
CAT_COUNT = {c['slug']: sum(1 for t in TOURS if tf.matches_category(t, c['slug'], c['term'])) for c in CATEGORIES}
LIVE_CATS = [c for c in CATEGORIES if CAT_COUNT[c['slug']]]
try:
    EXTRAS = {k: v for k, v in json.load(open(os.path.join(ROOT, 'data', 'tour-extras.json'), encoding='utf-8')).items() if not k.startswith('_')}
except Exception:
    EXTRAS = {}

ADDON_RE = re.compile(r'\badd[\s-]?on\b|addon', re.I)


def _clean_name(s):
    if not isinstance(s, str):
        return s
    s = re.sub(r'\b(tour|trip|transfer|cruise|safari) form\b', r'\1 from', s, flags=re.I)   # supplier typo "City Tour form Abu Dhabi"
    return re.sub(r'\s{2,}', ' ', s).strip()


def from_offers(tid, offers):
    """Offers that may set the "From" price: fast-track add-ons need a separate entry ticket, so they are
    left out (also any offer id in tour-extras `from_exclude`). With `from_price: "child"` the child rate is used."""
    x = EXTRAS.get(str(tid), {})
    skip = {str(i) for i in x.get('from_exclude', [])}
    priced = [o for o in offers if o.get('price')]
    keep = [o for o in priced if str(o.get('id')) not in skip and not ADDON_RE.search(o.get('name') or '')]
    keep = keep or priced
    if x.get('from_price') == 'child':
        keep = [dict(o, price=o['child'], unit='child') for o in keep if o.get('child')] or keep
    return keep


for _t in ALL_TOURS:   # listing price + tidy supplier names (slugs are already fixed, so URLs do not change)
    _d = DETAILS.get(_t['id']) or DETAILS.get(str(_t['id'])) or {}
    _t['name'] = _clean_name(_t['name'])
    if _d.get('name'):
        _d['name'] = _clean_name(_d['name'])
    for _o in _d.get('offers') or []:
        _o['name'] = _clean_name(_o.get('name'))
    _fo = from_offers(_t['id'], _d.get('offers') or [])
    if _fo:
        _c = min(_fo, key=lambda o: o['price'])
        _t['price'], _t['unit'] = _c['price'], _c.get('unit') or _t.get('unit')
try:
    CHECKED = datetime.datetime.fromisoformat(FEED_UPDATED.replace('Z', '+00:00')).strftime('%-d %b %Y')
except Exception:
    CHECKED = datetime.date.today().strftime('%-d %b %Y')
TODAY = datetime.date.today().isoformat()

# A hand-written slug in tour-extras.json renames the page; the old address keeps working (301).
_REDIR_FILE = os.path.join(ROOT, 'data', 'slug-redirects.json')
try:
    SLUG_REDIRECTS = json.load(open(_REDIR_FILE, encoding='utf-8'))
except Exception:
    SLUG_REDIRECTS = {}
_slugs_changed = False
for _tid, _x in EXTRAS.items():
    if _x.get('slug') and _tid in SLUGS:
        _new = SLUGS[_tid].rsplit('/', 1)[0] + '/' + _x['slug']
        if SLUGS[_tid] != _new:
            SLUG_REDIRECTS[SLUGS[_tid]] = _new
            SLUGS[_tid] = _new
            _slugs_changed = True
SLUG_REDIRECTS = {o: n for o, n in SLUG_REDIRECTS.items() if o not in SLUGS.values()}
if _slugs_changed:
    json.dump(SLUGS, open(tf.SLUG_FILE, 'w', encoding='utf-8'), indent=1, sort_keys=True)
json.dump(SLUG_REDIRECTS, open(_REDIR_FILE, 'w', encoding='utf-8'), indent=1, sort_keys=True)


def e(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def wa(msg):
    return f'https://wa.me/{PHONE}?text={quote(msg)}'


def money(n):
    n = float(n)
    return f'AED {n:,.0f}' if n.is_integer() else f'AED {n:,.2f}'  # 52.5 -> AED 52.50 (same as kw.js)


def loc(id_):
    return next((l for l in LOCATIONS if l['id'] == id_), None)


def loc_name(loc_id):
    """Name shown on cards and pages; 'other' tours are UAE-wide ("More")."""
    l = loc(loc_id)
    return l['name'] if l else 'More'


def tour_href(t):
    return SLUGS.get(str(t['id'])) or f"/tour/{t['id']}"


def dest_href(loc_id):
    return f'/destinations/{loc_id or "other"}'


def city_title(loc_id):
    return 'More UAE experiences' if loc_id == 'other' else f'Things to do in {loc_name(loc_id)}'


def U(pid, w=900):
    """Unsplash photos used by the previous site, stored locally in assets/img/u."""
    return f'/assets/img/u/{pid}{"-lg" if w >= 1200 else ""}.webp'


def photo(pid, w=800):
    return U(pid, w)


UNSPLASH = re.compile(r'https://images\.unsplash\.com/photo-([0-9a-f-]+)\?[^"\'\s)]*')


def localize(text):
    def rep(m):
        lg = re.search(r'[?&]w=(\d+)', m.group(0))
        return U(m.group(1), int(lg.group(1)) if lg else 800)
    return UNSPLASH.sub(rep, text)


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def crumbs_ld(crumbs):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]}


ORG = {'@type': 'TravelAgency', '@id': SITE + '/#organization', 'name': 'KWIKAR', 'legalName': 'Kwikar LLC-FZ', 'url': SITE + '/',
       'logo': SITE + '/assets/img/logo.webp', 'image': SITE + '/assets/img/kwikar-share.webp', 'telephone': '+' + PHONE,
       'email': EMAIL, 'address': {'@type': 'PostalAddress', 'addressCountry': 'AE'}, 'areaServed': {'@type': 'Country', 'name': 'United Arab Emirates'},
       'description': 'UAE travel company for tours and activities, holiday packages, private chauffeur transfers and UAE tourist visa assistance.',
       'contactPoint': {'@type': 'ContactPoint', 'telephone': '+' + PHONE, 'contactType': 'customer service', 'availableLanguage': 'English'}}
if SOCIAL:
    ORG['sameAs'] = SOCIAL
ORG_LD = {'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': SITE + '/#website', 'url': SITE + '/', 'name': 'KWIKAR',
                                                             'publisher': {'@id': SITE + '/#organization'}}]}


# ================================================================= icons (lucide, as on the previous site)
LUCIDE = {
    'flag': '<path d="M7 22V2l10 5-10 5"/>',
    'mountain': '<path d="m8 3 4 8 5-5 5 15H2L8 3z"/>',
    'plane': '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    'file': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    'ship': '<path d="M12 10.189V14"/><path d="M12 2v3"/><path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/><path d="M19.38 20A11.6 11.6 0 0 0 21 14l-8.188-3.639a2 2 0 0 0-1.624 0L3 14a11.6 11.6 0 0 0 2.81 7.76"/><path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
    'car': '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"/><path d="M7 14h.01"/><path d="M17 14h.01"/><rect width="18" height="8" x="3" y="10" rx="2"/><path d="M5 18v2"/><path d="M19 18v2"/>',
    'taxi': '<path d="M10 2h4"/><path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"/><path d="M7 14h.01"/><path d="M17 14h.01"/><rect width="18" height="8" x="3" y="10" rx="2"/><path d="M5 18v2"/><path d="M19 18v2"/>',
    'chevron-down': '<path d="m6 9 6 6 6-6"/>',
    'chevron-right': '<path d="m9 18 6-6-6-6"/>',
    'message': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'search': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'menu': '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    'map-pin': '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    'ferris': '<circle cx="12" cy="12" r="2"/><path d="M12 2v4"/><path d="m6.8 15-3.5 2"/><path d="m20.7 7-3.5 2"/><path d="M6.8 9 3.3 7"/><path d="m20.7 17-3.5-2"/><path d="m9 22 3-8 3 8"/><path d="M8 22h8"/><path d="M18 18.7a9 9 0 1 0-12 0"/>',
    'luggage': '<path d="M6 20a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2"/><path d="M8 18V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v14"/><path d="M10 20h4"/><circle cx="16" cy="20" r="2"/><circle cx="8" cy="20" r="2"/>',
    'book-user': '<path d="M15 13a3 3 0 1 0-6 0"/><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><circle cx="12" cy="8" r="2"/>',
    'panels': '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
    'calendar': '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>',
    'house': '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'ticket': '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
}


def svg(name, size=24, sw=2, cls='', style='', fill='none'):
    c = f' class="lucide {cls}"' if cls else ' class="lucide"'
    st = f' style="{style}"' if style else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"{c}{st} aria-hidden="true">{LUCIDE[name]}</svg>')


# ================================================================= header, menus, footer
NAV = [('Destinations', 'flag', '#ff6a21', '/destinations'), ('Activities', 'mountain', '#08b9bb', '/activities'),
       ('Holidays', 'plane', '#5969e9', '/holidays'), ('Visas', 'file', '#ff9516', '/visa'),
       ('Cruises', 'ship', '#406bf2', '/activities/cruises'), ('Transfers', 'car', '#2aba87', '/transfers')]
MENU_ITEMS = {
    'Activities': [('Explore activities', [('City tours', '/activities/city-tours'), ('Desert adventures', '/activities/desert-adventures'), ('Theme parks', '/activities/theme-parks'), ('Water activities', '/activities/water-activities')]),
                   ('Popular choices', [('Burj Khalifa', '/search?q=Burj%20Khalifa'), ('Dubai safari', '/search?q=desert%20safari'), ('Abu Dhabi tours', '/destinations/abu-dhabi')])],
    'Holidays': [('Holiday destinations', [(c, f'/holidays?country={quote(c)}') for c in dict.fromkeys(h['country'] for h in HOLIDAYS)]),
                 ('Plan your trip', [('All holiday packages', '/holidays'), ('Request a tailored holiday', '/contact')])],
    'Visas': [('UAE visa options', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' in v['name']]),
              ('Other visa assistance', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' not in v['name']])],
    'Cruises': [('Cruise experiences', [('All cruises', '/activities/cruises'), ('Dubai Marina cruises', '/search?q=marina%20cruise'), ('Dhow cruises', '/search?q=dhow%20cruise'), ('Dinner cruises', '/search?q=dinner%20cruise')])],
    'Transfers': [('Airport transfers', [(a['short'] + ' (' + a['code'] + ')', '/transfers/' + a['slug']) for a in TR['airports']]),
                  ('Popular routes', [(r['to'] + ' from ' + r['airport'], '/transfers/' + r['slug']) for r in TR['routes'] if r['id'] in ('dxb-downtown', 'dxb-marina', 'dxb-palm', 'dxb-abudhabi')]
                   + [('Dubai to Abu Dhabi', '/transfers/dubai-to-abu-dhabi'), ('Chauffeur by the hour', '/transfers/' + TR['hourly']['slug'])]),
                  ('Vehicle classes', [(c['name'], '/transfers/vehicles/' + c['slug']) for c in TR['classes']] + [('Our full fleet', '/transfers/fleet')])],
}
MENU_CITIES = ['dubai', 'abu-dhabi', 'sharjah', 'ras-al-khaimah', 'singapore', 'bali', 'thailand', 'malaysia']
EXPERIENCE_TERMS = [('City Tours', 'city tour'), ('Theme Parks', 'theme park'), ('Desert Adventures', 'desert'), ('Water Activities', 'water'),
                    ('Cultural Experiences', 'museum'), ('Family Activities', 'family'), ('Luxury Experiences', 'luxury'), ('Attraction Tickets', 'ticket')]


def mega_panel(label):
    chev = svg('chevron-right', 16)
    if label == 'Destinations':
        cities = [loc(i) for i in MENU_CITIES if loc(i) and i in LIVE_LOCS]

        def dest(l):
            return (f'<a class="kw-mega-destination" href="{dest_href(l["id"])}"><img src="{e(l.get("img") or "/assets/img/hero-dubai.webp")}" alt="" loading="lazy">'
                    f'<span><strong>{e(l["name"])}</strong><small>{"United Arab Emirates" if l["group"] == "uae" else "International experiences"}</small></span>{chev}</a>')
        uae = ''.join(dest(l) for l in cities if l['group'] == 'uae') or '<p class="kw-mega-empty">Explore UAE experiences</p>'
        intl = ''.join(dest(l) for l in cities if l['group'] != 'uae') or '<p class="kw-mega-empty">Ask about worldwide experiences</p>'
        exp = ''.join(f'<a href="/search?q={quote(q)}">{e(n)}{chev}</a>' for n, q in EXPERIENCE_TERMS)
        inner = (f'<div class="kw-mega-column"><h2>UAE Destinations</h2>{uae}</div><div class="kw-mega-column"><h2>International Destinations</h2>{intl}</div>'
                 f'<div class="kw-mega-column kw-mega-experiences"><h2>Experiences</h2>{exp}</div>'
                 '<a href="/destinations/dubai" class="kw-mega-feature"><span>ICONIC · MODERN · UNFORGETTABLE</span><strong>Explore Dubai</strong>'
                 '<p>Landmarks, desert adventures and memorable days in the city.</p><em>Explore Dubai&nbsp; →</em></a>')
        return f'<div class="kw-mega-menu" data-menu="{label}" hidden>{inner}</div>'
    href = dict((n, h) for n, _, _, h in NAV)[label]
    groups = ''.join(f'<div class="kw-menu-list"><h3>{e(t)}</h3>' + ''.join(f'<a href="{e(h)}">{e(n)}{svg("chevron-right", 15)}</a>' for n, h in items) + '</div>'
                     for t, items in MENU_ITEMS[label])
    return (f'<div class="kw-mega-menu kw-menu-panel" data-menu="{label}" hidden><div class="kw-menu-content"><div class="kw-menu-intro"><span>EXPLORE KWIKAR</span>'
            f'<h2>{label}</h2><p>Find your next experience or tell us what you have in mind.</p><a href="{href}">View all {label.lower()} →</a></div>{groups}</div>'
            '<div class="kw-menu-help"><strong>Need help planning?</strong><p>Share your dates and interests. Our team will confirm options and prices.</p>'
            '<a href="/contact">Contact KWIKAR →</a></div></div>')


ICON3D = {'Destinations': 'destinations', 'Activities': 'activities', 'Holidays': 'holidays', 'Visas': 'visas', 'Cruises': 'cruises',
          'Transfers': 'transfers', 'Events': 'events', 'More': 'more'}


def icon3d(label, size, cls=''):
    f = 'assets/img/icons/' + ICON3D[label] + '.svg'
    v = hashlib.md5(open(os.path.join(OUT, f), 'rb').read()).hexdigest()[:8] if os.path.exists(os.path.join(OUT, f)) else '1'
    return f'<img class="kw-icon3d {cls}" src="/{f}?v={v}" width="{size}" height="{size}" alt="" aria-hidden="true">'


def header(active):
    groups = ''.join(
        f'<div class="kw-nav-group{" active" if label == active else ""}" data-group="{label}"><a class="kw-nav-attractions" href="{href}">'
        f'{icon3d(label, 24, "kw-nav-icon")}{label}</a><button type="button" class="kw-nav-toggle" aria-label="Open {label} menu" '
        f'aria-expanded="false" aria-controls="kw-navigation-menu">{svg("chevron-down", 14)}</button></div>'
        for label, icon, color, href in NAV)
    panels = ''.join(mega_panel(label) for label, _, _, _ in NAV)
    return f'''<header class="kw-header kw-header-vb">
<div class="kw-header-toprow"><div class="kw-header-shell"><a href="/" class="kw-brand-logo" aria-label="KWIKAR homepage"><img src="/assets/img/logo.webp" alt="KWIKAR — Fast service that matters" width="1087" height="370"></a><div class="kw-header-contact"><a href="tel:+{PHONE}" aria-label="Call KWIKAR on {PHONE_FMT}">{svg("phone", 21)}<span><small>Call us</small><strong>{PHONE_FMT}</strong></span></a><a href="{e(wa("Hi KWIKAR, I have an enquiry."))}" target="_blank" rel="noopener noreferrer" aria-label="Chat with KWIKAR on WhatsApp">{svg("message", 23)}<span><small>WhatsApp</small><strong>Chat with our team</strong></span></a></div><button class="kw-mobile-menu" type="button" aria-label="Open menu" aria-expanded="false"><span class="kw-ico-open">{svg("menu", 25)}</span><span class="kw-ico-close" hidden>{svg("x", 25)}</span></button></div></div>
<div class="kw-header-navrow"><div class="kw-header-shell kw-navigation"><nav class="kw-main-nav" aria-label="Main navigation"><form class="kw-mobile-nav-search" action="/search" method="get" role="search"><label for="kw-mobile-query">Search experiences</label><div><input id="kw-mobile-query" type="search" name="q" placeholder="Tour, city or activity"><button type="submit" aria-label="Search experiences">{svg("search", 19)}</button></div></form>{groups}</nav><form class="kw-header-search-vb" role="search" action="/search" method="get">{svg("search", 19)}<input name="q" aria-label="Search destinations or activities" placeholder="Search destinations, attractions, experiences..."><button type="submit" aria-label="Search">{svg("search", 18)}</button></form></div></div>
<div id="kw-navigation-menu">{panels}</div>
</header>'''


def mobile_nav(path):
    primary = [('Activities', '/activities', 'ferris'), ('Holidays', '/holidays', 'luggage'), ('Transfers', '/transfers', 'taxi'), ('Visas', '/visa', 'book-user')]
    extra = [('Destinations', '/destinations', 'flag'), ('Cruises', '/activities/cruises', 'ship')]
    if CAT_COUNT.get('events'):
        extra.append(('Events', '/activities/events', 'calendar'))
    bottom = [('Home', '/', 'house'), ('Activities', '/activities', 'ticket'), ('Search', '/search', 'search'), ('Help', '/contact', 'message')]

    def sel(h):
        return path == h or path.startswith(h + '/')
    extra_active = any(sel(h) for _, h, _ in extra) or path.startswith('/destinations/')
    tour = path.startswith('/activities/') and path.count('/') >= 3
    prim = ''.join(f'<a href="{h}"{" class=kw-selected aria-current=page" if sel(h) and not extra_active else ""}><span class="kw-service-icon">{icon3d(t, 30)}</span>{t}</a>' for t, h, i in primary)
    more = ''.join(f'<a href="{h}"{" aria-current=page" if sel(h) else ""}>{icon3d(t, 22)}{t}<span aria-hidden="true">→</span></a>' for t, h, i in extra)
    app = '' if tour else ('<nav class="kw-app-bottom-nav" aria-label="Mobile app navigation">' + ''.join(
        f'<a href="{h}"{" aria-current=page" if path == h else ""}>{svg(i, 25, 2.6 if path == h else 1.8, fill="currentColor" if (path == h and t == "Home") else "none")}<span>{t}</span></a>'
        for t, h, i in bottom) + '</nav>')
    return (f'<div class="kw-mobile-shortcut-area{"" if not tour else " kw-tour-mobile-navigation"}"><nav class="kw-mobile-shortcuts" aria-label="Travel services">{prim}'
            f'<details class="kw-mobile-extra{" kw-selected" if extra_active else ""}"><summary><span class="kw-service-icon">{icon3d("More", 28)}</span>More</summary>'
            f'<nav class="kw-mobile-more" aria-label="More travel services">{more}</nav></details></nav></div>{app}')


FOOTER_LINKS = [('/destinations', 'Destinations'), ('/activities', 'Activities'), ('/destinations/dubai', 'Dubai'), ('/holidays', 'Holidays'),
                ('/transfers', 'Transfers'), ('/visa', 'Visa'), ('/blog', 'Travel guides'), ('/contact', 'Contact'), ('/about', 'About'), ('/privacy', 'Privacy policy'),
                ('/terms', 'Terms & conditions'), ('/booking-information', 'Booking information'), ('/refund-policy', 'Refund & cancellation')]


TRUSTPILOT_WIDGET = (
    '<div class="kw-wrap kw-trustpilot"><p class="kw-trustpilot-head">Travelled with us? Leave a review</p>'
    '<div class="kw-trustpilot-box">'
    '<!-- TrustBox widget - Review Collector -->\n'
    '<div class="trustpilot-widget" data-locale="en-US" data-template-id="56278e9abfbbba0bdcd568bc" '
    'data-businessunit-id="6aec232d6c0eb68ba5bb8064" data-style-height="52px" data-style-width="100%">\n'
    '  <a href="https://www.trustpilot.com/review/kwikar.com" target="_blank" rel="noopener">Trustpilot</a>\n'
    '</div>\n<!-- End TrustBox widget -->'
    '</div></div>')
TRUSTPILOT_SCRIPT = ('<!-- TrustBox script -->\n'
    '<script type="text/javascript" src="//widget.trustpilot.com/bootstrap/v5/tp.widget.bootstrap.min.js" async></script>\n'
    '<!-- End TrustBox script -->')


def footer():
    links = ''.join(f'<a href="{h}">{e(t)}</a>' for h, t in FOOTER_LINKS)
    return (f'<footer class="kw-footer"><div class="kw-wrap kw-footer-grid"><div><a class="kw-logo kw-logo-footer" href="/"><img src="/assets/img/logo-white.webp" alt="KWIKAR" loading="lazy"></a>'
            f'<p>Travel experiences, holidays, transfers and visa assistance across the UAE and beyond.</p></div><div><strong>Explore</strong>{links}</div>'
            f'<div><strong>Contact</strong><a href="tel:+{PHONE}">{PHONE_FMT}</a><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{e(wa("Hi KWIKAR, I have an enquiry."))}" target="_blank" rel="noopener noreferrer">WhatsApp us</a></div></div>'
            f'{TRUSTPILOT_WIDGET}<div class="kw-wrap kw-footer-bottom">© <span data-year>{datetime.date.today().year}</span> Kwikar LLC-FZ · United Arab Emirates · {PHONE_FMT} · {EMAIL}</div></footer>'
            f'<a class="kw-floating-chat" href="{e(wa("Hi KWIKAR, I would like help planning my trip."))}" target="_blank" rel="noopener noreferrer" aria-label="Chat with KWIKAR on WhatsApp"><span aria-hidden="true">WhatsApp</span></a>')


def _asset_version():
    h = hashlib.sha1()
    for f in ('assets/css/site.css', 'assets/js/kw.js'):
        try:
            h.update(open(os.path.join(OUT, f), 'rb').read())
        except OSError:
            pass
    return h.hexdigest()[:10]


def page(path, title, desc, main, active=None, scripts=('kw',), noindex=False, og_image='/assets/img/kwikar-share.webp',
         full_title=False, head_extra='', crumbs=None, main_class='', main_attrs='', og_title=None, og_desc=None):
    t = title if full_title else f'{title} | KWIKAR'
    url = SITE + path
    extra = ld(ORG_LD) + (ld(crumbs_ld(crumbs)) if crumbs else '') + head_extra
    if GOOGLE_VERIFY:
        extra += f'<meta name="google-site-verification" content="{e(GOOGLE_VERIFY)}">'
    if BING_VERIFY:
        extra += f'<meta name="msvalidate.01" content="{e(BING_VERIFY)}">'
    if GA4_ID:
        extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={e(GA4_ID)}"></script>'
                  f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{e(GA4_ID)}');</script>")
    og = og_image if og_image.startswith('http') else SITE + og_image
    js = ''.join(f'<script src="/assets/js/{s}.js?v={VERSION}" defer></script>' for s in scripts)
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t)}</title>
<meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex, follow">' if noindex else ''}
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="KWIKAR">
<meta property="og:title" content="{e(og_title or t)}">
<meta property="og:description" content="{e(og_desc or desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{e(og)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon-blue.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"></noscript>
<link rel="stylesheet" href="/assets/css/site.css?v={VERSION}">
{extra}
{TRUSTPILOT_SCRIPT}
</head>
<body>
{header(active)}
{mobile_nav(path)}
<main class="{main_class}"{main_attrs}>
{main}
</main>
{footer()}
{js}
</body>
</html>
'''
    doc = localize(re.sub(r'\n{2,}', '\n', doc))
    dest = os.path.join(OUT, 'index.html' if path == '/' else path.strip('/') + ('' if path.endswith('.html') else '/index.html'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(doc)


# ================================================================= shared pieces (same markup as the previous site)
def section_head(title, eyebrow=None, action=None, carousel_id=None):
    acts = ''
    if action or carousel_id:
        acts = '<div class="kw-section-actions">'
        if action:
            acts += f'<a href="{action[1]}" class="kw-text-link">{e(action[0])} <span aria-hidden="true">↗</span></a>'
        if carousel_id:
            acts += (f'<div class="kw-row-arrows"><button type="button" aria-label="Previous {e(title)}" data-scroll="{carousel_id}" data-dir="-1">‹</button>'
                     f'<button type="button" aria-label="Next {e(title)}" data-scroll="{carousel_id}" data-dir="1">›</button></div>')
        acts += '</div>'
    eb = f'<span class="kw-eyebrow">{e(eyebrow)}</span>' if eyebrow else ''
    return f'<div class="kw-section-head"><div>{eb}<h2>{e(title)}</h2></div>{acts}</div>'


def page_hero(eyebrow, title, subtitle, image, extra=''):
    return (f'<section class="kw-page-hero"><div class="kw-wrap kw-page-hero-grid"><div><span class="kw-eyebrow">{e(eyebrow)}</span><h1>{e(title)}</h1><p>{e(subtitle)}</p>'
            f'<div class="kw-hero-actions">{extra}<a class="kw-button{" kw-button-ghost" if extra else ""}" href="{e(wa(f"Hi KWIKAR, I would like to enquire about {title}"))}" target="_blank" rel="noopener noreferrer">Plan with us ↗</a></div></div>'
            f'<div class="kw-page-hero-photo" style="background-image:url(\'{e(image)}\')" role="img" aria-label="{e(title)}"></div></div></section>')


def price_line(t):
    if t.get('price'):
        return f'From <strong>{money(t["price"])}</strong> {("/ " + e(t["unit"])) if t.get("unit") else ""}'
    return 'Price on request'


def market_card(t):
    """Home page tour card (kw-market-card). No supplier ratings (SEO strategy rule 9)."""
    href = tour_href(t)
    img = t.get('img') or '/assets/img/hero-dubai-mobile.webp'
    return (f'<article class="kw-market-card"><a href="{href}" class="kw-market-image" aria-label="View {e(t["name"])}"><img src="{e(img)}" alt="{e(t["name"])}" loading="lazy" width="640" height="480"></a>'
            f'<div class="kw-market-info"><span>{e(loc_name(t["loc"]))}</span><h3><a href="{href}">{e(t["name"])}</a></h3><p>{price_line(t)}</p>'
            f'<a class="kw-card-view" href="{href}">View experience →</a></div></article>')


def list_card(t):
    """Listing card (kw-list-card), same markup as the previous site."""
    href = tour_href(t)
    cats = t.get('cats') or []
    cat_ = ''
    if cats:
        cat_ = ' · ' + (next((c for c in cats if re.search('desert', t['name'], re.I) and re.search('desert', c, re.I)), None) or cats[0])
    img = t.get('img') or '/assets/img/hero-dubai.webp'
    return (f'<article class="kw-list-card"><a href="{href}"><img src="{e(img)}" loading="lazy" alt="{e(t["name"])}" width="640" height="480"></a><div><span>{e(loc_name(t["loc"]))}{e(cat_)}</span>'
            f'<h3><a href="{href}">{e(t["name"])}</a></h3><p>{price_line(t)}</p><a class="kw-card-view" href="{href}">View experience →</a></div></article>')


# ================================================================= home
CITY_CARDS = [
    ('dubai', 'Dubai', 'Modern city, iconic experiences', photo('1512453979798-5ea266f8880c')),
    ('abu-dhabi', 'Abu Dhabi', 'Culture, heritage and beyond', '/assets/img/hero-abu-dhabi.webp'),
    ('sharjah', 'Sharjah', 'Culture and heritage', photo('1580674684081-7617fbf3d745')),
    ('fujairah', 'Fujairah', 'Coast and mountains', photo('1506929562872-bb421503ef21')),
    ('ajman', 'Ajman', 'Coastal experiences', photo('1518684079-3c830dcef090')),
    ('ras-al-khaimah', 'Ras Al Khaimah', 'Mountains, beaches and more', photo('1451337516015-6b6e9a44a8a3')),
    ('singapore', 'Singapore', 'Iconic sights and family fun', photo('1525625293386-3f8f99389edd')),
]
SLIDES = [
    {'eyebrow': 'DUBAI', 'title': 'Discover Dubai', 'description': 'Iconic experiences, modern attractions and unforgettable moments with KWIKAR.', 'href': '/destinations/dubai', 'image': '/assets/img/hero-dubai.webp'},
    {'eyebrow': 'ABU DHABI', 'title': 'Abu Dhabi Awaits', 'description': 'Culture, heritage and world-class attractions', 'href': '/destinations/abu-dhabi', 'image': '/assets/img/hero-abu-dhabi.webp'},
    {'eyebrow': 'DESERT', 'title': 'Desert Adventures', 'description': 'Dunes, thrills and unforgettable moments', 'href': '/activities/desert-adventures', 'image': '/assets/img/hero-desert.webp'},
]

# ---------------- homepage SEO content (from the "Kwikar Website Content – Homepage" doc).
# Tour names and prices are looked up in the live feed at build time; a tour that disappears is left out.
HOME_PICKS = [('Burj Khalifa - At The Top', 'Observation deck'), ('Dubai Frame', 'Observation deck'), ('Global Village', 'Theme park'),
              ('Dubai Miracle Garden', 'Theme park'), ('Aquarium and Underwater Zoo at the Dubai Mall', 'Family friendly'),
              ('Aquaventure World Waterpark', 'Water park'), ('Ski Dubai', 'Snow park'), ('Ferrari World Abu Dhabi Theme Park', 'Theme park'),
              ('Louvre Abu Dhabi', 'Museum')]
HOME_CRUISES = ['Alexandra Dhow Cruise in Dubai Marina', 'Lotus Royale Dinner Cruise', 'Dubai Water Canal Dhow Cruise']


def find_tour(name):
    n = name.lower()
    return next((t for t in TOURS if t['name'].lower() == n), None) or next((t for t in TOURS if n in t['name'].lower()), None)


def tlink(t, text=None):
    return f'<a href="{tour_href(t)}">{e(text or t["name"])}</a>'


def home_intro():
    picks = [t for t in (find_tour(n) for n, _ in HOME_PICKS) if t and t.get('price')]
    low = min((t['price'] for t in picks), default=None)
    wa_ = wa('Hi KWIKAR, I would like help planning my UAE trip.')
    return (f'<section class="kw-market-section kw-home-intro"><div class="kw-market-wrap"><span class="kw-eyebrow">UAE TRAVEL · ONE TEAM</span><h1>UAE Tours and Activities, Holidays, Transfers &amp; Visas</h1>'
            f'<p>KWIKAR is a UAE travel company where you can plan UAE tours and activities, holiday packages, private chauffeur transfers and tourist visa assistance in one place.'
            + (f' Attraction tickets start from {money(low)} per person.' if low else '')
            + ' Send your date and group size, and our team confirms availability and the final price before you pay.</p>'
            f'<div class="kw-home-intro-ctas"><a class="kw-button" href="{e(wa_)}" target="_blank" rel="noopener noreferrer">WhatsApp us ↗</a>'
            f'<a class="kw-button kw-button-ghost" href="tel:+{PHONE}">Call {PHONE_FMT}</a><a class="kw-button kw-button-ghost" href="/activities">Explore activities</a></div></div></section>')


def home_faqs():
    et = next((c for c in CARS if c['name'] == 'Mercedes E-Class'), None)
    uae_v = [v for v in VISAS if 'UAE Tourist' in v['name'] and v.get('price')]
    uae_cities = [l['name'] for l in REAL_LOCATIONS if l['group'] == 'uae']
    fam = [h['name'] for h in HOLIDAYS if re.search(r'Family|Honeymoon', h['name'])]
    return [
        ('How do I book a tour or activity with KWIKAR?', f'Choose an experience on our website and send a request with your preferred date and number of guests. You can also message us on WhatsApp or call {PHONE_FMT}. Our team checks availability with the supplier, confirms the final price and booking terms, and only then asks for payment.'),
        ('Are the prices on KWIKAR final?', 'Prices shown are starting prices, and tour prices come from live supplier rates. The final amount depends on your date, group size, ticket type and any extras. We send you a confirmed quote before you pay, so you know the full cost in advance.'),
        ('Does KWIKAR offer airport transfers from Dubai Airport?', 'Yes. We arrange private transfers from Dubai International Airport (DXB) to hotels in Downtown, DIFC, Dubai Marina, JBR, Palm Jumeirah and other areas.'
         + (f' A Business Sedan (Mercedes E-Class or similar) to Downtown or DIFC starts from {money(DXB_DT)}.' if et else '') + ' Share your flight number so we can plan the pickup.'),
        ('Can KWIKAR help me get a UAE tourist visa?', 'Yes. We assist with 14, 30 and 60-day UAE tourist visas, single and multiple entry'
         + (f', from {money(min(v["price"] for v in uae_v))}' if uae_v else '') + '. Processing usually takes three to four working days. You typically need a passport valid for six months and a recent colour photo. The issuing authority makes the final decision.'),
        ('Which UAE cities does KWIKAR cover?', f'Our UAE destinations are {", ".join(uae_cities[:-1])} and {uae_cities[-1]}. Private chauffeur transfers also run between emirates, for example from Dubai to Abu Dhabi. For travel outside the UAE, we arrange holiday packages to several countries in Asia and Europe.'),
        ('Do you offer holiday packages for families and couples?', 'Yes. Options include multi-night Dubai and Abu Dhabi packages'
         + (f', and Singapore trips such as {" and ".join(fam[:2])}' if fam else '') + '. Each package is priced for your travel dates and preferred hotel. Send us your plans and we will share a tailored quote.'),
    ]


def seo_head(eyebrow, title, sub=None, center=False):
    """Section heading in the site's own style: eyebrow, heading, optional subtitle and a short rule."""
    return (f'<div class="kw-seo-head{" kw-center" if center else ""}"><span class="kw-eyebrow">{e(eyebrow)}</span><h2>{title}</h2>'
            + (f'<p>{sub}</p>' if sub else '') + '<i aria-hidden="true"></i></div>')


def facts(rows):
    """Label / value rows (used instead of plain tables)."""
    return '<dl class="kw-facts">' + ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows) + '</dl>'


def info_cards(items, numbered=False):
    return '<div class="kw-info-cards">' + ''.join(
        f'<div class="kw-info-card"><span>{f"{i + 1:02d}" if numbered else icon}</span><h3>{e(t)}</h3><p>{d}</p></div>'
        for i, (icon, t, d) in enumerate(items)) + '</div>'


def faq_cards(items, open_all=True):
    if open_all:
        return '<div class="kw-faq-cards">' + ''.join(f'<div class="kw-faq-card"><h3>{e(q)}</h3><p>{e(a)}</p></div>' for q, a in items) + '</div>'
    return '<div class="kw-faq-cards">' + ''.join(f'<details class="kw-faq-card"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in items) + '</div>'


def home_guide():
    picks = [(t, c) for t, c in ((find_tour(n), c) for n, c in HOME_PICKS) if t and t.get('price')]
    cities = [l['name'] for l in REAL_LOCATIONS if l['group'] == 'uae' and l['id'] in LIVE_LOCS]
    n_exp = len(TOURS)
    price_rows = ''.join(f'<a class="kw-price-row" href="{tour_href(t)}"><span><strong>{e(t["name"])}</strong><small>{e(loc_name(t["loc"]))} · {e(c)}</small></span><em>From {money(t["price"])}</em></a>' for t, c in picks)
    cats = [c for c in LIVE_CATS if c['slug'] not in ('events',)]
    chips = ''.join(f'<a href="/activities/{c["slug"]}">{e(c["name"])}<span>↗</span></a>' for c in cats)
    g = find_tour('Vintage G-Class Evening Heritage Safari')
    cruises = [t for t in (find_tour(n) for n in HOME_CRUISES) if t]
    yacht = find_tour('Shared Luxury Yacht Tour')
    speed = find_tour('Speed Boat Tour Dubai')
    by_type = {}
    for c in CARS:
        by_type.setdefault(c['type'], []).append(c)
    uae_v = [v for v in VISAS if 'UAE Tourist' in v['name'] and v.get('price')]
    other_v = [v['name'] for v in VISAS if 'UAE Tourist' not in v['name']]
    hol_countries = [c for c in dict.fromkeys(h['country'] for h in HOLIDAYS) if c != 'UAE']
    nights = [h['nights'] for h in HOLIDAYS if h['country'] == 'UAE']
    intl = [l for l in REAL_LOCATIONS if l['group'] != 'uae']
    uae_locs = [l for l in REAL_LOCATIONS if l['group'] == 'uae']
    wa_ = wa('Hi KWIKAR, I would like help planning my UAE trip.')
    e150 = money(DXB_DT)

    s1 = (f'<section class="kw-seo-section"><div class="kw-market-wrap">'
          + seo_head('POPULAR PICKS', 'Top UAE tours and activities to book',
                     f'Choose from {n_exp} experiences across {", ".join(cities[:-1])} and {cities[-1]}. These are popular picks with the starting prices currently listed on KWIKAR, from live supplier rates last checked {CHECKED}.')
          + f'<div class="kw-price-list">{price_rows}</div>'
          + f'<div class="kw-seo-split kw-seo-split-tight"><div><h3>Browse by travel style</h3><p>Theme parks and the aquarium suit families, while dinner cruises and yachts make a relaxed evening out. For a Dubai-only shortlist, see <a href="/destinations/dubai">things to do in Dubai</a>.</p></div>'
          + f'<div class="kw-chip-links">{chips}</div></div>'
          + (f'<p class="kw-seo-note">Beyond the city, the <a href="{tour_href(g)}">{e(g["name"])}</a> is a desert outing in a classic Mercedes 4x4, from {money(g["price"])} per person. More options are in <a href="/activities/desert-adventures">desert adventures</a>.</p>' if g and g.get('price') else '')
          + '</div></section>')

    s2 = ''
    if cruises:
        rows = [(f'<a href="{tour_href(t)}">{e(t["name"])}</a>', f'From {money(t["price"])} per person' if t.get('price') else 'Price on request') for t in cruises]
        if yacht and yacht.get('price'):
            rows.append((f'<a href="{tour_href(yacht)}">Shared yacht tour</a>', f'From {money(yacht["price"])} per person'))
        if speed and speed.get('price'):
            rows.append((f'<a href="{tour_href(speed)}">Speed boat tour</a>', f'From {money(speed["price"])} per person'))
        s2 = (f'<section class="kw-seo-section kw-market-alt"><div class="kw-market-wrap kw-seo-split"><div>'
              + seo_head('ON THE WATER', 'Dhow and dinner cruises in Dubai')
              + '<p class="kw-seo-lead">An evening on the water is one of the easiest ways to see the Dubai skyline. Choose a traditional wooden dhow with a buffet dinner, a dinner cruise with live entertainment, or a shared yacht at sunset.</p>'
              + '<a class="kw-text-link" href="/activities/cruises">See all Dubai cruises <span aria-hidden="true">↗</span></a></div>'
              + f'<div>{facts(rows)}</div></div></section>')

    car_rows = [(f'<a href="{cls_href(c)}">{e(c["name"])}</a>', f'{e(", ".join(c["models"][:2]))} or similar · up to {c["guests"]} guests') for c in TR_CLASSES]
    s3 = (f'<section class="kw-seo-section"><div class="kw-market-wrap kw-seo-split"><div>'
          + seo_head('PRIVATE TRANSFERS', 'Airport transfers and chauffeur service')
          + f'<p class="kw-seo-lead">Travel between Dubai International Airport (DXB), your hotel and other emirates in a private car with a professional chauffeur. A Business Sedan (Mercedes E-Class or similar) from DXB to <a href="/transfers/dubai-airport-to-downtown-dubai">Downtown Dubai or DIFC</a> starts from {e150}; popular routes also include <a href="/transfers/dubai-airport-to-dubai-marina">Dubai Marina</a>, <a href="/transfers/dubai-airport-to-palm-jumeirah">Palm Jumeirah</a> and <a href="/transfers/dubai-to-abu-dhabi">Dubai to Abu Dhabi</a>.</p>'
          + f'<p>Prices are per car and include {e(INCLUDED_TXT)}. Share your flight number and your driver follows your flight.</p>'
          + '<a class="kw-text-link" href="/transfers#transfer-enquiry">Get a transfer quote <span aria-hidden="true">↗</span></a></div>'
          + f'<div>{facts(car_rows)}</div></div></section>')

    visa_rows = [(e(re.sub(r"UAE Tourist Visa ", "", v["name"])), f'From {money(v["price"])} · {e(v["processing"])}') for v in uae_v]
    s4 = (f'<section class="kw-seo-section kw-market-alt"><div class="kw-market-wrap kw-seo-split"><div>'
          + seo_head('TRAVEL DOCUMENTS', 'UAE tourist visa assistance')
          + '<p class="kw-seo-lead">Planning a trip but still need a visa? KWIKAR helps you apply for a UAE tourist visa and explains the documents your nationality needs.</p>'
          + f'<p>{e(", ".join(other_v[:-1]))} and {e(other_v[-1])} are also available on request. Approval is always decided by the issuing authority.</p>'
          + '<a class="kw-text-link" href="/visa">UAE visa options <span aria-hidden="true">↗</span></a></div>'
          + f'<div>{facts(visa_rows)}</div></div></section>')

    city_chips = ''.join(f'<a href="{dest_href(l["id"])}">{e(l["name"])}<span>↗</span></a>' for l in uae_locs if l['id'] in LIVE_LOCS)
    s5 = (f'<section class="kw-seo-section"><div class="kw-market-wrap kw-seo-split"><div>'
          + seo_head('HOLIDAYS', 'Dubai and Abu Dhabi holiday packages')
          + f'<p class="kw-seo-lead">Prefer a ready-made itinerary? Our UAE packages run from {min(nights)} to {max(nights)} nights, from a short Abu Dhabi break to Dubai itineraries including a New Year celebration with gala dinner.</p>'
          + f'<p>Every package is quoted for your dates and preferred hotel. We also arrange holidays to {", ".join(hol_countries[:-1])} and {hol_countries[-1]}.</p>'
          + '<a class="kw-text-link" href="/holidays">Holiday packages <span aria-hidden="true">↗</span></a></div><div>'
          + seo_head('DESTINATIONS', 'Across the UAE and beyond')
          + f'<p>Inside the UAE we cover {", ".join(l["name"] for l in uae_locs[:-1])} and {uae_locs[-1]["name"]}. Abroad, choices include {", ".join(l["name"] for l in intl[:6])} and more.</p>'
          + f'<div class="kw-chip-links">{city_chips}<a href="/destinations">All destinations<span>↗</span></a></div></div></div></section>')

    s6 = (f'<section class="kw-seo-section kw-market-alt"><div class="kw-market-wrap">'
          + seo_head('HOW IT WORKS', 'Booking with KWIKAR in three steps', 'No account and no online payment. You only pay once our team has confirmed everything.', center=True)
          + info_cards([('', 'Choose', 'Browse experiences, transfers or packages and note the indicative price.'),
                        ('', 'Send a request', 'Send your preferred date and number of guests by form, WhatsApp or phone.'),
                        ('', 'Confirm and pay', 'Our team replies with availability, the final price and booking terms. You pay only after that.')], numbered=True)
          + '</div></section>')

    s7 = (f'<section class="kw-seo-section"><div class="kw-market-wrap">'
          + seo_head('LOCAL TIPS', 'Tips for visiting Dubai and Abu Dhabi')
          + info_cards([('☀', 'Plan around the heat', 'Summer days are very hot. Book desert and outdoor activities for early morning or evening; Ski Dubai and the aquarium suit midday.'),
                        ('✦', 'Dress modestly at cultural sites', 'Cover shoulders and knees at mosques. Women need a headscarf at the Sheikh Zayed Grand Mosque.'),
                        ('◷', 'Check seasonal openings', 'Outdoor attractions such as Global Village and Dubai Miracle Garden open for a season, roughly October to May.'),
                        ('☾', 'Respect Ramadan customs', 'During the holy month, avoid eating or drinking in public during daylight hours.')])
          + '</div></section>')

    s8 = ''
    if POSTS:
        guide_cards = ''.join(f'<a class="kw-guide-link" href="{post_href(b)}"><span class="kw-eyebrow">TRAVEL GUIDE</span><strong>{e(b["h1"])}</strong><small>{e(b["summary"][:120].rsplit(" ", 1)[0])}…</small><em>Read the guide →</em></a>' for b in POSTS[:3])
        s8 = (f'<section class="kw-seo-section kw-market-alt"><div class="kw-market-wrap">'
              + seo_head('TRAVEL GUIDES', 'Plan with our guides', None)
              + f'<div class="kw-guide-links">{guide_cards}</div><p class="kw-seo-note"><a href="/blog">All travel guides ↗</a></p></div></section>')

    s9 = (f'<section class="kw-seo-section"><div class="kw-market-wrap kw-seo-narrow">'
          + seo_head('FAQ', 'Questions, answered', None, center=True)
          + faq_cards(home_faqs())
          + f'<div class="kw-final-cta"><div><h2>Plan your UAE trip today</h2><p>Tell us where you want to go and when. Our team will reply with options and a clear quote.</p></div><div><a class="kw-button" href="{e(wa_)}" target="_blank" rel="noopener noreferrer">WhatsApp us ↗</a><a class="kw-final-wa" href="tel:+{PHONE}">Call {PHONE_FMT}</a></div></div>'
          + f'<p class="kw-checked kw-center-text">Last updated {CHECKED} · Reviewed by the KWIKAR team. Prices and availability are confirmed at the time of booking.</p>'
          + '</div></section>')
    return s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9


def build_home():
    seen, best = set(), []
    for t in TOURS:
        if t.get('price') and t.get('img') and t['img'] not in seen:
            seen.add(t['img'])
            best.append(t)
    best = best[:12]
    cities = [c for c in CITY_CARDS if c[0] in LIVE_LOCS]
    prev_, cur, nxt = SLIDES[-1], SLIDES[0], SLIDES[1]

    def peek(s, side):
        return (f'<button type="button" class="kw-slider-peek kw-peek-{side}" data-slide-step="{"-1" if side == "left" else "1"}" aria-label="View {e(s["title"])}" style="background-image:url(\'{s["image"]}\')">'
                f'<span class="kw-peek-copy"><span class="kw-peek-eyebrow">{e(s["eyebrow"])}</span><strong>{e(s["title"])}</strong><small>{e(s["description"])}</small><em>Explore &nbsp; →</em></span></button>')
    dots = ''.join(f'<button type="button" class="{"selected" if i == 0 else ""}" data-slide="{i}" aria-label="Show {e(s["eyebrow"])} slide"></button>' for i, s in enumerate(SLIDES))
    city_html = ''.join(f'<a class="kw-city-card" href="/destinations/{i}"><span class="kw-city-photo" style="background-image:url(\'{img}\')"></span><span>Things to do in <strong>{e(n)}</strong><small>{e(sub)}</small></span></a>'
                        for i, n, sub, img in cities)
    hol = ''.join(f'<a class="kw-home-feature" href="/holidays?country={quote(h["country"])}"><img src="{e(h["img"])}" loading="lazy" alt=""><span>{e(h["country"])}</span><strong>{e(h["name"])}</strong><small>{h["nights"]} nights · Request a quote</small></a>'
                  for h in [x for x in HOLIDAYS if x.get('img')][:6])
    cars = ''.join(f'<a class="kw-home-feature" href="{car_class_href(c)}"><img src="{e(c["img"])}" loading="lazy" alt=""><span>{e(c["type"])}</span><strong>{e(c["name"])}</strong><small>Up to {c["pax"]} passengers · Enquire for a quote</small></a>'
                   for c in CARS[:5])
    visas = ''.join(f'<a href="/visa?type={quote(v["name"])}#visa-enquiry"><span>UAE TOURIST VISA</span><strong>{e(v["name"])}</strong><small>{("From " + money(v["price"])) if v.get("price") else "Request a quote"} →</small></a>'
                    for v in [v for v in VISAS if re.search(r'30 Days|60 Days', v['name'])][:4])
    main = f'''<section class="kw-slider" aria-label="Explore destinations" data-slider='{e(json.dumps(SLIDES))}'><div class="kw-slider-track">
{peek(prev_, "left")}
<div class="kw-slider-main first-slide" style="background-image:url('{cur["image"]}')"><div class="kw-slider-copy"><span class="kw-slide-eyebrow">{e(cur["eyebrow"])}</span><h2>{e(cur["title"])}</h2><p>{e(cur["description"])}</p><a href="{cur["href"]}">Explore &nbsp; →</a></div><div class="kw-slider-dots">{dots}</div></div>
{peek(nxt, "right")}
</div></section>
{home_intro()}
<section class="kw-market-section kw-market-cities"><div class="kw-market-wrap">{section_head("Best cities to visit", action=("View all", "/destinations"), carousel_id="kw-home-cities" if len(cities) > 3 else None)}<div class="kw-city-grid" id="kw-home-cities">{city_html}</div></div></section>
<section class="kw-market-section kw-market-alt kw-popular"><div class="kw-market-wrap">{section_head("Best-selling experiences", action=("View all", "/activities"), carousel_id="kw-home-best")}<div class="kw-home-row" id="kw-home-best">{"".join(market_card(t) for t in best)}</div></div></section>
<section class="kw-market-section"><div class="kw-market-wrap">{section_head("Holiday packages", action=("View all", "/holidays"), carousel_id="kw-home-holidays")}<div class="kw-home-row" id="kw-home-holidays">{hol}</div></div></section>
<section class="kw-market-section kw-market-alt"><div class="kw-market-wrap">{section_head("Private transfers", action=("View all", "/transfers"), carousel_id="kw-home-transfers")}<div class="kw-home-row" id="kw-home-transfers">{cars}</div></div></section>
<section class="kw-market-section"><div class="kw-market-wrap">{section_head("Visa assistance", action=("View all", "/visa"))}<div class="kw-home-visa">{visas}</div></div></section>
<section class="kw-market-section kw-market-alt"><div class="kw-market-wrap">{section_head("Why travellers choose KWIKAR")}<div class="kw-market-benefits kw-benefits-5"><div><span>01</span><h3>One team for the whole trip</h3><p>Activities, cruises, transfers, visas and holidays in one conversation.</p></div><div><span>02</span><h3>Clear quotes first</h3><p>The final price and terms are confirmed before you pay, with no booking or card fees.</p></div><div><span>03</span><h3>WhatsApp support</h3><p>Message the team directly about your plans, before and during your trip.</p></div><div><span>04</span><h3>Local UAE company</h3><p>Operated by Kwikar LLC-FZ in the United Arab Emirates.</p></div><div><span>05</span><h3>Modern fleet</h3><p>From electric cars to seven-seat vans for families and groups.</p></div></div></div></section>'''
    main += home_guide()
    faq_ld = ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': _plain(a)}} for q, a in home_faqs()]})
    page('/', 'UAE Tours and Activities, Transfers & Visas | KWIKAR',
         'Book UAE tours and activities, Dubai cruises, private airport transfers and tourist visas with KWIKAR. Get a clear quote on WhatsApp before you pay.',
         main, active='Destinations', full_title=True, main_class='kw-market-home',
         og_title='UAE Tours, Activities, Transfers & Visas – KWIKAR',
         og_desc='Plan attractions, dhow cruises, chauffeur transfers, holidays and UAE visas with one team. Clear quotes before you pay.',
         head_extra=faq_ld + '<link rel="preload" as="image" href="/assets/img/hero-dubai.webp" media="(min-width: 561px)"><link rel="preload" as="image" href="/assets/img/hero-dubai-mobile.webp" media="(max-width: 560px)">')


# ================================================================= listings (same markup as ExperienceList)
try:
    HUB_INTROS = json.load(open(os.path.join(ROOT, 'data', 'hub-intros.json'), encoding='utf-8'))
except Exception:
    HUB_INTROS = {}


def hub_intro(key, heading, items, where='', eyebrow='ABOUT'):
    """80–150 word intro for a hub: hand-written text + live counts, prices and top picks from the API."""
    text = HUB_INTROS.get(key)
    if not text or not items:
        return ''
    priced = [t['price'] for t in items if t.get('price')]
    top = items[:3]
    picks = ', '.join(f'<a href="{tour_href(t)}">{e(t["name"])}</a>' for t in top[:-1]) + (f' and <a href="{tour_href(top[-1])}">{e(top[-1]["name"])}</a>' if len(top) > 1 else f'<a href="{tour_href(top[0])}">{e(top[0]["name"])}</a>')
    live = (f'KWIKAR currently lists {len(items)} experience{"s" if len(items) != 1 else ""}{where}'
            + (f', with prices from {money(min(priced))}' if priced else '') + f'. Popular picks include {picks}.')
    return (f'<section class="kw-seo-section kw-hub-about"><div class="kw-market-wrap kw-seo-narrow">'
            + seo_head(eyebrow, e(heading)) + f'<div class="kw-seo-prose"><p>{e(text)}</p><p>{live}</p></div></div></section>')


def list_search():
    return '<form class="kw-list-search" role="search" data-list-search><input placeholder="Search experiences" aria-label="Search experiences"><button type="submit">Search →</button></form>'


def list_body(items, location=None, category=None, kind='standard'):
    cats_with = [c for c in CATEGORIES if any((not location or t['loc'] == location) and tf.matches_category(t, c['slug'], c['term']) for t in TOURS)]
    side_cats = ''.join(f'<a href="/activities/{c["slug"]}">{e(c["name"])}</a>' for c in cats_with)
    base = items if category else TOURS
    relevant = [l for l in LOCATIONS if any(t['loc'] == l['id'] for t in base)]
    side_dest = ''.join(f'<a href="{dest_href(l["id"])}">{e(l["name"])}</a>' for l in relevant[:14])
    n = len(items)
    word = 'experience' if n == 1 else 'experiences'
    if category in ('cruises', 'yachts', 'events') or kind in ('category', 'marine'):
        sing = {'yachts': 'yacht', 'cruises': 'cruise', 'events': 'event'}.get(category, 'experience')
        word = sing if n == 1 else ({'yachts': 'yachts', 'cruises': 'cruises', 'events': 'events'}.get(category) or next(c['name'].lower() for c in CATEGORIES if c['slug'] == category))
    dest_sel = ''
    if not location and len(relevant) > 1:
        dest_sel = ('<label>Destination<select data-dest-select><option value="all">All destinations</option>'
                    + ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in relevant) + '</select></label>')
    grid = ''.join(list_card(t) for t in items) or (
        '<div class="kw-market-empty"><p>No experiences are currently listed here.</p> <a href="/activities">Browse all experiences</a> or <a href="/contact">ask our team</a>.</div>')
    return (f'<div class="kw-market-wrap kw-list-body" id="kw-page-results"><aside class="kw-list-sidebar"><h2>Explore</h2>'
            f'<a href="{dest_href(location) if location else "/activities"}">All experiences</a>{side_cats}<h2>Destinations</h2>{side_dest}</aside>'
            f'<section class="kw-list-results"><div class="kw-list-controls"><div><h2 data-count-title>{n} {word}</h2><p>Live supplier prices shown when available, last checked {CHECKED}. Final details are confirmed on enquiry.</p></div>'
            f'<div class="kw-list-selects">{dest_sel}<label>Sort by<select data-sort><option value="popular">Popular</option><option value="low">Price low to high</option><option value="high">Price high to low</option></select></label></div></div>'
            f'<div class="kw-list-grid" data-grid>{grid}</div><button class="kw-market-more" data-more hidden>Show more experiences →</button></section></div>')


def build_listings():
    # /activities
    main = (f'<section class="kw-list-banner" style="background-image:linear-gradient(90deg,#07162aeb,#07162a3d),url(\'/assets/img/hero-dubai.webp\')"><div class="kw-market-wrap">'
            f'<nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Activities &amp; attractions</nav><h1>Activities &amp; attractions</h1>'
            f'<p>Discover tours, tickets and experiences across the UAE and beyond.</p>{list_search()}</div></section>'
            f'{list_body(TOURS)}{hub_intro("page:activities", "Activities and attractions across the UAE", TOURS, eyebrow="ABOUT KWIKAR ACTIVITIES")}')
    page('/activities', 'Activities & Attractions', 'Browse tours, attraction tickets, desert safaris, cruises and theme parks in Dubai, Abu Dhabi and the UAE, with prices our team keeps up to date.', main,
         active='Activities', main_class='kw-list-page kw-list-standard', main_attrs=' data-listing data-kind="standard"',
         crumbs=[('Home', '/'), ('Activities', '/activities')])

    # /search (not indexed)
    main = (f'<section class="kw-list-banner" style="background-image:linear-gradient(90deg,#07162aeb,#07162a3d),url(\'/assets/img/hero-dubai.webp\')"><div class="kw-market-wrap">'
            f'<nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Search experiences</nav><h1>Search experiences</h1>'
            f'<p>Search tours, tickets and activities by name, destination or category.</p>{list_search()}</div></section>{list_body(TOURS)}')
    page('/search', 'Search Experiences', 'Search KWIKAR experiences and attractions.', main, noindex=True,
         main_class='kw-list-page kw-list-standard', main_attrs=' data-listing data-kind="search"')

    # categories
    for c in CATEGORIES:
        slug = c['slug']
        items = [t for t in TOURS if tf.matches_category(t, slug, c['term'])]
        marine = slug in ('cruises', 'yachts')
        kind = 'marine' if marine else 'category'
        first_img = next((t['img'] for t in items if t.get('img')), None)
        primary = first_img or '/assets/img/hero-dubai.webp'
        crumb = f'<nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/activities">Activities</a> / {e(c["name"])}</nav>'
        desc_ = f'Explore {e(c["name"].lower())} and enquire with our team for current availability.'
        if marine:
            switch = ''.join(f'<a href="/activities/{s}"{" aria-current=page" if s == slug else ""}>Explore {s}</a>' for s in ('cruises', 'yachts') if CAT_COUNT[s])
            bg = f' style="background-image:linear-gradient(90deg,#071a33ec,#071a33a6 58%,#071a3333),url(\'{e(first_img)}\')"' if first_img else ''
            lead = f'<section class="kw-marine-lead"{bg}><div class="kw-market-wrap">{crumb}<span class="kw-eyebrow">EXPERIENCES ON THE WATER</span><h1>{e(c["name"])}</h1><p>{desc_}</p><div class="kw-marine-switch">{switch}</div>{list_search()}</div></section>'
        else:
            bg = f' style="background-image:linear-gradient(90deg,#061b34db,#061b3440),url(\'{U("1777231755912-109c409e760e", 1600)}\')"' if slug == 'events' else ''
            lead = (f'<section class="kw-category-lead"{bg}><div class="kw-market-wrap kw-category-lead-grid"><div>{crumb}<span class="kw-eyebrow">EXPLORE BY ACTIVITY</span><h1>{e(c["name"])}</h1><p>{desc_}</p>{list_search()}</div>'
                    f'<div class="kw-category-lead-photo"><img src="{e(primary)}" alt=""><span>{len(items)} experiences to explore</span></div></div></section>')
        places = [l for l in LOCATIONS if any(t['loc'] == l['id'] for t in items)][:8]
        places_html = ''
        if len(places) > 1:
            btns = ''.join(f'<button type="button" data-place-id="{l["id"]}"><img src="{e(l.get("img") or "/assets/img/hero-dubai.webp")}" alt="" loading="lazy"><span>{e(l["name"])}<small>{sum(1 for t in items if t["loc"] == l["id"])} experiences</small></span></button>' for l in places)
            places_html = f'<section class="kw-category-places"><div class="kw-market-wrap"><div class="kw-section-head"><div><h2>Explore {e(c["name"].lower())} by destination</h2></div></div><div class="kw-category-places-row">{btns}</div></div></section>'
        related = ''.join(f'<a href="/activities/{x["slug"]}">{e(x["name"])}<span>↗</span></a>' for x in LIVE_CATS if x['slug'] != slug)[:100000]
        rel_html = f'<section class="kw-related-categories"><div class="kw-market-wrap"><h2>Keep exploring</h2><div>{related}</div></div></section>'
        main = lead + places_html + list_body(items, category=slug, kind=kind) + hub_intro(f'cat:{slug}', f'{c["name"]} in the UAE', items, eyebrow='GOOD TO KNOW') + rel_html
        page(f'/activities/{slug}', f'{c["name"]} in Dubai & the UAE', CAT_DESC.get(slug) or f'Browse {c["name"].lower()} experiences with KWIKAR. Enquire for current availability.', main,
             active='Cruises' if slug == 'cruises' else 'Activities', noindex=not items,
             main_class=f'kw-list-page kw-list-{kind} kw-category-{slug}',
             main_attrs=f' data-listing data-kind="{kind}" data-category="{slug}" data-term="{e(c["term"])}"',
             crumbs=[('Home', '/'), ('Activities', '/activities'), (c['name'], f'/activities/{slug}')])


def build_destinations():
    # /destinations hub (previously /attractions)
    live = [l for l in LOCATIONS if l['id'] in LIVE_LOCS]
    uae = [l for l in live if l['group'] == 'uae']
    world = [l for l in live if l['group'] != 'uae' and l['id'] != 'other']

    def count(lid):
        return f'{sum(1 for t in TOURS if t["loc"] == lid)} experiences'
    uae_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in uae)
    w_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in world)
    search = (f'<form class="kw-discover-form" action="/search" method="get" role="search"><label>Destination<span><select name="destination"><option value="">All destinations</option>'
              f'<optgroup label="United Arab Emirates">{uae_opts}</optgroup>{f"<optgroup label=Worldwide>{w_opts}</optgroup>" if w_opts else ""}</select></span></label>'
              f'<label>What would you like to do?<span><input type="search" name="q" placeholder="Tour, attraction or activity" autocomplete="off"></span></label><button type="submit">Find experiences →</button></form>')
    tiles = ''.join(f'<a class="kw-attractions-tile" href="/destinations/{l["id"]}"><img src="{e(l.get("img") or "/assets/img/hero-dubai.webp")}" alt="" loading="lazy"><span><strong>{e(l["name"])}</strong><small>{count(l["id"])} ↗</small></span></a>' for l in uae)
    wl = ''.join(f'<a href="/destinations/{l["id"]}"><strong>{e(l["name"])}</strong><span>{count(l["id"])} ↗</span></a>' for l in world)
    main = (f'<section class="kw-attractions-hero"><div class="kw-market-wrap"><span class="kw-eyebrow">KWIKAR DESTINATIONS</span><h1>Where would you like to explore?</h1>'
            f'<p>Browse by city, then choose an experience or ask our team to plan your day.</p>{search}</div></section>'
            f'<section class="kw-market-section"><div class="kw-market-wrap"><div class="kw-section-head"><div><span class="kw-eyebrow">EXPLORE THE EMIRATES</span><h2>United Arab Emirates</h2></div><a class="kw-text-link" href="/activities">Browse by activity ↗</a></div><div class="kw-attractions-grid">{tiles}</div></div></section>'
            + hub_intro('page:destinations', 'Choosing where to go', TOURS, eyebrow='PLANNING')
            + (f'<section class="kw-market-section kw-market-alt"><div class="kw-market-wrap"><span class="kw-eyebrow">TRAVEL FURTHER</span><h2>Worldwide destinations</h2><p class="kw-market-subtitle">Explore international experiences from the current catalogue.</p><div class="kw-attractions-world">{wl}</div></div></section>' if wl else ''))
    page('/destinations', 'Destinations', 'Browse tours and activities by destination: Dubai, Abu Dhabi, Ras Al Khaimah and more. Compare current prices and send your request on WhatsApp.', main, active='Destinations',
         main_class='kw-attractions-hub', crumbs=[('Home', '/'), ('Destinations', '/destinations')])

    # /destinations/{id}: city hub with every experience (same layout as the previous site)
    for l in LOCATIONS:
        lid, name = l['id'], l['name']
        items = [t for t in TOURS if t['loc'] == lid]
        heading = city_title(lid)
        crumb_label = 'More' if lid == 'other' else name
        if not items:
            main = (f'<section class="kw-destination-lead"><div class="kw-market-wrap kw-destination-lead-grid"><div class="kw-lead-copy"><nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/destinations">Destinations</a> / {e(crumb_label)}</nav>'
                    f'<span class="kw-eyebrow">{"UNITED ARAB EMIRATES" if l["group"] == "uae" else "WORLDWIDE EXPERIENCES"}</span><h1>{e(heading)}</h1><p>We don\'t have {e(name)} experiences listed right now. Tell us your dates and our team will check options for you.</p>'
                    f'<a class="kw-lead-action" href="{e(wa(f"Hi KWIKAR, I am looking for experiences in {name}."))}" target="_blank" rel="noopener noreferrer">Ask on WhatsApp ↗</a></div>'
                    f'<div class="kw-destination-lead-photo"><img src="{e(l.get("img") or "/assets/img/hero-dubai.webp")}" alt="Explore {e(name)}"></div></div></section>')
            page(f'/destinations/{lid}', heading, f'Ask KWIKAR about experiences in {name}.', main, active='Destinations', noindex=True,
                 main_class='kw-list-page kw-list-destination')
            continue
        img = (l.get('img') if l['group'] == 'uae' else None) or items[0].get('img') or '/assets/img/hero-dubai.webp'
        themes = list(dict.fromkeys(c for t in items for c in (t.get('cats') or []) if c))[:5]
        themes_html = ''
        if themes:
            themes_html = f'<div class="kw-market-wrap kw-destination-themes"><span>Popular themes in {e(name)}</span>' + ''.join(
                f'<a href="/search?destination={quote(lid)}&amp;q={quote(t_)}">{e(t_)} ↗</a>' for t_ in themes) + '</div>'
        others = [x for x in LOCATIONS if x['id'] != lid and x['group'] == l['group'] and x['id'] in LIVE_LOCS and x['id'] != 'other'][:3]
        rel = ''
        if others:
            rel = '<section class="kw-related-destinations"><div class="kw-market-wrap"><h2>Explore more destinations</h2><div>' + ''.join(
                f'<a href="/destinations/{x["id"]}"><strong>{e(x["name"])}</strong><span>See experiences ↗</span></a>' for x in others) + '</div></div></section>'
        main = (f'<section class="kw-destination-lead"><div class="kw-market-wrap kw-destination-lead-grid"><div class="kw-lead-copy"><nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/destinations">Destinations</a> / {e(crumb_label)}</nav>'
                f'<span class="kw-eyebrow">{"UNITED ARAB EMIRATES" if l["group"] == "uae" else "WORLDWIDE EXPERIENCES"}</span><h1>{e(heading)}</h1>'
                f'<p>Explore experiences in {e("the UAE" if lid == "other" else name)}, compare options and enquire for your preferred travel date.</p>'
                f'<a class="kw-lead-action" href="#kw-page-results">Browse {len(items)} experiences ↓</a>{list_search()}</div>'
                f'<div class="kw-destination-lead-photo"><img src="{e(img)}" alt="Explore {e(name)}"></div></div></section>'
                f'{themes_html}{list_body(items, location=lid, kind="destination")}'
                f'{hub_intro(f"dest:{lid}", "Experiences across the UAE" if lid == "other" else f"Visiting {name}", items, "" if lid == "other" else f" in {name}", eyebrow="GOOD TO KNOW")}{rel}')
        page(f'/destinations/{lid}', heading,
             f'{heading}: compare {len(items)} tours, attraction tickets and experiences with current prices. Book with KWIKAR on WhatsApp.', main,
             active='Destinations', main_class='kw-list-page kw-list-destination', main_attrs=f' data-listing data-kind="destination" data-location="{lid}"',
             crumbs=[('Home', '/'), ('Destinations', '/destinations'), (crumb_label, f'/destinations/{lid}')])


# ================================================================= tour pages (previous layout + SEO blocks)
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _plain(htmltext, n=None):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(htmltext or ''))).strip()
    return t[:n].rsplit(' ', 1)[0] + '…' if n and len(t) > n else t


def _num(h):
    h = float(h)
    return str(int(h)) if h.is_integer() else str(h)


def _opt_price(o):
    if not o.get('price'):
        return 'On request'
    s = f'From {money(o["price"])} / {o.get("unit") or "person"}'
    if o.get('tripFee') and o.get('adultBase'):
        s += f' + {money(o["tripFee"])} / booking'
    return s


def _customer_terms(v):
    v = re.sub(r'<li>[^<]*(?:credit\s*card|card|admin|booking)\s*(?:/|and|&)?\s*fees?[^<]*</li>', '', v or '', flags=re.I)
    return re.sub(r'<(?:ul|ol)>\s*</(?:ul|ol)>', '', v, flags=re.I)


def _free_cancel_hours(d):
    for r in d.get('cancellationRules') or []:
        try:
            if int(r.get('percents')) == 100 and int(r.get('hours')) > 0:
                return int(r['hours'])
        except Exception:
            pass
    for line in d.get('cancellation') or []:
        m = re.search(r'free cancellation[^.]*?(\d+)\s*hours?', line, re.I)
        if m:
            return int(m.group(1))
    return None


_TAIL_WORDS = {'and', 'or', 'of', 'the', 'with', 'in', 'at', 'on', 'for', 'to', 'from', 'by', 'new', '&', '+', '-', '–', 'a'}


def short_title(name, limit=51):
    """Shorten a long supplier name for the <title> (limit + ' | KWIKAR' <= 60) at a natural break."""
    if len(name) <= limit:
        return name
    n = re.sub(r'\s+(Theme Park|Tickets?|Experience)\b', '', name).strip()
    if len(n) <= limit:
        return n
    n = name
    cuts = []
    for sep in (' – ', ' - ', ' | ', ': ', ', ', ' (', ' with ', ' including ', ' at ', ' in ', ' from '):
        i = n.rfind(sep, 0, limit + 1)
        while i >= 20:
            c = n[:i].rstrip(' ,(-–')
            if c.count('(') == c.count(')'):
                cuts.append(c)
                break
            i = n.rfind(sep, 0, i)
    if cuts:
        return max(cuts, key=len)
    words = n[:limit + 1].rsplit(' ', 1)[0].split()
    while len(words) > 2 and words[-1].lower() in _TAIL_WORDS:
        words.pop()
    return ' '.join(words).rstrip(' ,(-–')


def build_product(t, d):
    tid = str(t['id'])
    x = EXTRAS.get(tid, {})
    path = tour_href(t)
    lid = t['loc'] if t['loc'] in {l['id'] for l in LOCATIONS} else 'other'
    cname = 'UAE' if lid == 'other' else loc_name(lid)
    name = d.get('name') or t['name']
    offers = d.get('offers') or []
    priced = [o for o in offers if o.get('price')]
    from_ = from_offers(t['id'], offers)
    cheapest = min(from_, key=lambda o: o['price']) if from_ else None
    low = cheapest['price'] if cheapest else t.get('price')
    high = max([o['price'] for o in priced] + ([low] if low else []), default=low)
    unit = (cheapest or t).get('unit')
    low_unit = {'trip': 'per booking', 'child': 'per child'}.get(unit, 'per person')
    if cheapest and cheapest.get('unit') == 'child':
        cheapest = next((o for o in priced if o.get('id') == cheapest.get('id')), cheapest)
    cats = d.get('categories') or t.get('cats') or []
    photos = [p for p in [d.get('img') or t.get('img')] + (d.get('photos') or []) if p][:4]
    cancel = [c for c in (d.get('cancellation') or []) if c]
    free_h = _free_cancel_hours(d)

    def fill(v):   # {from} = lowest current API price, so hand-written text never shows an old price
        if isinstance(v, str):
            return v.replace('{from}', money(low) if low else 'the price our team confirms')
        if isinstance(v, list):
            return [fill(i) for i in v]
        return v
    x = {k: fill(v) for k, v in x.items()}
    h1 = x.get('h1') or name

    # ---- SEO head
    title = x.get('title')
    if not title:
        title = f'{name} – From {money(low)} | KWIKAR' if low else f'{name} | KWIKAR'
        if len(title) > 60:
            title = f'{name} | KWIKAR'
        if len(title) > 60:
            title = short_title(name) + ' | KWIKAR'
    desc = x.get('description')
    if not desc:
        head_ = f'Book {name} in {cname}' + (f' from {money(low)} {low_unit}' if low else '') + '.'
        opts = []
        if len(offers) > 1:
            opts = [f' {len(offers)} options, including {offers[0]["name"]} and {offers[1]["name"]}.', f' {len(offers)} options, including {offers[0]["name"]}.', f' {len(offers)} options to choose from.']
        tails = (' Confirm availability and the final price with KWIKAR on WhatsApp.',
                 ' Send your date on WhatsApp and our team confirms availability and the final price.',
                 ' Book with KWIKAR on WhatsApp.', '')
        fits = [head_ + o_ + t_ for o_ in opts + [''] for t_ in tails if len(head_ + o_ + t_) <= 160]
        desc = next((c_ for c_ in fits if len(c_) >= 120), fits[0] if fits else head_[:157] + '…')

    # ---- quick answer + at a glance (facts from the API only)
    quick = x.get('quick_answer') or (
        f'You can book {name} in {cname} with KWIKAR' + (f' from {money(low)} {low_unit}' if low else '') + '. '
        + (f'There are {len(offers)} options to choose from. ' if len(offers) > 1 else '')
        + 'Send your preferred date and number of guests on WhatsApp; our team confirms availability and the final price before you pay.')
    glance = [('Location', cname)]
    hrs = sorted({float(o['hours']) for o in offers if o.get('hours')})
    if hrs:
        glance.append(('Duration', f'{_num(hrs[0])} hour{"s" if hrs[0] != 1 else ""}' if len(hrs) == 1 else f'{_num(hrs[0])}–{_num(hrs[-1])} hours'))
    if low:
        glance.append(('Price', f'From {money(low)} {low_unit}'))
    if len(offers) > 1:
        glance.append(('Options', f'{len(offers)} options'))
    if any(o.get('pickupRequired') for o in offers):
        glance.append(('Transfers', 'Hotel pickup available'))
    elif offers and all(o.get('transferKind') == 'meet_at_location' for o in offers):
        glance.append(('Getting there', 'Meet at the venue'))
    if any(o.get('child') for o in offers):
        glance.append(('Children', 'Child prices on some options'))
    days = set()
    for o in offers:
        days.update(o.get('daysOffered') or [])
    if days:
        glance.append(('Runs on', 'Every day' if len(days) >= 7 else ', '.join(dd[:3].title() for dd in DAYS if dd in days)))
    if free_h:
        glance.append(('Cancellation', f'Free up to {free_h} hours before'))
    over = {k: v for k, v in x.get('at_a_glance', [])}          # hand-checked facts replace the automatic ones
    glance = [(k, over.pop(k) if k in over else v) for k, v in glance if k not in x.get('glance_hide', [])]
    glance += [(k, v) for k, v in x.get('at_a_glance', []) if k in over]
    glance_html = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in glance)

    # ---- options: comparison table + which to choose + details (previous kw-offer cards)
    def transfer(o):
        return {'private': 'Private transfer', 'sharing': 'Sharing transfer', 'meet_at_location': 'Meet at location'}.get(o.get('transferKind'), '—')
    rows = ''.join(f'<tr><th scope="row">{e(o["name"])}</th><td>{e(_num(o["hours"]) + " h" if o.get("hours") else "—")}</td><td>{e(transfer(o))}</td><td>{e(_opt_price(o))}</td></tr>' for o in offers)
    choose = []
    if len(priced) >= 2:
        choose.append(('Lowest price' if cheapest['price'] == min(o['price'] for o in priced) else 'Entry ticket', cheapest['name'], _opt_price(cheapest)))
        tr = [o for o in priced if o.get('pickupRequired')]
        if tr and min(tr, key=lambda o: o['price']) is not cheapest:
            tc = min(tr, key=lambda o: o['price'])
            choose.append(('With hotel transfer', tc['name'], _opt_price(tc)))
        top_ = max(priced, key=lambda o: o['price'])
        if top_ is not cheapest:
            choose.append(('Most premium', top_['name'], _opt_price(top_)))

    def offer_card(o):
        meta = ' · '.join(x_ for x_ in [(f'{_num(o["hours"])} hour{"" if float(o["hours"]) == 1 else "s"}' if o.get('hours') else ''),
                                       (transfer(o) if transfer(o) != '—' else ''),
                                       (f'{_num(o["minPeople"])}–{_num(o["maxPeople"])} guests' if o.get('minPeople') is not None and o.get('maxPeople') is not None else '')] if x_)
        tr_ = ''
        if o.get('pickupRequired'):
            tr_ = f'<p>{"Private transfer" if o.get("transferKind") == "private" else "Sharing transfer" if o.get("transferKind") == "sharing" else "Transfer included"}{" · priced once per booking" if o.get("transferPricingMode") == "per_booking" else " · included in per-person price"}</p>'
        return (f'<details class="kw-offer-row"><summary><span><strong>{e(o["name"])}</strong><small>{e(meta)}</small></span><em>{e(_opt_price(o))}</em></summary>'
                f'<div>{tr_}{o.get("desc") or "<p>Our team shares the full details for this option on WhatsApp.</p>"}</div></details>')
    options_html = ''
    if offers:
        choose_html = ''
        if x.get('choose'):
            choose = [(k, v, None) for k, v in x['choose']]
        if choose:
            choose_html = ('<div class="kw-choose"><h3>Which should I choose?</h3><ul>' + ''.join(f'<li><strong>{e(k)}:</strong> {e(n_)}{f" <span>({e(p_)})</span>" if p_ else ""}</li>' for k, n_, p_ in choose)
                           + '</ul><p>Not sure? <a href="' + e(wa(f'Hi KWIKAR, which {name} option should I choose?')) + '" target="_blank" rel="noopener noreferrer">Ask our team on WhatsApp</a>.</p></div>')
        options_html = (f'<section class="kw-detail-block" id="options"><h2>Available options</h2>'
                        + (f'<p class="kw-offer-intro">Compare the {len(offers)} options. Tap an option to see what it includes.</p>' if len(offers) > 1 else '')
                        + '<div class="kw-offer-rows">' + ''.join(offer_card(o) for o in offers) + '</div>' + choose_html + '</section>')

    inc = ''
    if x.get('included') or x.get('not_included'):
        inc = ('<section class="kw-detail-block"><h2>What\'s included</h2><div class="kw-inc-grid">'
               + (f'<div><h3>Included</h3><ul class="kw-ticks">{"".join(f"<li>{e(i)}</li>" for i in x.get("included", []))}</ul></div>' if x.get('included') else '')
               + (f'<div><h3>Not included</h3><ul class="kw-crosses">{"".join(f"<li>{e(i)}</li>" for i in x.get("not_included", []))}</ul></div>' if x.get('not_included') else '')
               + '</div></section>')
    vis = ''
    if x.get('visitor_info'):
        vis = '<section class="kw-detail-block"><h2>Visitor information</h2>' + facts([(e(k), v) for k, v in x['visitor_info']]) + '</section>'
    best_for = (f'<h3 class="kw-sub">Best for</h3><ul class="kw-ticks">{"".join((f"<li><strong>{e(b[0])}:</strong> {e(b[1])}</li>" if isinstance(b, list) else f"<li>{e(b)}</li>") for b in x["best_for"])}</ul>') if x.get('best_for') else ''
    tip = f'<aside class="kw-tip"><strong>KWIKAR tip</strong><p>{e(x["tip"])}</p></aside>' if x.get('tip') else ''

    itin = d.get('itinerary') or []
    if x.get('steps'):
        how = f'<section class="kw-detail-block"><h2>{e(x.get("steps_title") or "How it works")}</h2><ol class="kw-steps">' + ''.join(f'<li><strong>{e(a)}</strong><p>{e(b)}</p></li>' for a, b in x['steps']) + '</ol></section>'
    elif itin:
        how = '<section class="kw-detail-block"><h2>Itinerary</h2>' + ''.join(f'<div class="kw-step"><strong>{e(s_["name"])}</strong><p>{e(s_.get("desc") or "")}</p></div>' for s_ in itin if s_.get('name')) + '</section>'
    else:
        how = ('<section class="kw-detail-block"><h2>How booking works</h2>'
               '<div class="kw-step"><strong>Choose your option and date</strong><p>Compare the options above and pick your preferred date.</p></div>'
               '<div class="kw-step"><strong>Send your request on WhatsApp</strong><p>Tap Check availability. Your request opens in WhatsApp for you to review and send.</p></div>'
               '<div class="kw-step"><strong>We confirm availability and price</strong><p>Our team checks with the supplier and replies with the final AED price.</p></div>'
               '<div class="kw-step"><strong>Pay and receive your confirmation</strong><p>Pay as agreed with our team and receive your booking details.</p></div></section>')

    api_faqs = [] if x.get('faqs_replace') else [(f['q'], f['a']) for f in (d.get('faq') or []) if f.get('q') and f.get('a')]
    faqs = api_faqs + [tuple(f) for f in x.get('faqs', [])]
    kfaqs = [('How do I book this with KWIKAR?', 'Tap Check availability, choose your date, guests and option, and send the request on WhatsApp. Our team checks availability with the supplier and replies with the final AED price before you pay.'),
             ('Are there booking or card fees?', 'No. The price our team confirms on WhatsApp is the total you pay. KWIKAR does not add a separate booking or card fee.'),
             ('Can I cancel or change my booking?', "Changes and refunds follow the supplier's rules for this experience, shown in the cancellation policy on this page. Contact us as soon as possible and we will check what applies to your booking.")]
    faq_html = f'<p class="kw-faq-note">{e(x["faq_note"])}</p>' if x.get('faq_note') else ''
    if faqs:
        faq_html += '<h3 class="kw-faq-group">About this experience</h3>' + faq_cards(faqs, open_all=False)
    faq_html += '<h3 class="kw-faq-group">Booking with KWIKAR</h3>' + faq_cards(kfaqs, open_all=False)

    safe_terms = ''.join(f'<p><strong>{e(k)}:</strong> {v}</p>' for k, v in x['terms']) if x.get('terms') else _customer_terms(d.get('terms'))
    cancel_html = f'<section class="kw-detail-block"><h2>Cancellation policy</h2>{"".join(f"<p>{e(_plain(c))}</p>" for c in cancel)}</section>' if cancel else ''
    terms_html = f'<section class="kw-detail-block"><h2>Terms</h2><div>{safe_terms}</div><p class="kw-terms-links">Also read our <a href="/booking-information">booking information</a> and <a href="/refund-policy">refund and cancellation policy</a>.</p></section>' if safe_terms else ''

    rel = [r for r in TOURS if r['id'] != t['id'] and r['loc'] == t['loc'] and set(r.get('cats') or []) & set(cats)]
    rel += [r for r in TOURS if r['id'] != t['id'] and r['loc'] == t['loc'] and r not in rel]
    rel = rel[:8]
    cat_links = ''.join(f'<a href="/activities/{c["slug"]}">{e(c["name"])}<span>↗</span></a>' for c in LIVE_CATS if tf.matches_category(t, c['slug'], c['term']))
    checked = x.get('last_checked')
    checked_txt = (f'Details checked by our team on {datetime.date.fromisoformat(checked).strftime("%-d %b %Y")}. ' if checked else '') + f'Prices and options from the supplier, last checked {CHECKED}.'
    meta = e(cname) + (f' · {" · ".join(e(c) for c in cats)}' if cats else '')
    badges = ''.join(f'<span>{e(b)}</span>' for b in x['badges']) if x.get('badges') else (f'<span>Free cancellation up to {free_h} hours before</span>' if free_h else '') + f'<span>{"Transfer options available" if any(o.get("pickupRequired") for o in offers) else "Meet at location"}</span><span>Book on WhatsApp</span>'
    alts = x.get('alts') or []
    pics = ''.join(f'<img src="{e(p)}" alt="{e(alts[i] if i < len(alts) else (name + ("" if i == 0 else f" image {i + 1}")))}"{" fetchpriority=high" if i == 0 else " loading=lazy"}>' for i, p in enumerate(photos))
    if x.get('subtitle'):
        meta = e(x['subtitle'])
    overview = ''.join(f'<p>{p_}</p>' for p_ in x['overview']) if x.get('overview') else (d.get('description') or '')

    def link_for(target):
        if target.startswith('search:'):
            hit = next((r for r in TOURS if r['name'].lower() == target[7:].lower()), None) or next((r for r in TOURS if target[7:].lower() in r['name'].lower()), None)
            return tour_href(hit) if hit else '/search?q=' + quote(target[7:])
        return target
    rel_links = ''
    if x.get('related_links'):
        rel_links = ('<section class="kw-detail-block kw-more-links"><h2>' + e(x.get('related_heading') or 'Related experiences') + '</h2><ul>'
                     + ''.join(f'<li><a href="{e(link_for(u))}">{e(a)}</a></li>' for a, u in x['related_links']) + '</ul></section>')
    cta_h = x.get('cta_heading') or f'Ready to book {name}?'
    cta_t = x.get('cta_text') or 'Send your date and guests. Our team replies on WhatsApp with availability and the final price.'
    wa_q = wa(f'Hi KWIKAR, I would like to book {name}. Please share availability.')
    sheet_data = {'id': t['id'], 'name': name, 'url': SITE + path, 'cancellation': [_plain(c) for c in cancel],
                  'offers': [{k: o.get(k) for k in ('name', 'hours', 'price', 'unit', 'child', 'tripFee', 'adultBase', 'minPeople', 'maxPeople', 'daysOffered', 'pricingPeriods', 'transferKind', 'transferPricingMode', 'pickupRequired', 'childrenAllowed')} for o in offers]}
    city_link = dest_href(lid)
    main = f'''<nav aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/activities">Activities</a> / <a href="{city_link}">{e("More" if lid == "other" else cname)}</a> / {e(name)}</nav>
<h1>{e(h1)}</h1>
<p class="kw-detail-meta">{meta}</p>
{f'<div class="kw-detail-photos">{pics}</div>' if photos else ''}
<div class="kw-product-badges">{badges}</div>
<div class="kw-detail-grid"><div>
<section class="kw-detail-block kw-quick" aria-label="Quick answer"><p>{e(quick)}</p><dl class="kw-facts kw-facts-2">{glance_html}</dl></section>
{f'<section class="kw-detail-block"><h2>Overview</h2><div>{overview}</div>{best_for}</section>' if overview or best_for else ''}
{tip}
{options_html}
{inc}{vis}
{how}
<section class="kw-detail-block" id="faq"><h2>Questions</h2>{faq_html}</section>
{cancel_html}
{terms_html}
{rel_links}
<p class="kw-checked">{e(checked_txt)}</p>
</div><aside><div class="kw-selection-card"><span>From</span><strong>{money(low) if low else "Price on request"}</strong><small>{(low_unit + " · no booking or card fees") if low else "Our team will confirm the price"}</small><button class="kw-button" type="button" data-book>Check availability</button><a href="tel:+{PHONE}">Need help? Call {PHONE_FMT}</a><p class="kw-seller">Booking handled by Kwikar LLC-FZ, United Arab Emirates.</p></div></aside></div>
{f'<section class="kw-detail-related"><div class="kw-section-head"><div><h2>More things to do in {e(cname)}</h2></div><div class="kw-section-actions"><a href="{city_link}" class="kw-text-link">View all <span aria-hidden="true">↗</span></a></div></div><div class="kw-list-grid">{"".join(list_card(r) for r in rel)}</div>{f"<div class=kw-related-cats>{cat_links}</div>" if cat_links else ""}</section>' if rel else ''}
<section class="kw-final-cta"><div><h2>{e(cta_h)}</h2><p>{e(cta_t)} Questions? <a href="{e(wa_q)}" target="_blank" rel="noopener noreferrer">WhatsApp us on {PHONE_FMT}</a>.</p></div><div><button class="kw-button" type="button" data-book>Check availability</button><a class="kw-final-wa" href="{e(wa_q)}" target="_blank" rel="noopener noreferrer">WhatsApp us ↗</a></div></section>
<div class="kw-product-sticky"><div><span>From</span><strong>{money(low) if low else "On request"}</strong>{f"<small>{low_unit}</small>" if low else ""}</div><button class="kw-button" type="button" data-book>Check availability</button></div>
<script type="application/json" id="kw-tour">{json.dumps(sheet_data, ensure_ascii=False).replace("</", "<\\/")}</script>'''

    product = {'@context': 'https://schema.org', '@type': 'Product', 'name': name, 'sku': tid, 'url': SITE + path,
               'description': _plain(overview or quick, 300), 'image': photos, 'category': (cats[0] if cats else 'Tours & activities'),
               'brand': {'@type': 'Brand', 'name': 'KWIKAR'}}
    if priced:
        product['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'AED', 'lowPrice': low, 'highPrice': high, 'offerCount': len(priced),
                             'availability': 'https://schema.org/InStock', 'url': SITE + path, 'seller': {'@id': SITE + '/#organization'}}
    lds = ld(product) + ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs + kfaqs]})
    page(path, title, desc, main, active='Cruises' if tf.matches_category(t, 'cruises', '') else 'Activities', full_title=True,
         og_image=photos[0] if photos and photos[0].startswith('https://') else '/assets/img/kwikar-share.webp',
         noindex=not tf.visible(t), head_extra=lds, og_title=x.get('og_title'), og_desc=x.get('og_description'), main_class='kw-wrap kw-detail kw-product-detail', main_attrs=' data-tour',
         crumbs=[('Home', '/'), ('Activities', '/activities'), ('More' if lid == 'other' else cname, city_link), (name, path)])


# Supplier text sometimes uses online-checkout wording that does not fit our WhatsApp flow (hard rule).
_SUPPLIER_FIXES = [
    (re.compile(r'\s*\bBook now\b[^.!?<]*[.!?]?', re.I), ''),
    (re.compile(r'\b(?:selected|chosen) during checkout\b', re.I), 'chosen when booking'),
    (re.compile(r'\b(?:during|at) (?:the )?checkout\b', re.I), 'when booking'),
    (re.compile(r'\binstant confirmation\b', re.I), 'confirmation from our team'),
    # "Upon purchase, you will instantly receive tickets" -> tickets come from our team after WhatsApp confirmation
    (re.compile(r'\b(?:Upon|After|Once)\s+(?:completing\s+)?(?:purchase|payment)(?:\s+is\s+complete)?,?\s+you will instantly receive (?:a |your )?tickets?\b', re.I),
     'After you pay, our team sends your tickets'),
]


def _clean_supplier(v):
    if isinstance(v, str):
        for rx, rep in _SUPPLIER_FIXES:
            v = rx.sub(rep, v)
        return v
    if isinstance(v, list):
        return [_clean_supplier(i) for i in v]
    if isinstance(v, dict):
        return {k: _clean_supplier(i) for k, i in v.items()}
    return v


def _fix_offer_hours(d, x):
    """tour-extras `offer_hours`: {part of an option name: hours, or null to hide} for clearly wrong supplier durations."""
    fixes = {k.lower(): v for k, v in (x.get('offer_hours') or {}).items()}
    if not fixes or not d.get('offers'):
        return d
    offers = []
    for o in d['offers']:
        for part, hrs in fixes.items():
            if part in (o.get('name') or '').lower():
                o = dict(o, hours=hrs or None)
        offers.append(o)
    return dict(d, offers=offers)


def build_products():
    for t in ALL_TOURS:
        d = DETAILS.get(t['id']) or DETAILS.get(str(t['id'])) or {}
        build_product(t, _fix_offer_hours(_clean_supplier(d), EXTRAS.get(str(t['id']), {})))


# ================================================================= service pages (same markup as before)
def build_holidays():
    countries = list(dict.fromkeys(h['country'] for h in HOLIDAYS))
    tiles = ''.join(f'<button type="button" data-country="{e(c)}"><img src="{e(next(h["img"] for h in HOLIDAYS if h["country"] == c))}" alt="" loading="lazy"><span>{e(c)}</span></button>' for c in countries)
    filt = ''.join(f'<button data-country="{e(c)}"{" class=selected" if c == "All" else ""}>{e(c)}</button>' for c in ['All'] + countries)
    groups = ''.join(f'<section class="kw-holiday-group" data-group="{e(c)}"><h2>{e(c)} holiday packages</h2><div class="kw-package-grid">' + ''.join(
        f'<article class="kw-package"><img src="{e(h["img"])}" alt="{e(h["country"])}" loading="lazy"><div><span class="kw-eyebrow">{e(h["country"])} · {h["nights"]} nights / {h["days"]} days</span><h3>{e(h["name"])}</h3>'
        f'<p>Get a tailored quote for your dates.</p><a href="{e(wa(f"Hi KWIKAR, please quote {h['name']} for my travel dates."))}" target="_blank" rel="noopener noreferrer">Request a quote ↗</a></div></article>'
        for h in HOLIDAYS if h['country'] == c) + '</div></section>' for c in countries)
    main = (page_hero('TAILORED GETAWAYS', 'Holidays designed around you.', 'Discover destinations and let us help put together the right hotel, activities and transfers for your journey.', photo('1525625293386-3f8f99389edd', 1600))
            + f'<section class="kw-section"><div class="kw-wrap" data-holidays>{section_head("Explore holiday ideas", "WHERE TO NEXT")}<p class="kw-section-intro">Holiday prices will be confirmed by our team for your dates and preferred hotels.</p>'
            f'<div class="kw-holiday-destinations" aria-label="Holiday destinations">{tiles}</div><div class="kw-filter-row">{filt}</div>{groups}</div></section>')
    page('/holidays', 'Holiday Packages', 'Holiday package ideas for the UAE, Singapore, Thailand and beyond. Tell us your dates and budget on WhatsApp and our team sends a tailored quote.', main,
         active='Holidays', main_class='kw-category-service kw-holiday-service', crumbs=[('Home', '/'), ('Holidays', '/holidays')])


TR_CLASSES = TR['classes']
TR_ROUTES = TR['routes']
TR_AIRPORTS = TR['airports']
TR_SET = TR['settings']
WAIT_A, WAIT_O, HOUR_MIN = TR_SET['wait_airport'], TR_SET['wait_other'], TR_SET['hourly_min']
HOURLY_PATH = '/transfers/' + TR['hourly']['slug']
DXB_DT = next(r for r in TR_ROUTES if r['id'] == 'dxb-downtown')['prices']['e']
INCLUDED_TXT = f'Salik and Darb tolls, airport parking, child seats and {WAIT_A} minutes of free waiting at airports ({WAIT_O} minutes elsewhere)'


def tr_href(r):
    return '/transfers/' + r['slug']


def cls_href(c):
    return '/transfers/vehicles/' + c['slug']


def ap_href(a):
    return '/transfers/' + a['slug']


def cls_img(c):
    car = next((x for x in CARS if x['name'] == c['car']), None)
    return car['img'] if car else '/assets/img/kwikar-share.webp'


def cls_cap(c):
    g = c['guests']
    return (f'{g} guests' if isinstance(g, str) else f'Up to {g} guests') + f' · {c["bags"]} bags'


def tr_low(prices):
    vals = [v for v in prices.values() if v]
    return min(vals) if vals else None


def tr_name(r):
    return f'{r["from"]} to {r["to"]}'


def tr_short_from(r):
    return re.sub(r' \((DXB|DWC|AUH|SHJ)\)$', '', r['from'])


# Estimator on /transfers: the same approved rates, by vehicle class
EST = {
    'vehicles': [c['name'] for c in TR_CLASSES],
    'airport': [{'name': f'{tr_short_from(r)} → {r["to"]}', 'from': r['from'], 'to': r['to'],
                 'rates': {c['name']: r['prices'].get(c['key']) for c in TR_CLASSES}} for r in TR_ROUTES if r['airport']],
    'intercity': [{'name': f'{r["from"]} → {r["to"]}', 'from': r['from'], 'to': r['to'],
                   'rates': {c['name']: r['prices'].get(c['key']) for c in TR_CLASSES}} for r in TR_ROUTES if not r['airport']],
    'hourly': {c['name']: TR['hourly']['prices'].get(c['key']) for c in TR_CLASSES},
}


def faq_block(title, items):
    return f'<section class="kw-section"><div class="kw-wrap kw-seo-narrow">{seo_head("FAQ", e(title), None, center=True)}{faq_cards(items, open_all=False)}</div></section>'


def tr_form(service='Airport transfer', pickup='', dropoff='', vehicle=None, wa_title='Transfer enquiry'):
    opts = ''.join(f'<option{" selected" if c["name"] == vehicle else ""}>{e(c["name"])}</option>' for c in TR_CLASSES)
    svc = ''.join(f'<option{" selected" if s == service else ""}>{s}</option>' for s in ('Airport transfer', 'Point to point', 'Hourly chauffeur'))
    return (f'<form class="kw-form" data-wa="{e(wa_title)}"><label>Service type<select name="service" data-label="Service" data-prefill="service">{svc}</select></label>'
            f'<label>Vehicle class<select name="vehicle" data-label="Vehicle class">{opts}</select></label>'
            f'<label>Pickup location<input required name="pickup" data-label="Pickup" value="{e(pickup)}" placeholder="Hotel, address or airport terminal"></label>'
            f'<label>Drop-off location<input required name="dropoff" data-label="Drop-off" value="{e(dropoff)}" placeholder="Hotel or address"></label>'
            f'<div class="kw-two-fields"><label>Date<input required type="date" name="date" data-label="Date"></label><label>Time<input required type="time" name="time" data-label="Time"></label></div>'
            f'<div class="kw-two-fields"><label>Passengers<input required type="number" min="1" value="1" name="pax" data-label="Passengers"></label><label>Your name<input required name="name" data-label="Name"></label></div>'
            f'<label>Flight number (airport pickups)<input name="flight" data-label="Flight number" placeholder="For example EK 202"></label>'
            f'<label>Child seats, extra stops or special requests<textarea name="special" data-label="Special requirements" placeholder="Child ages for seats, luggage, extra stops"></textarea></label>'
            f'<button class="kw-button" type="submit">Send enquiry on WhatsApp ↗</button></form>')


def tr_enquiry_section(title, text, **kw):
    return (f'<section id="transfer-enquiry" class="kw-section kw-market-alt"><div class="kw-wrap kw-service-layout"><div>{section_head(title, "YOUR RIDE")}'
            f'<p>{text}</p><h3>Included in the price</h3><p>{e(INCLUDED_TXT)}. The price is per vehicle, not per person. '
            f'Our team confirms the final price on WhatsApp before you pay. There is no online payment on the website.</p></div>{tr_form(**kw)}</div></section>')


def class_rows(prices, unit='one way', pick=True):
    """One row per vehicle class with photo, models, capacity and price (links fill the form)."""
    rows = ''
    for c in TR_CLASSES:
        p = prices.get(c['key'])
        rows += (f'<div class="kw-class-row"><img src="{e(cls_img(c))}" alt="{e(c["car"])}, {e(c["name"])} class" loading="lazy" width="160" height="100">'
                 f'<div><strong><a href="{cls_href(c)}">{e(c["name"])}</a></strong><small>{e(", ".join(c["models"]))} or similar</small><small>{e(cls_cap(c))}</small></div>'
                 f'<div class="kw-class-price"><em>{money(p) if p else "Quote on WhatsApp"}</em>{f"<small>{e(unit)}</small>" if p else ""}'
                 + (f'<a href="#transfer-enquiry" data-pick="{e(c["name"])}">Choose ↗</a>' if pick else '') + '</div></div>')
    return f'<div class="kw-class-rows">{rows}</div>'


def route_rows(routes, key=None):
    """Route list (price rows that link to each route page)."""
    out = ''
    for r in routes:
        p = r['prices'].get(key) if key else tr_low(r['prices'])
        out += (f'<a class="kw-price-row" href="{tr_href(r)}"><span><strong>{e(tr_short_from(r))} → {e(r["to"])}</strong><small>{e(r["info"])}</small></span>'
                f'<em>{("from " if not key else "") + money(p) if p else "Quote"}</em></a>')
    return f'<div class="kw-price-list">{out}</div>'


def tr_service_ld(name, path, desc, prices, service_type, area):
    offers = [{'@type': 'Offer', 'name': c['name'], 'price': prices[c['key']], 'priceCurrency': 'AED', 'url': SITE + path,
               'availability': 'https://schema.org/InStock', 'seller': {'@id': SITE + '/#organization'}} for c in TR_CLASSES if prices.get(c['key'])]
    return {'@context': 'https://schema.org', '@type': 'TaxiService', 'name': name, 'url': SITE + path, 'description': desc,
            'serviceType': service_type, 'provider': {'@id': SITE + '/#organization'}, 'areaServed': area,
            'offers': offers}


def faq_ld(items):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items]}


def fit(s, n):
    """Trim a description to at most n characters at a word boundary."""
    if len(s) <= n:
        return s
    return s[:n].rsplit(' ', 1)[0].rstrip(',;') + '.'


def tr_page(path, title, desc, h1, sub, body, aside_price, aside_unit, crumbs, lds, cta_text, active='Transfers'):
    nav = ' / '.join(f'<a href="{h}">{e(n)}</a>' for n, h in crumbs[:-1]) + f' / {e(crumbs[-1][0])}'
    main = (f'<nav aria-label="Breadcrumb">{nav}</nav><h1>{e(h1)}</h1><p class="kw-detail-meta">{e(sub)}</p>'
            f'<div class="kw-product-badges"><span>Price per vehicle</span><span>Tolls and parking included</span><span>Book on WhatsApp</span></div>'
            f'<div class="kw-detail-grid"><div>{body}</div>'
            f'<aside><div class="kw-selection-card"><span>From</span><strong>{money(aside_price) if aside_price else "Price on request"}</strong>'
            f'<small>{e(aside_unit)} · no booking or card fees</small><a class="kw-button" href="#transfer-enquiry">Request this transfer</a>'
            f'<a href="tel:+{PHONE}">Need help? Call {PHONE_FMT}</a><p class="kw-seller">Transfers arranged by Kwikar LLC-FZ, United Arab Emirates.</p></div></aside></div>'
            f'<section class="kw-final-cta"><div><h2>Book your ride</h2><p>{e(cta_text)} Questions? <a href="{e(wa("Hi KWIKAR, I have a transfer question."))}" target="_blank" rel="noopener noreferrer">WhatsApp us on {PHONE_FMT}</a>.</p></div>'
            f'<div><a class="kw-button" href="#transfer-enquiry">Request a quote</a></div></section>'
            f'<div class="kw-product-sticky"><div><span>From</span><strong>{money(aside_price) if aside_price else "On request"}</strong><small>{e(aside_unit)}</small></div><a class="kw-button" href="#transfer-enquiry">Request</a></div>')
    return main


def _how_steps(airport):
    meet = (f'Your chauffeur tracks your flight and waits in the arrivals hall with a name sign. The first {WAIT_A} minutes after landing are free.'
            if airport else f'Your chauffeur arrives at your pickup point at the agreed time. The first {WAIT_O} minutes of waiting are free.')
    return info_cards([('', 'Send your trip', 'Use the form or WhatsApp: pickup, drop-off, date, time, guests' + (' and flight number.' if airport else '.')),
                       ('', 'Get the final price', 'Our team confirms the vehicle class and the final AED price before you pay.'),
                       ('', 'Meet your chauffeur', meet),
                       ('', 'Ride direct', 'A private car only for your group, straight to your address. Tolls and parking are already in the price.')], numbered=True)


def build_transfer_route(r):
    path = tr_href(r)
    low = tr_low(r['prices'])
    frm, to = r['from'], r['to']
    sf = tr_short_from(r)
    ap = next((a for a in TR_AIRPORTS if a['code'] == r['airport']), None)
    km, mins = (r['info'].split(' · ') + [''])[:2]
    title = f'{sf} to {to} Transfer from {money(low)}'
    if len(title) > 60:
        title = f'{sf} to {to} Private Transfer'
    if len(title) > 60:
        title = f'{sf} to {to} Transfer'
    if len(title) > 60:
        title = f'{sf} to {to.split(" and ")[0]} Transfer'
    desc = fit(f'Private {sf} to {to} transfer from {money(low)} per car. Tolls, parking, child seats and free waiting included. '
               f'Choose your vehicle class and book on WhatsApp.', 160)
    h1 = f'{sf} to {to} Transfer'
    sub = f'Private chauffeur transfer · {km} · {mins}'
    e_p, v_p = r['prices'].get('e'), r['prices'].get('v')
    quick = (f'A private transfer from {frm} to {to} costs from {money(low)} per car with KWIKAR (Business Sedan, up to 3 guests)'
             + (f' and {money(v_p)} for a Business Van for up to 7 guests' if v_p else '') + f'. The drive takes {mins} in normal traffic. '
             + ('Your chauffeur meets you in arrivals with a name sign. ' if ap else '') + 'Tolls and parking are included.')
    glance = facts([('Distance', e(km.replace('about ', 'About '))), ('Journey time', e(mins) + ' in normal traffic'),
                    ('Price', f'From {money(low)} per vehicle, one way'), ('Free waiting', f'{WAIT_A if ap else WAIT_O} minutes' + (' after landing' if ap else '')),
                    ('Included', 'Salik and Darb tolls, parking, child seats'), ('Return trip', 'Same price in the other direction')])
    cover = (f'<p>We pick you up {"at " + ap["name"] if ap else "anywhere in " + frm} and drive you to {r["areas"]}. '
             f'The same route also runs the other way, from {to} to {sf}, at the same price.</p>')
    others = [x for x in TR_ROUTES if x['id'] != r['id'] and (x['airport'] == r['airport'] if r['airport'] else not x['airport'])][:6]
    to_same = [x for x in TR_ROUTES if x['id'] != r['id'] and x['to'] == to and x not in others][:3]
    faqs = [
        (f'How much is a private transfer from {sf} to {to}?',
         f'From {money(low)} per car in a Business Sedan (up to 3 guests). '
         + '; '.join(f'{c["name"]} {money(r["prices"][c["key"]])}' for c in TR_CLASSES[1:] if r['prices'].get(c['key']))
         + f'. Prices are per vehicle, one way, and include {INCLUDED_TXT}.'),
        (f'How long does the drive from {sf} to {to} take?',
         f'About {mins.replace("about ", "")} in normal traffic ({km.replace("about ", "about ")}). Allow extra time in the morning and evening rush hours.'),
        (('Where will the driver meet me at the airport?', f'{ap["note"]} The driver follows your flight, so a delay does not cost you extra; the first {WAIT_A} minutes after landing are free.')
         if ap else (f'Can you pick me up from my hotel or home in {frm}?', f'Yes. We pick you up from any address, hotel or mall in {frm} and drop you at your address in {to}.')),
        ('Is the price per person?', 'No. The price is for the whole car, one way. A Business Sedan takes up to 3 guests, a Family SUV up to 6 and a Business Van up to 7.'),
        ('Which vehicle should I choose for a family with luggage?',
         f'For 4 to 6 guests with suitcases, the Family SUV ({money(r["prices"]["f"]) if r["prices"].get("f") else "on request"}) is the best value. '
         f'For 7 guests or a lot of luggage, choose the Business Van ({money(v_p) if v_p else "on request"}).'),
        ('Are child seats included?', 'Yes, child seats are free. Tell us the age of each child when you book so the right seats are fitted.'),
        (f'Can I book the return trip from {to} to {sf}?', 'Yes. The return trip costs the same. Send both dates and times in one message and our team confirms both rides.'),
        ('How do I pay?', 'You send your request on WhatsApp or with the form. Our team confirms the vehicle and the final price before you pay. There is no online payment on this website.'),
    ]
    body = (f'<section class="kw-detail-block kw-quick" aria-label="Quick answer"><p>{e(quick)}</p>{glance}</section>'
            f'<section class="kw-detail-block"><h2>Prices by vehicle class</h2><p>Every price is for the whole car, one way. Pick a class and our team sends the car from that class that is free at your time.</p>'
            f'{class_rows(r["prices"])}</section>'
            f'<section class="kw-detail-block"><h2>Where we drive</h2>{cover}</section>'
            f'<section class="kw-detail-block"><h2>How it works</h2>{_how_steps(bool(ap))}</section>'
            f'<section class="kw-detail-block" id="faq"><h2>Questions</h2>{faq_cards(faqs, open_all=False)}</section>'
            + (f'<section class="kw-detail-block"><h2>{"More transfers from " + ap["short"] if ap else "More city-to-city transfers"}</h2>{route_rows(others)}</section>' if others else '')
            + (f'<section class="kw-detail-block"><h2>Other ways to {e(to)}</h2>{route_rows(to_same)}</section>' if to_same else '')
            + f'<p class="kw-checked">Prices from the KWIKAR transfer rate card, updated {datetime.date.fromisoformat(TR["approved"]).strftime("%-d %b %Y")}.</p>')
    crumbs = [('Home', '/'), ('Transfers', '/transfers')] + ([(ap['short'], ap_href(ap))] if ap else []) + [(h1, path)]
    main = tr_page(path, title, desc, h1, sub, body, low, 'per car, one way', crumbs, None,
                   'Send pickup, drop-off, date, time and guests. Our team replies on WhatsApp with the final price.')
    main += tr_enquiry_section(f'Request your {sf} to {to} transfer', 'Tell us your date, time and number of guests. We reply on WhatsApp with the final price.',
                               service='Airport transfer' if ap else 'Point to point', pickup=frm, dropoff=to, wa_title=f'Transfer enquiry: {sf} to {to}')
    lds = (ld(tr_service_ld(h1, path, desc, r['prices'], 'Airport transfer' if ap else 'Private transfer', [frm, to])) + ld(faq_ld(faqs)))
    page(path, title, desc, main, active='Transfers', full_title=True, head_extra=lds, crumbs=crumbs, main_class='kw-wrap kw-detail kw-transfer-detail',
         og_image=cls_img(TR_CLASSES[0]) if cls_img(TR_CLASSES[0]).startswith('http') else '/assets/img/kwikar-share.webp')


def build_transfer_airport(a):
    path = ap_href(a)
    rs = [r for r in TR_ROUTES if r['airport'] == a['code']]
    low = min(tr_low(r['prices']) for r in rs)
    title = f'{a["short"]} Transfers ({a["code"]}) from {money(low)}'
    desc = fit(f'Private transfers from {a["name"]} to {", ".join(r["to"] for r in rs[:4])} and more. From {money(low)} per car, tolls and parking included.', 160)
    h1 = f'{a["short"]} ({a["code"]}) Transfers'
    quick = (f'KWIKAR runs private transfers from {a["name"]} to {len(rs)} popular areas, from {money(low)} per car. '
             f'Your chauffeur tracks your flight, meets you in arrivals with a name sign and waits {WAIT_A} minutes for free after landing.')
    faqs = [(f'How much is a transfer from {a["short"]}?', f'From {money(low)} per car. ' + '; '.join(f'{r["to"]} from {money(tr_low(r["prices"]))}' for r in rs) + '. Prices are per vehicle, one way.'),
            ('Where will my driver wait?', a['note'] + f' The first {WAIT_A} minutes after landing are free.'),
            ('What if my flight is late?', 'Share your flight number when you book. The driver follows the flight and adjusts the pickup time, so a delay does not cost you extra.'),
            ('Can I book a transfer to the airport too?', f'Yes. Every route on this page also runs to {a["short"]} at the same price.'),
            ('Which car is best for a family?', 'Choose the Family SUV for 4 to 6 guests with luggage, or the Business Van for up to 7 guests.')]
    body = (f'<section class="kw-detail-block kw-quick" aria-label="Quick answer"><p>{e(quick)}</p>'
            + facts([('Airport', e(a['name'])), ('Meeting point', 'Arrivals hall, name sign'), ('Free waiting', f'{WAIT_A} minutes after landing'), ('Included', 'Tolls, parking, child seats')]) + '</section>'
            f'<section class="kw-detail-block"><h2>Transfers from {e(a["short"])}</h2><p>Prices from, per car, one way. Open a route for prices by vehicle class.</p>{route_rows(rs)}</section>'
            f'<section class="kw-detail-block"><h2>Vehicle classes</h2>{class_rows({c["key"]: min(r["prices"][c["key"]] for r in rs if r["prices"].get(c["key"])) for c in TR_CLASSES}, unit="from, one way")}</section>'
            f'<section class="kw-detail-block"><h2>How it works</h2>{_how_steps(True)}</section>'
            f'<section class="kw-detail-block" id="faq"><h2>Questions</h2>{faq_cards(faqs, open_all=False)}</section>')
    crumbs = [('Home', '/'), ('Transfers', '/transfers'), (a['short'], path)]
    main = tr_page(path, title, desc, h1, f'Private airport transfers · {a["city"]}', body, low, 'per car, one way', crumbs, None,
                   'Send your flight, drop-off address and guests. Our team replies on WhatsApp with the final price.')
    main += tr_enquiry_section(f'Request your {a["short"]} transfer', 'Tell us your flight number, drop-off address and number of guests.',
                               service='Airport transfer', pickup=a['name'], wa_title=f'Transfer enquiry: {a["short"]}')
    page(path, title, desc, main, active='Transfers', full_title=True, crumbs=crumbs, main_class='kw-wrap kw-detail kw-transfer-detail',
         head_extra=ld(tr_service_ld(h1, path, desc, {c['key']: min(r['prices'][c['key']] for r in rs if r['prices'].get(c['key'])) for c in TR_CLASSES}, 'Airport transfer', a['city'])) + ld(faq_ld(faqs)))


def build_transfer_class(c):
    path = cls_href(c)
    k = c['key']
    rs = [r for r in TR_ROUTES if r['prices'].get(k)]
    low = min(r['prices'][k] for r in rs)
    hour = TR['hourly']['prices'].get(k)
    models = ', '.join(c['models'])
    title = f'{c["name"]} Chauffeur in Dubai: {c["models"][0]} or Similar'
    if len(title) > 60:
        title = f'{c["name"]} Chauffeur Dubai: {c["models"][0]}'
    if len(title) > 60:
        title = f'{c["name"]} Chauffeur Service in Dubai'
    desc = fit(f'Book a {c["name"]} with chauffeur in the UAE: {models} or similar. {cls_cap(c)}. Transfers from {money(low)}, hourly from {money(hour)}.', 160)
    h1 = f'{c["name"]} with Chauffeur'
    fleet = [x for x in CARS if x['name'] in c['models'] or any(x['name'].startswith(m) for m in c['models'])]
    pics = ''.join(f'<figure class="kw-class-fig"><img src="{e(x["img"])}" alt="{e(x["name"])}" loading="lazy" width="320" height="200"><figcaption>{e(x["name"])}</figcaption></figure>' for x in fleet)
    quick = (f'The {c["name"]} class is a {models} or a similar car with a professional chauffeur. It takes {cls_cap(c).lower()}. '
             f'{c["best"]} Airport transfers start at {money(low)} per car and hourly bookings at {money(hour)} per hour (minimum {HOUR_MIN} hours).')
    faqs = [(f'Which cars are in the {c["name"]} class?', f'{models}, or a similar car of the same standard. You book the class; our team sends the car from that class that is free at your time.'),
            (f'How many people fit in a {c["name"]}?', f'{cls_cap(c)}. Tell us your luggage when you book and we confirm the right car.'),
            (f'Can I book a {c["name"]} by the hour?', f'Yes, from {money(hour)} per hour with a minimum of {HOUR_MIN} hours. See chauffeur service by the hour.'),
            ('What is included?', f'The chauffeur, fuel, {INCLUDED_TXT}.'),
            ('Can I ask for a specific model?', 'Write the model you prefer in your request. We confirm it when it is free; otherwise we offer another car of the same class.')]
    body = (f'<section class="kw-detail-block kw-quick" aria-label="Quick answer"><p>{e(quick)}</p>'
            + facts([('Cars', e(models) + ' or similar'), ('Capacity', e(cls_cap(c))), ('Transfers', f'From {money(low)} per car'), ('By the hour', f'{money(hour)} per hour, {HOUR_MIN} hours minimum')]) + '</section>'
            + (f'<section class="kw-detail-block"><h2>Cars in this class</h2><div class="kw-class-figs">{pics}</div><p><a class="kw-text-link" href="/transfers/fleet">See the full fleet ↗</a> <span class="kw-photo-note">Example photos. <a href="/transfers/fleet#photo-credits">Photo credits</a></span></p></section>' if pics else '')
            + f'<section class="kw-detail-block"><h2>{e(c["name"])} transfer prices</h2><p>Per car, one way. Open a route for details.</p>{route_rows(rs, key=k)}</section>'
            f'<section class="kw-detail-block"><h2>Other vehicle classes</h2><div class="kw-chip-links">'
            + ''.join(f'<a href="{cls_href(o)}">{e(o["name"])}<span>↗</span></a>' for o in TR_CLASSES if o is not c) + '</div></section>'
            f'<section class="kw-detail-block" id="faq"><h2>Questions</h2>{faq_cards(faqs, open_all=False)}</section>')
    crumbs = [('Home', '/'), ('Transfers', '/transfers'), (c['name'], path)]
    main = tr_page(path, title, desc, h1, f'{models} or similar · {cls_cap(c)}', body, low, 'per car, one way', crumbs, None,
                   f'Tell us your route, date and guests for a {c["name"]}. Our team replies on WhatsApp with the final price.')
    main += tr_enquiry_section(f'Request a {c["name"]}', 'Tell us your route or the hours you need.', vehicle=c['name'], wa_title=f'Transfer enquiry: {c["name"]}')
    offers = {kk: None for kk in ('e', 'f', 's', 'v', 'x')}
    offers[k] = low
    page(path, title, desc, main, active='Transfers', full_title=True, crumbs=crumbs, main_class='kw-wrap kw-detail kw-transfer-detail',
         og_image=cls_img(c) if cls_img(c).startswith('http') else '/assets/img/kwikar-share.webp',
         head_extra=ld(tr_service_ld(h1, path, desc, offers, 'Chauffeur service', 'United Arab Emirates')) + ld(faq_ld(faqs)))


def build_transfer_hourly():
    path = HOURLY_PATH
    hp = TR['hourly']['prices']
    low = tr_low(hp)
    title = f'Chauffeur Service Dubai by the Hour from {money(low)}'
    desc = fit(f'Hire a car with a chauffeur in Dubai by the hour: from {money(low)} per hour, minimum {HOUR_MIN} hours. Business Sedan to Luxury SUV. Book on WhatsApp.', 160)
    h1 = 'Chauffeur Service in Dubai by the Hour'
    quick = (f'Hire a private car with a chauffeur in Dubai from {money(low)} per hour (Business Sedan), with a minimum of {HOUR_MIN} hours. '
             f'The car stays with you for meetings, shopping, sightseeing or several stops. Fuel, tolls and parking are included.')
    uses = info_cards([('', 'Business days', 'Meetings across Dubai with one car and driver waiting between stops.'),
                       ('', 'Shopping and malls', 'Dubai Mall, Mall of the Emirates and souks, with room for your bags.'),
                       ('', 'Sightseeing', 'Build your own city tour at your pace: Burj Khalifa, Dubai Frame, the Creek and the beach.'),
                       ('', 'Events and evenings', 'Weddings, dinners and events, with the car ready when you are.')])
    faqs = [('How much is a chauffeur per hour in Dubai?', 'From ' + '; '.join(f'{c["name"]} {money(hp[c["key"]])}' for c in TR_CLASSES if hp.get(c['key'])) + ' per hour.'),
            ('Is there a minimum booking?', f'Yes, {HOUR_MIN} hours. Longer bookings are welcome; tell us your plan and we confirm the price.'),
            ('Can I go to other emirates?', 'Hourly bookings are for driving within Dubai. For trips to Abu Dhabi, Sharjah or other emirates, see our city-to-city transfers or ask for a full-day quote.'),
            ('What is included?', f'The chauffeur, fuel, Salik tolls, parking and child seats.'),
            ('Can I extend on the day?', 'Usually yes, if the chauffeur is free. Extra hours are charged at the same hourly rate.')]
    body = (f'<section class="kw-detail-block kw-quick" aria-label="Quick answer"><p>{e(quick)}</p>'
            + facts([('Price', f'From {money(low)} per hour'), ('Minimum', f'{HOUR_MIN} hours'), ('Area', 'Within Dubai'), ('Included', 'Fuel, tolls, parking, child seats')]) + '</section>'
            f'<section class="kw-detail-block"><h2>Hourly prices by vehicle class</h2>{class_rows(hp, unit="per hour")}</section>'
            f'<section class="kw-detail-block"><h2>Popular uses</h2>{uses}</section>'
            f'<section class="kw-detail-block" id="faq"><h2>Questions</h2>{faq_cards(faqs, open_all=False)}</section>'
            f'<section class="kw-detail-block"><h2>Going further?</h2>{route_rows([r for r in TR_ROUTES if not r["airport"]])}</section>')
    crumbs = [('Home', '/'), ('Transfers', '/transfers'), ('Chauffeur by the hour', path)]
    main = tr_page(path, title, desc, h1, f'Private car with driver · minimum {HOUR_MIN} hours', body, low, 'per hour', crumbs, None,
                   'Send the date, start time, hours and plan. Our team replies on WhatsApp with the final price.')
    main += tr_enquiry_section('Request a chauffeur by the hour', 'Tell us the date, start time, number of hours and your plan.', service='Hourly chauffeur', wa_title='Hourly chauffeur enquiry')
    page(path, title, desc, main, active='Transfers', full_title=True, crumbs=crumbs, main_class='kw-wrap kw-detail kw-transfer-detail',
         head_extra=ld(tr_service_ld(h1, path, desc, hp, 'Chauffeur service by the hour', 'Dubai')) + ld(faq_ld(faqs)))


def build_transfers():
    tabs = ''.join(f'<button type="button" data-service="{v}" class="{"selected" if v == "airport" else ""}" aria-pressed="{"true" if v == "airport" else "false"}">{l_}</button>'
                   for v, l_ in (('airport', 'Airport transfer'), ('hourly', 'Hourly chauffeur'), ('intercity', 'City to city')))
    routes = ''.join(f'<option value="{i}">{e(r["name"])}</option>' for i, r in enumerate(EST['airport']))
    veh = ''.join(f'<option>{v}</option>' for v in EST['vehicles'])
    r0 = EST['airport'][0]
    estimator = (f'<section class="kw-section kw-transfer-estimator" data-estimator=\'{e(json.dumps(EST))}\'><div class="kw-wrap"><div class="kw-estimate-head"><div><span class="kw-eyebrow">PRICE CHECK</span><h2>Estimate your transfer</h2>'
                 f'<p>Select a route and vehicle class to see the price per car. Our team confirms your booking and the final price on WhatsApp. No online payment.</p></div></div>'
                 f'<div class="kw-estimate-grid"><div><div class="kw-estimate-tabs" role="group" aria-label="Transfer service">{tabs}</div>'
                 f'<label class="kw-estimate-field" data-route-field>Route<select name="route">{routes}</select></label>'
                 f'<label class="kw-estimate-field" data-hours-field hidden>Hours (minimum {HOUR_MIN})<input type="number" name="hours" min="{HOUR_MIN}" max="12" value="{HOUR_MIN}"></label>'
                 f'<label class="kw-estimate-field">Vehicle class<select name="vehicle">{veh}</select></label></div>'
                 f'<div class="kw-estimate-result"><span>PRICE PER CAR</span><strong data-out>{money(r0["rates"][EST["vehicles"][0]])}</strong><p data-sel>{e(r0["name"])} · {EST["vehicles"][0]}</p>'
                 f'<p>Includes {e(INCLUDED_TXT)}. Other addresses and extra stops are quoted by our team.</p>'
                 f'<a href="#transfer-enquiry" data-request>Request this transfer →</a></div></div></div></section>')
    groups = []
    for a in TR_AIRPORTS:
        rs = [r for r in TR_ROUTES if r['airport'] == a['code']]
        groups.append((a['name'], ap_href(a), rs))
    groups.append(('City to city', None, [r for r in TR_ROUTES if not r['airport']]))
    routes_html = ''.join(f'<div class="kw-route-group"><h3>{e(n)}{f" <a href={h} class=kw-text-link>All {e(n.split(" (")[0])} transfers ↗</a>" if h else ""}</h3>{route_rows(rs)}</div>' for n, h, rs in groups)
    class_cards = ''.join(f'<a class="kw-package kw-car" href="{cls_href(c)}"><img src="{e(cls_img(c))}" alt="{e(c["car"])}" loading="lazy"><div><span class="kw-eyebrow">{e(cls_cap(c))}</span>'
                          f'<h3>{e(c["name"])}</h3><p>{e(", ".join(c["models"]))} or similar. {e(c["best"])}</p><span class="kw-text-link">From {money(min(r["prices"][c["key"]] for r in TR_ROUTES if r["prices"].get(c["key"])))} ↗</span></div></a>' for c in TR_CLASSES)
    faqs = [('How much is a private transfer from Dubai Airport?', f'From {money(min(tr_low(r["prices"]) for r in TR_ROUTES if r["airport"] == "DXB"))} per car to Deira and Bur Dubai, and from {money(next(tr_low(r["prices"]) for r in TR_ROUTES if r["id"] == "dxb-downtown"))} to Downtown Dubai. See every route above.'),
            ('Is the price per person or per car?', 'Per car, one way. A Business Sedan takes up to 3 guests, a Family SUV up to 6 and a Business Van up to 7.'),
            ('What is included in the price?', INCLUDED_TXT + '.'),
            ('What happens if my flight is delayed?', f'Share your flight number when you book. The driver follows the flight; the first {WAIT_A} minutes after landing are free.'),
            ('Do I get the exact car model?', 'You book a vehicle class. Our team sends the car from that class that is free at your time, for example a Mercedes E-Class or a Lexus ES for a Business Sedan.'),
            ('Can I change or cancel a booking?', 'Tell us as soon as possible. We confirm the change and cancellation terms for your ride before you pay.')]
    ftabs, fcards, _ = fleet_cards()
    class_chips = ''.join(f'<a href="{cls_href(c)}">{e(c["name"])} · from {money(class_low(c))}<span>↗</span></a>' for c in TR_CLASSES)
    main = (page_hero('PRIVATE TRANSFERS', 'Airport transfers and chauffeur service across the UAE.', 'Fixed prices per car from Dubai, Abu Dhabi and Sharjah airports, between emirates and by the hour. Tolls and parking included.', photo('1518684079-3c830dcef090', 1600),
                      extra='<a class="kw-button" href="#fleet">See our fleet ↓</a>')
            + f'<section class="kw-section kw-fleet-section" id="fleet"><div class="kw-wrap">{section_head("Our fleet", "CHOOSE YOUR CAR", action=("Full fleet page", FLEET_PATH), carousel_id="kw-fleet-row")}'
            + f'<p class="kw-section-intro">{len(CARS)} chauffeur-driven cars. Pick the car you like and send your trip; prices are per car and include tolls and parking.</p>'
            + f'<div class="kw-filter-row kw-fleet-tabs" role="group" aria-label="Filter the fleet">{ftabs}</div><div class="kw-fleet-row" id="kw-fleet-row">{fcards}</div>'
            + f'<p class="kw-photo-note">Example photos of each model. <a href="{FLEET_PATH}#photo-credits">Photo credits</a></p>'
            + f'<h3 class="kw-fleet-classes-h">Prices by vehicle class</h3><div class="kw-chip-links">{class_chips}</div></div></section>'
            + estimator
            + f'<section class="kw-section"><div class="kw-wrap">{section_head("Popular transfer routes", "PRICES PER CAR")}<p class="kw-section-intro">Starting prices for a Business Sedan, one way. Open a route to see every vehicle class.</p>{routes_html}'
            + f'<div class="kw-route-group"><h3>By the hour</h3><div class="kw-price-list"><a class="kw-price-row" href="{HOURLY_PATH}"><span><strong>Chauffeur service in Dubai</strong><small>minimum {HOUR_MIN} hours</small></span><em>from {money(tr_low(TR["hourly"]["prices"]))}/hour</em></a></div></div></div></section>'
            + f'<section class="kw-section"><div class="kw-wrap">{seo_head("INCLUDED", "What every price includes")}'
            + info_cards([('', 'Tolls and parking', 'Salik and Darb road tolls and airport parking are in the price.'),
                          ('', 'Free waiting', f'{WAIT_A} minutes after your flight lands, {WAIT_O} minutes at other pickups.'),
                          ('', 'Child seats', 'Free on request. Tell us the age of each child.'),
                          ('', 'Flight tracking', 'Your driver follows your flight and adjusts the pickup time.')]) + '</div></section>'
            + tr_enquiry_section('Request a transfer quote', 'Tell us your route and any extras. Our team sends the final AED price before you pay.')
            + faq_block('Transfer questions', faqs))
    page('/transfers', 'Dubai Airport Transfers & Chauffeur Service', 'Private airport transfers in Dubai, Abu Dhabi and Sharjah, city-to-city rides and hourly chauffeur. Fixed prices per car, tolls and parking included.', main,
         active='Transfers', crumbs=[('Home', '/'), ('Transfers', '/transfers')], head_extra=ld(faq_ld(faqs)))
    for r in TR_ROUTES:
        build_transfer_route(r)
    for a in TR_AIRPORTS:
        build_transfer_airport(a)
    for c in TR_CLASSES:
        build_transfer_class(c)
    build_transfer_hourly()
    build_fleet()


FLEET_PATH = '/transfers/fleet'
try:
    FLEET_CREDITS = json.load(open(os.path.join(ROOT, 'data', 'fleet-credits.json'), encoding='utf-8'))
except OSError:
    FLEET_CREDITS = {}


def fleet_credits_html():
    if not FLEET_CREDITS:
        return ''
    names = {re.sub(r'[^a-z0-9]+', '-', c['name'].lower()).strip('-'): c['name'] for c in CARS}
    items = ''.join(f'<li>{e(names.get(k, k))}: photo by {e(v["artist"] or "unknown")}, '
                    f'<a href="{e(v["page"])}" target="_blank" rel="noopener">Wikimedia Commons</a>, '
                    + (f'<a href="{e(v["license_url"])}" target="_blank" rel="noopener">{e(v["license"])}</a>' if v.get('license_url') else e(v['license'])) + '</li>'
                    for k, v in FLEET_CREDITS.items())
    return (f'<section class="kw-section kw-photo-credits" id="photo-credits"><div class="kw-wrap"><h2>Photo credits</h2>'
            f'<p>Car photos are example photos of each model from Wikimedia Commons, used under their free licences. We removed the backgrounds and hid the number plates; '
            f'the edited photos are shared under the same licence. The car sent for your booking may differ in colour and details.</p><ul>{items}</ul></div></section>')
CAR_INFO = {   # one line per car and the filter groups it belongs to
    'Mercedes E-Class': ('Business sedan for airport runs and city meetings.', ['sedan']),
    'Lexus ES 300h': ('Quiet hybrid business sedan.', ['sedan', 'electric']),
    'BMW 530i': ('Executive sedan with a smooth, quiet ride.', ['sedan']),
    'BYD Han Flagship': ('Electric flagship sedan with no tailpipe emissions.', ['sedan', 'electric']),
    'Tesla Model Y': ('Electric SUV with a large boot.', ['suv', 'electric']),
    'BYD Song+ Flagship': ('Electric SUV for small families.', ['suv', 'electric']),
    'Exeed VX Flagship': ('Spacious premium SUV for families with luggage.', ['suv']),
    'BMW 7 Series': ('Flagship sedan for VIP guests.', ['sedan', 'luxury']),
    'Mercedes S-Class': ('The classic luxury sedan for executives and special days.', ['sedan', 'luxury']),
    'Mercedes V-Class': ('Business van for families and groups of up to seven.', ['van']),
    'GMC Yukon XL': ('Full-size SUV with room for seven and their bags.', ['suv', 'luxury']),
    'Cadillac Escalade': ('Luxury SUV for VIP arrivals and long trips.', ['suv', 'luxury']),
}
FLEET_TABS = [('all', 'All'), ('sedan', 'Sedan'), ('suv', 'SUV'), ('van', 'Van'), ('electric', 'Electric & hybrid'), ('luxury', 'Luxury')]


def car_class(car):
    return next((c for c in TR_CLASSES if car['name'] in c['models'] or any(car['name'].startswith(m) for m in c['models'])), None)


def class_low(c):
    return min(r['prices'][c['key']] for r in TR_ROUTES if r['prices'].get(c['key']))


def fleet_cards():
    order = [c['key'] for c in TR_CLASSES]
    cars = sorted(CARS, key=lambda x: (order.index(car_class(x)['key']) if car_class(x) else 9))
    tabs = ''.join(f'<button type="button" data-fleet-tab="{k}"{" class=selected aria-pressed=true" if k == "all" else " aria-pressed=false"}>{e(n)}</button>' for k, n in FLEET_TABS)
    cards = ''
    for x in cars:
        c = car_class(x)
        line, tags = CAR_INFO.get(x['name'], ('', []))
        hour = TR['hourly']['prices'].get(c['key']) if c else None
        cards += (f'<article class="kw-fleet-card" data-tags="{" ".join(tags)}"><div class="kw-fleet-photo"><img src="{e(x["img"])}" alt="{e(x["name"])}" loading="lazy" width="600" height="375"></div>'
                  f'<div class="kw-fleet-body"><span class="kw-eyebrow">{e(c["name"]) if c else e(x["type"])}</span><h3>{e(x["name"])}</h3><p>{e(line)}</p>'
                  f'<p class="kw-fleet-cap">Up to {x["pax"]} guests · {c["bags"] if c else "–"} bags</p>'
                  f'<dl class="kw-fleet-prices"><div><dt>From / trip</dt><dd>{money(class_low(c)) if c else "On request"}</dd></div><div><dt>From / hour</dt><dd>{money(hour) if hour else "On request"}</dd></div></dl>'
                  f'<div class="kw-fleet-actions"><a href="{cls_href(c) if c else "/transfers"}">{e(c["name"]) if c else "Details"} prices</a>'
                  f'<a class="kw-button" href="#transfer-enquiry" data-pick="{e(c["name"]) if c else ""}" data-model="{e(x["name"])}">Book this car</a></div></div></article>')
    return tabs, cards, cars


def build_fleet():
    path = FLEET_PATH
    tabs, cards, cars = fleet_cards()
    suits = info_cards([('', '1 to 3 guests', f'<a href="{cls_href(TR_CLASSES[0])}">Business Sedan</a> for everyday rides, or <a href="{cls_href(TR_CLASSES[2])}">First Class</a> for VIP guests.'),
                        ('', '4 to 6 guests', f'<a href="{cls_href(TR_CLASSES[1])}">Family SUV</a> for families with luggage, or <a href="{cls_href(TR_CLASSES[4])}">Luxury SUV</a> for a premium ride.'),
                        ('', '7 guests', f'<a href="{cls_href(TR_CLASSES[3])}">Business Van</a> or a GMC Yukon XL from the Luxury SUV class.'),
                        ('', 'More than 7', 'Two cars, or ask us about a larger van for your group.')])
    faqs = [('Will I get the exact car I book?', 'You book a vehicle class, and you can name the car you prefer. We confirm that car when it is free; otherwise we send another car from the same class.'),
            ('Are the prices per car?', 'Yes. Trip prices are per car, one way, and hourly prices are per car per hour (minimum ' + str(HOUR_MIN) + ' hours).'),
            ('What is included?', INCLUDED_TXT + '.'),
            ('Do you have electric cars?', 'Yes: the Tesla Model Y, BYD Han and BYD Song+ are electric, and the Lexus ES 300h is a hybrid.')]
    title = f'Chauffeur Fleet in Dubai: {len(CARS)} Cars with Driver'
    desc = fit(f'See the KWIKAR chauffeur fleet: Mercedes E-Class, S-Class and V-Class, BMW, Lexus, Tesla, BYD, GMC and Cadillac Escalade. Prices per car from {money(class_low(TR_CLASSES[0]))}.', 160)
    main = (f'<section class="kw-fleet-head"><div class="kw-wrap"><nav aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/transfers">Transfers</a> / Fleet</nav>'
            f'<span class="kw-eyebrow">OUR FLEET</span><h1>A car for every journey</h1>'
            f'<p>{len(CARS)} chauffeur-driven cars in five vehicle classes, from business sedans to seven-seat vans. Every price includes {e(INCLUDED_TXT)}.</p></div></section>'
            f'<section class="kw-section kw-fleet-section"><div class="kw-wrap"><div class="kw-filter-row kw-fleet-tabs" role="group" aria-label="Filter the fleet">{tabs}</div>'
            f'<div class="kw-fleet-grid">{cards}</div></div></section>'
            f'<section class="kw-section kw-market-alt"><div class="kw-wrap">{seo_head("CHOOSING A CAR", "Which car suits your journey")}{suits}</div></section>'
            + tr_enquiry_section('Book a car', 'Tell us your route, date and the car you prefer.')
            + faq_block('Fleet questions', faqs) + fleet_credits_html())
    page(path, title, desc, main, active='Transfers', full_title=True, crumbs=[('Home', '/'), ('Transfers', '/transfers'), ('Fleet', path)],
         head_extra=ld(faq_ld(faqs)) + ld({'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'KWIKAR chauffeur fleet',
                                            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': x['name']} for i, x in enumerate(cars)]}))


def car_class_href(car):
    c = next((c for c in TR_CLASSES if car['name'] in c['models'] or any(car['name'].startswith(m) for m in c['models'])), None)
    return cls_href(c) if c else '/transfers'


def transfer_paths():
    return ([tr_href(r) for r in TR_ROUTES] + [ap_href(a) for a in TR_AIRPORTS] + [cls_href(c) for c in TR_CLASSES] + [HOURLY_PATH, FLEET_PATH])


def VISA_FAQS(low_v):
    return [
        ('How much is a UAE tourist visa?', f'With KWIKAR, UAE tourist visas start from {money(low_v)} for 14 days, single entry. 30- and 60-day visas and multiple-entry visas cost more; the current prices are listed above. Our team confirms the final fee for your nationality before you pay.'),
        ('What documents do I need for a UAE tourist visa?', 'Usually a passport copy valid for at least six months, a recent colour photo, a return or onward ticket and travel medical insurance. Some nationalities also need a national ID card. We confirm the full list for your nationality.'),
        ('How long does a UAE tourist visa take?', 'Processing usually takes 3–4 working days. Express processing is available on request for some nationalities, at an extra cost.'),
        ('What is the difference between single and multiple entry?', 'A single-entry visa lets you enter the UAE once. A multiple-entry visa lets you leave and come back during its validity, which suits trips that include Oman or other nearby countries.'),
        ('Is approval guaranteed?', 'No. Visa decisions are made by the UAE immigration authorities. We help you understand the requirements and prepare a complete application.'),
        ('Can I apply if I am already in the UAE?', 'In some cases, yes, but extra government fees apply when the applicant is inside the UAE. Tell us your situation and we will explain the options.'),
        ('Do you help with other visas?', 'Yes. We can also help with the 96-hour UAE transit visa, express UAE visas and the Saudi Arabia tourist e-visa. Ask us for current requirements and fees.'),
    ]


def build_visa():
    def card(v):
        return (f'<article class="kw-visa"><span class="kw-eyebrow">{e(v["stay"])} · Estimate {e(v["processing"])}</span><h3>{e(v["name"])}</h3>'
                f'<p>{e(f"From {money(v[chr(112) + "rice"])} · final fee confirmed by our team") if v.get("price") else "Fee on request"}</p><a href="#visa-enquiry" data-pick="{e(v["name"])}">Ask about this visa ↗</a></article>')
    groups = ''.join(f'<section class="kw-visa-group"><h2>{g}</h2><div class="kw-visa-grid">' + ''.join(card(v) for v in VISAS if ('UAE' in v['name']) == (g == 'UAE visas')) + '</div></section>' for g in ('UAE visas', 'Other destinations'))
    opts = ''.join(f'<option>{e(v["name"])}</option>' for v in VISAS)
    form = (f'<form class="kw-form" data-wa="Visa enquiry"><label>Visa type<select name="type" data-label="Type" data-prefill="type">{opts}</select></label><label>Nationality<input required name="nationality" data-label="Nationality"></label>'
            f'<label>Planned travel date<input type="date" name="date" data-label="Travel date"></label><label>Your name<input required name="name" data-label="Name"></label><label>Phone or email<input required name="contact" data-label="Contact"></label>'
            f'<button class="kw-button" type="submit">Enquire on WhatsApp ↗</button></form>')
    uae_v = [v for v in VISAS if 'UAE Tourist' in v['name'] and v.get('price')]
    low_v = min(v['price'] for v in uae_v)
    quick = (f'<section class="kw-section kw-visa-quick"><div class="kw-wrap">' + seo_head('AT A GLANCE', 'UAE tourist visa in short') + f'<div class="kw-detail-block kw-quick"><p>KWIKAR helps you apply for a UAE tourist visa for 14, 30 or 60 days, single or multiple entry, from {money(low_v)}. '
             'Processing usually takes 3–4 working days, and express processing is available on request. You typically need a clear passport copy valid for at least six months, a recent colour photo, a return or onward ticket and travel medical insurance. '
             'The visa is issued by the UAE authorities, so approval is never guaranteed.</p>'
             '<dl class="kw-facts kw-facts-2"><div><dt>Lengths</dt><dd>14, 30 or 60 days</dd></div><div><dt>Entries</dt><dd>Single or multiple</dd></div>'
             f'<div><dt>Price</dt><dd>From {money(low_v)}</dd></div><div><dt>Processing</dt><dd>3–4 working days; express on request</dd></div>'
             '<div><dt>Passport</dt><dd>Valid for at least 6 months</dd></div><div><dt>Issued by</dt><dd>UAE immigration authorities</dd></div></dl></div></div></section>')
    docs = ('<h3>Documents you will usually need</h3><ul class="kw-ticks"><li>Passport copy, valid for at least six months from your arrival date</li><li>Recent colour passport photo on a white background</li>'
            '<li>Return or onward flight ticket</li><li>Travel medical insurance valid in the UAE</li><li>National ID card for some nationalities (for example Pakistan, Iraq, Iran and Afghanistan)</li></ul>'
            '<p>Further documents may be requested depending on nationality. Do not send passport documents in the enquiry form; our team tells you the secure way to share them. '
            'Requirements checked against the <a href="https://gdrfad.gov.ae/en/node/13896" target="_blank" rel="noopener noreferrer">GDRFA Dubai tourist visa page</a>.</p>')
    main = (page_hero('TRAVEL DOCUMENTS', 'UAE Tourist Visa: 14, 30 and 60 Days', 'Tell us about your travel plans and our team will explain the available visa options, documents and current processing estimates.', photo('1436491865332-7a61a109cc05', 1600))
            + quick
            + f'<section class="kw-section"><div class="kw-wrap">{section_head("Find the right visa", "VISA OPTIONS")}<p class="kw-section-intro">Starting prices are indicative benchmarks for eligible applications. Our team confirms your actual visa cost after checking nationality, eligibility and processing. No payment is requested through this page.</p><div class="kw-visa-categories">{groups}</div></div></section>'
            + f'<section class="kw-section kw-market-alt" id="visa-enquiry"><div class="kw-wrap kw-service-layout"><div>{section_head("How to get started", "APPLICATION")}<ol class="kw-process"><li>Choose the visa and share your travel date.</li><li>We check eligibility and confirm current fees and document requirements.</li><li>Submit documents through the agreed secure channel.</li><li>Our team updates you on the application outcome.</li></ol>{docs}</div>{form}</div></section>'
            + faq_block('Visa questions', VISA_FAQS(low_v))
            + f'<section class="kw-section"><div class="kw-wrap"><p class="kw-checked">Visa options and fees last reviewed by the KWIKAR team on 30 Oct 2026. Government rules can change; we confirm current requirements before you apply.</p></div></section>')
    faq_ld = ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in VISA_FAQS(low_v)]})
    page('/visa', 'UAE Tourist Visa – 14, 30 & 60 Days | KWIKAR',
         f'Apply for a UAE tourist visa with KWIKAR: 14, 30 or 60 days, single or multiple entry, from {money(low_v)}. Check documents and processing, then ask on WhatsApp.',
         main, active='Visas', full_title=True, head_extra=faq_ld, crumbs=[('Home', '/'), ('Visa', '/visa')])


def build_contact():
    form = ('<form class="kw-form" data-wa="KWIKAR enquiry"><label>Your name<input required name="name" data-label="Name"></label><label>Phone or email<input required name="contact" data-label="Contact"></label>'
            '<label>How can we help?<select name="service" data-label="Service" data-prefill="service"><option>Attractions</option><option>Holidays</option><option>Transfers</option><option>Visa</option><option>Other</option></select></label>'
            '<label>Travel details<textarea required rows="5" name="details" data-label="Details" placeholder="Dates, number of travellers and what you\'re looking for"></textarea></label>'
            '<button class="kw-button" type="submit">Continue on WhatsApp ↗</button><small>Your enquiry opens WhatsApp for you to review and send.</small><a href="#" data-mail>Prefer email? Open your email app ↗</a></form>')
    main = (page_hero("LET'S PLAN TOGETHER", "Tell us where you're going.", 'Our team can help with experiences, holidays, transfers and visa enquiries.', photo('1512453979798-5ea266f8880c', 1600))
            + f'<section class="kw-section"><div class="kw-wrap kw-contact-grid"><div>{section_head("We\'re here to help", "SPEAK TO OUR TEAM")}<p>Share what you need and continue the conversation on WhatsApp.</p>'
            f'<div class="kw-contact-list"><a href="tel:+{PHONE}">Call us<br><strong>{PHONE_FMT}</strong></a><a href="mailto:{EMAIL}">Email us<br><strong>{EMAIL}</strong></a></div></div>{form}</div></section>')
    page('/contact', 'Contact', 'Contact KWIKAR on WhatsApp, phone or email about tours, attraction tickets, holiday packages, private transfers and UAE visa help. We are happy to help.', main, crumbs=[('Home', '/'), ('Contact', '/contact')])


def info(path, title, desc, body, label):
    page(path, title, desc, body, main_class='kw-info-page', crumbs=[('Home', '/'), (label, path)])


def build_info_pages():
    info('/about', 'About KWIKAR', 'KWIKAR is a UAE travel company for tours, attraction tickets, holidays, private transfers and visa help. See how we check prices and visitor details.', '''
<h1>Travel plans, made simpler.</h1><p>KWIKAR LLC-FZ helps travellers explore experiences, holiday ideas, private transfers and visa assistance in the UAE and beyond. Browse what interests you, then tell our team your dates and requirements.</p>
<h2>How we check our information</h2><ul><li><strong>Prices and options</strong> come from our suppliers' live rates and are refreshed several times a day. Each tour page shows when they were last checked.</li><li><strong>Visitor details</strong> on our main pages, such as opening hours, entry rules and what to bring, are written by the KWIKAR team from official venue and supplier information, and each page shows the date it was checked.</li><li><strong>Final details</strong> are confirmed by our team for your date before you pay, because supplier rules can change.</li><li><strong>No invented reviews or ratings.</strong> We do not show ratings from other websites as our own.</li><li><strong>Corrections:</strong> if you spot something out of date, email <a href="mailto:info@kwikar.com">info@kwikar.com</a> and we will check and fix it.</li></ul>
<h2>How enquiries work</h2><ol><li>Explore experiences and indicative prices.</li><li>Send your request on WhatsApp with your preferred date and number of guests.</li><li>Our team confirms availability, final price and applicable booking terms before payment.</li></ol><p>Questions? <a href="/contact">Get in touch</a>.</p>''', 'About')
    info('/privacy', 'Privacy', 'How KWIKAR uses the details you share in WhatsApp and email enquiries. This website takes no online payments and does not ask for or store card details.', f'''
<h1>Privacy and enquiries</h1><p>KWIKAR LLC-FZ uses the details you share to respond to travel enquiries and arrange requested services. This website does not take online payments and does not ask for or store card details.</p>
<h2>How our forms work</h2><p>Booking and enquiry forms on this website open WhatsApp (or your email app) with a prepared message, which you review before you send it.</p>
<h2>Information you share</h2><p>When you contact us we receive the details you choose to send, for example your name, phone number or email, selected tour or service, travel date, number of guests, pickup location and notes. We use them to answer you, confirm availability and price, arrange your booking and contact you about it. Visa documents should be shared only after our team confirms the appropriate process.</p>
<h2>Other services</h2><p>WhatsApp and your email provider handle messages under their own terms. A tour or transfer supplier may receive the booking details needed to provide your service.</p>
<h2>Your questions</h2><p>Contact <a href="mailto:{EMAIL}">{EMAIL}</a> about your information or a data request. See our <a href="/booking-information">booking information</a>.</p>''', 'Privacy')
    info('/terms', 'Terms & conditions', 'Terms for KWIKAR travel enquiries, quotes and confirmed bookings: how reservations are confirmed in writing, payment, changes and supplier cancellation rules.', '''
<h1>Terms &amp; conditions</h1><p>Kwikar LLC-FZ provides travel enquiries and booking assistance for attractions, holidays, transfers and visas. Information and prices on this website may change with supplier availability, dates and guest details.</p>
<h2>Quotes and orders</h2><p>Only a written confirmation from KWIKAR confirms a reservation. Sending an enquiry does not reserve a service. Before any payment, KWIKAR confirms the final AED amount, what is included and the applicable supplier conditions.</p>
<h2>Booking and payment</h2><p>No payment is taken on this website. Our team agrees the payment method with you directly. A booking is confirmed only when KWIKAR sends you a written confirmation with your booking details.</p>
<h2>Changes and cancellations</h2><p>Supplier rules for each service govern changes, cancellation charges and refunds. Read the specific tour conditions and our <a href="/refund-policy">refund and cancellation policy</a>. Visa issuance is determined by the issuing authority; processing times and approval are not guaranteed.</p>
<p>Read <a href="/booking-information">booking information</a> or <a href="/contact">contact our team</a> with questions.</p>''', 'Terms')
    info('/refund-policy', 'Refund & cancellation policy', 'How KWIKAR handles experiences that cannot be confirmed, changes and cancellations after confirmation, and refunds under each supplier policy.', f'''
<h1>Refund &amp; cancellation policy</h1><h2>Before confirmation</h2><p>If an experience or service cannot be confirmed with the supplier, we tell you on WhatsApp and suggest alternatives. Nothing is booked until you accept the final quote.</p>
<h2>After confirmation</h2><p>Cancellation or changes to a confirmed booking depend on the supplier's policy for that exact tour, option and travel date. The applicable conditions are shown on the tour page when provided by the supplier and are shared with your confirmation. Some tickets are non-refundable or carry a cancellation charge. Contact us as soon as possible with your booking details; we will check the supplier's terms and tell you the refundable amount, if any, before processing a request.</p>
<h2>Other services</h2><p>Transfers, visas and holiday packages can have different cancellation terms. KWIKAR shares the applicable terms with your quote before requesting payment. Visa approval is determined by the issuing authority; an application fee may not be refundable after processing starts.</p>
<p>For assistance email <a href="mailto:{EMAIL}">{EMAIL}</a> or <a href="/contact">contact our team</a>. See <a href="/booking-information">how booking works</a>.</p>''', 'Refund policy')
    info('/booking-information', 'Booking information', 'How booking with KWIKAR works: send your request on WhatsApp, our team confirms availability and the final AED price, then you pay and receive confirmation.', '''
<h1>Booking information</h1><p>Tour prices are shown in AED. Some services require a quote before we can confirm the total.</p>
<h2>Tour booking</h2><p>Choose an experience, option, date and guests, then send your booking request on WhatsApp. The supplier recommended prices are indicative; our team checks age-based guest prices, date and availability, then replies with the final AED amount and how to pay. Your booking is confirmed when we send your confirmation and voucher reference.</p>
<h2>Transfers, visas and holidays</h2><p>Send an enquiry with your travel details. Transfers and holidays are arranged on WhatsApp. For visas, contact our team to check requirements and pricing. A website starting price does not reserve a vehicle, visa or holiday. The confirmed AED quote is the customer total, with no separate card or booking fee.</p>
<p>Read our <a href="/terms">terms</a>, <a href="/refund-policy">refund and cancellation policy</a> and <a href="/privacy">privacy policy</a>. Questions? <a href="/contact">Contact KWIKAR</a>.</p>''', 'Booking information')


# ================================================================= blog / guides (data/blog/*.json)
def load_posts():
    posts = []
    for f in sorted(os.listdir(os.path.join(ROOT, 'data', 'blog'))):
        if f.endswith('.json'):
            posts.append(json.load(open(os.path.join(ROOT, 'data', 'blog', f), encoding='utf-8')))
    return sorted(posts, key=lambda a: a['published'], reverse=True)


POSTS = load_posts() if os.path.isdir(os.path.join(ROOT, 'data', 'blog')) else []


def post_href(a):
    return f'/blog/{a["city"]}/{a["slug"]}'


def tour_by_id(tid):
    return next((t for t in TOURS if t['id'] == tid), None)


def build_blog():
    if not POSTS:
        return
    def nice(d):
        return datetime.date.fromisoformat(d).strftime('%-d %b %Y')
    for a in POSTS:
        path = post_href(a)
        tour = tour_by_id(a.get('tour_id'))
        body = a['body'].replace('{tour}', tour_href(tour) if tour else '/activities')
        aq = tour_by_id(144)
        body = body.replace('{aquarium}', tour_href(aq) if aq else '/search?q=aquarium')
        def _price(m):
            t_ = tour_by_id(int(m.group(1)))
            return money(t_['price']) if t_ and t_.get('price') else 'the price our team confirms'
        def _link(m):
            t_ = tour_by_id(int(m.group(1)))
            return tour_href(t_) if t_ else '/activities'
        body = re.sub(r'\{price:(\d+)\}', _price, re.sub(r'\{link:(\d+)\}', _link, body))
        a = dict(a, summary=re.sub(r'\{price:(\d+)\}', _price, a['summary']), faqs=[[q, re.sub(r'\{price:(\d+)\}', _price, x)] for q, x in a.get('faqs', [])])
        img = (DETAILS.get(a.get('tour_id')) or {}).get('img') or (tour or {}).get('img') or '/assets/img/hero-dubai.webp'
        glance = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in a.get('glance', []))
        faqs = faq_cards(a.get('faqs', []), open_all=True) if a.get('faqs') else ''
        rel = [r for r in (tour_by_id(i) for i in a.get('related', [])) if r]
        others = [b for b in POSTS if b["slug"] != a["slug"]]
        sources = ''.join(f'<li><a href="{e(u)}" target="_blank" rel="noopener noreferrer">{e(n)}</a></li>' for n, u in a.get('sources', []))
        cta = ''
        if tour:
            cta = (f'<section class="kw-final-cta"><div><h2>Book {e(tour["name"])}</h2><p>Compare every option and current price, then send your request on WhatsApp.'
                   + (f' From {money(tour["price"])} per person.' if tour.get('price') else '') + '</p></div>'
                   f'<div><a class="kw-button" href="{tour_href(tour)}">See tickets and prices</a></div></section>')
        main = f"""<nav aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/blog">Travel guides</a> / {e(a['h1'])}</nav>
<article class="kw-blog-article">
<h1>{e(a['h1'])}</h1>
<p class="kw-detail-meta">By the KWIKAR team · Published {nice(a['published'])} · Updated {nice(a['updated'])}</p>
<img class="kw-blog-hero" src="{e(img)}" alt="{e(a['h1'])}" fetchpriority="high">
<section class="kw-detail-block kw-quick" aria-label="Summary"><p>{e(a['summary'])}</p>{f'<dl class="kw-facts kw-facts-2">{glance}</dl>' if glance else ''}</section>
<div class="kw-blog-body">{body}</div>
{cta}
{f'<section class="kw-detail-block"><h2>Questions</h2>{faqs}</section>' if faqs else ''}
{f'<section class="kw-detail-related"><div class="kw-section-head"><div><h2>Experiences in this guide</h2></div></div><div class="kw-list-grid">{"".join(list_card(r) for r in rel)}</div></section>' if rel else ''}
{f'<section class="kw-detail-block kw-more-links"><h2>More travel guides</h2><ul>' + "".join(f'<li><a href="{post_href(b)}">{e(b["h1"])}</a></li>' for b in others) + '</ul></section>' if others else ''}
{f'<section class="kw-detail-block"><h3>Sources</h3><ul class="kw-sources">{sources}</ul><p class="kw-checked">Prices on linked pages come from live supplier rates. Venue rules can change; our team confirms details for your date before you pay.</p></section>' if sources else ''}
</article>"""
        post_ld = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': a['h1'], 'description': a['description'],
                   'datePublished': a['published'], 'dateModified': a['updated'], 'image': [img if img.startswith('http') else SITE + img],
                   'author': {'@type': 'Organization', 'name': 'KWIKAR team', 'url': SITE + '/about'},
                   'publisher': {'@id': SITE + '/#organization'}, 'mainEntityOfPage': SITE + path, 'inLanguage': 'en'}
        lds = ld(post_ld)
        if a.get('faqs'):
            lds += ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
                {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': x}} for q, x in a['faqs']]})
        page(path, a['title'], a['description'], main, full_title=True, head_extra=lds, og_image=img,
             main_class='kw-wrap kw-detail kw-blog', crumbs=[('Home', '/'), ('Travel guides', '/blog'), (a['h1'], path)])
    cards = ''.join(
        f'<article class="kw-list-card"><a href="{post_href(a)}"><img src="{e((DETAILS.get(a.get("tour_id")) or {}).get("img") or "/assets/img/hero-dubai.webp")}" loading="lazy" alt=""></a>'
        f'<div><span>{e(loc_name(a["city"]))} · Guide</span><h3><a href="{post_href(a)}">{e(a["h1"])}</a></h3><p>{e(a["summary"][:150].rsplit(" ", 1)[0])}…</p>'
        f'<a class="kw-card-view" href="{post_href(a)}">Read the guide →</a></div></article>' for a in POSTS)
    main = (f'<section class="kw-list-banner" style="background-image:linear-gradient(90deg,#07162aeb,#07162a3d),url(\'/assets/img/hero-dubai.webp\')"><div class="kw-market-wrap">'
            f'<nav class="kw-list-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Travel guides</nav><h1>Dubai and UAE Travel Guides</h1>'
            f'<p>Practical guides from the KWIKAR team to help you choose tickets, plan your days and get more from your trip.</p></div></section>'
            f'<div class="kw-market-wrap kw-blog-list"><div class="kw-list-grid">{cards}</div></div>')
    page('/blog', 'Dubai and UAE Travel Guides', 'Practical Dubai and UAE travel guides from KWIKAR: which tickets to book, the best times to visit and how to plan your days.',
         main, main_class='kw-list-page', crumbs=[('Home', '/'), ('Travel guides', '/blog')])


def build_status_pages():
    page('/404.html', 'Page not found', 'This page could not be found.', f'''<h1>Page not found</h1><p>The page you are looking for has moved or no longer exists.</p>
<p><a class="kw-button" href="/">Go to homepage</a> <a class="kw-button" href="/activities">Browse experiences</a></p>''', noindex=True, main_class='kw-wrap kw-status')
    page('/410.html', 'No longer available', 'This experience is no longer available.', f'''<h1>This experience is no longer available</h1><p>The supplier has stopped offering it. Browse similar experiences or ask our team for an alternative.</p>
<p><a class="kw-button" href="/activities">Browse experiences</a> <a class="kw-button" href="{e(wa("Hi KWIKAR, the experience I was looking for is no longer available. Can you suggest an alternative?"))}" target="_blank" rel="noopener noreferrer">Ask on WhatsApp</a></p>''', noindex=True, main_class='kw-wrap kw-status')


# ================================================================= data files, sitemaps, robots, redirects
def write_data_files():
    items = [{'id': t['id'], 'name': t['name'], 'img': t.get('img'), 'cats': t.get('cats') or [], 'price': t.get('price'), 'unit': t.get('unit'),
              'loc': t['loc'], 'url': tour_href(t)} for t in TOURS]
    os.makedirs(os.path.join(OUT, 'assets', 'data'), exist_ok=True)
    json.dump({'checked': CHECKED, 'items': items, 'locations': [{'id': l['id'], 'name': l['name']} for l in LOCATIONS], 'categories': CATEGORIES},
              open(os.path.join(OUT, 'assets', 'data', 'tours.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


def write_css():
    parts = [open(os.path.join(ROOT, 'styles', f), encoding='utf-8').read() for f in ('preflight.css', 'old-site.css', 'additions.css')]
    css = parts[1].replace('.kw-slider-copy h1', '.kw-slider-copy h2')   # the page H1 now sits below the slider
    imp = re.match(r"@import url\([^)]*\);\s*", css)
    if imp:  # fonts are linked in <head>; an @import must not follow other rules
        css = css[imp.end():]
    os.makedirs(os.path.join(OUT, 'assets', 'css'), exist_ok=True)
    out = parts[0] + '\n' + css + '\n' + parts[2]
    out = re.sub(r'/\*.*?\*/', '', out, flags=re.S)
    out = re.sub(r'\s*([{};,>])\s*', r'\1', out)
    out = re.sub(r'\s+', ' ', out).replace(';}', '}')
    open(os.path.join(OUT, 'assets', 'css', 'site.css'), 'w', encoding='utf-8').write(out)


def build_seo_files():
    def urlset(paths):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + ''.join(f'  <url><loc>{SITE}{p_}</loc><lastmod>{TODAY}</lastmod></url>\n' for p_ in paths) + '</urlset>\n')
    pages = ['/', '/holidays', '/transfers'] + transfer_paths() + ['/visa', '/contact', '/about', '/privacy', '/terms', '/booking-information', '/refund-policy'] + (['/blog'] + [post_href(a) for a in POSTS] if POSTS else [])
    hubs = ['/destinations', '/activities'] + [f'/destinations/{l["id"]}' for l in LOCATIONS if l['id'] in LIVE_LOCS] + [f'/activities/{c["slug"]}' for c in LIVE_CATS]
    products = [tour_href(t) for t in ALL_TOURS if tf.visible(t)]
    for name, paths in (('pages', pages), ('hubs', hubs), ('products', products)):
        open(os.path.join(OUT, f'sitemap-{name}.xml'), 'w').write(urlset(paths))
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <sitemap><loc>{SITE}/sitemap-{n}.xml</loc><lastmod>{TODAY}</lastmod></sitemap>\n' for n in ('pages', 'hubs', 'products')) + '</sitemapindex>\n')
    rules = 'Disallow: /search\nDisallow: /api/\n'
    open(os.path.join(OUT, 'robots.txt'), 'w').write(
        f'# Search engines and AI search (ChatGPT search = OAI-SearchBot) may crawl the site.\nUser-agent: *\nAllow: /\n{rules}\n'
        f'User-agent: OAI-SearchBot\nAllow: /\n{rules}\nUser-agent: GPTBot\nAllow: /\n{rules}\nSitemap: {SITE}/sitemap.xml\n')

    lines = []
    for tid, p_ in sorted(SLUGS.items(), key=lambda kv: int(kv[0])):
        if tid in LIVE_IDS:
            lines += [f'RewriteRule ^(?:ar/)?tour/{tid}/?$ {p_} [R=301,L]', f'RewriteCond %{{QUERY_STRING}} (?:^|&)id={tid}(?:&|$)', f'RewriteRule ^tour\\.html$ {p_}? [R=301,L]']
        else:
            lines += [f'RewriteRule ^(?:ar/)?tour/{tid}/?$ - [G,L]', f'RewriteRule ^{p_.strip("/")}/?$ - [G,L]']
    for old, new in sorted(SLUG_REDIRECTS.items()):
        lines.append(f'RewriteRule ^{re.escape(old.strip("/"))}/?$ {new} [R=301,L]')
    # city lists that existed briefly at /activities/{city} now live on the destination pages
    for city in sorted({tf.city_of(t['loc']) for t in ALL_TOURS}):
        lines.append(f'RewriteRule ^activities/{city}/?$ /destinations/{"other" if city == "uae" else city} [R=301,L]')
    tpl = open(os.path.join(ROOT, 'htaccess.template'), encoding='utf-8').read()
    tpl = tpl.replace('RewriteRule ^destinations/other/?$ /activities/uae [R=301,L]\n', '')
    open(os.path.join(OUT, '.htaccess'), 'w', encoding='utf-8').write(tpl.replace('# {{TOUR_RULES}}', '\n'.join(lines)))


def clean_output():
    keep = {'assets', 'api'}
    for name in os.listdir(OUT):
        full = os.path.join(OUT, name)
        if os.path.isdir(full) and name not in keep and not name.startswith('.'):
            shutil.rmtree(full)
        elif os.path.isfile(full) and (name.endswith(('.html', '.xml')) or name in ('robots.txt', '.htaccess')) \
                and not re.match(r'(google[0-9a-f]+\.html|BingSiteAuth\.xml)$', name):   # search-engine verification files stay
            os.remove(full)
    for old in ('assets/css/style.css', 'assets/js/site.js', 'assets/js/tours.js', 'assets/js/catalog.js'):
        try:
            os.remove(os.path.join(OUT, old))
        except OSError:
            pass


if __name__ == '__main__':
    clean_output()
    write_css()
    VERSION = _asset_version()
    write_data_files()
    build_home()
    build_listings()
    build_destinations()
    build_products()
    build_holidays()
    build_transfers()
    build_visa()
    build_contact()
    build_info_pages()
    build_blog()
    build_status_pages()
    build_seo_files()
    n = sum(len([f for f in fs if f.endswith('.html')]) for _, _, fs in os.walk(OUT))
    print(f'Built {n} HTML pages ({len(ALL_TOURS)} tour pages) into {OUT}')
