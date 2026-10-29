#!/usr/bin/env python3
"""
KWIKAR static site generator.

Reads data/catalog.json (holidays, cars, visas, destinations) and the live tours
API, and writes plain HTML pages into ../public_html.

Run:  python3 build.py                 (loads tours from https://kwikar.com/api/tours.php)
      python3 build.py --feed FILE.json (use a saved feed, for offline testing)
"""
import json, html, os, re, sys, datetime
from urllib.parse import quote
import tours_feed as tf

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, '..', 'public_html'))
SITE = 'https://kwikar.com'
PHONE = '971505599243'
PHONE_FMT = '+971 50 559 9243'
EMAIL = 'info@kwikar.com'
def _asset_version():
    import hashlib
    h = hashlib.sha1()
    for f in ('assets/css/style.css', 'assets/js/site.js', 'assets/js/tours.js'):
        try:
            h.update(open(os.path.join(OUT, f), 'rb').read())
        except OSError:
            pass
    return h.hexdigest()[:10]


VERSION = _asset_version()  # changes only when CSS/JS change
TODAY = datetime.date.today().isoformat()

# Optional: fill these in to switch on analytics / search-engine verification.
CONFIG = {}
try:
    CONFIG = json.load(open(os.path.join(ROOT, 'data', 'site-config.json'), encoding='utf-8'))
except Exception:
    pass
GA4_ID = CONFIG.get('ga4_id', '').strip()
GOOGLE_VERIFY = CONFIG.get('google_site_verification', '').strip()
BING_VERIFY = CONFIG.get('bing_site_verification', '').strip()

cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
LOCATIONS = cat['locations']  # includes 'other' (shown as "More")
REAL_LOCATIONS = [l for l in LOCATIONS if l['id'] != 'other']
HOLIDAYS, CARS, VISAS = cat['holidays'], cat['cars'], cat['visas']
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


# ---------------------------------------------------------------- live tours
def _load_tours():
    if '--feed' in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index('--feed') + 1], encoding='utf-8'))
        return data['items'], {int(k): v for k, v in data['details'].items()}, data.get('updated', '')
    return tf.load_feed()


ALL_TOURS, DETAILS, FEED_UPDATED = _load_tours()
TOURS = tf.popular([t for t in ALL_TOURS if tf.visible(t)])      # what listings show
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
try:
    CHECKED = datetime.datetime.fromisoformat(FEED_UPDATED.replace('Z', '+00:00')).strftime('%-d %b %Y')
except Exception:
    CHECKED = datetime.date.today().strftime('%-d %b %Y')


def tour_href(t):
    return SLUGS.get(str(t['id'])) or f"/tour/{t['id']}"


def place_name(loc_id):
    if loc_id in (None, '', 'other'):
        return 'UAE'
    l = next((x for x in LOCATIONS if x['id'] == loc_id), None)
    return l['name'] if l else 'UAE'


def tour_cards(tours, short=False):
    return ''.join(tf.card(t, place_name(t['loc']), tour_href(t), short) for t in tours)


# City hubs for tours: /activities/{city}. 'other' tours are UAE-wide.
CITY_IDS = []
for _t in TOURS:
    _c = tf.city_of(_t['loc'])
    if _c not in CITY_IDS:
        CITY_IDS.append(_c)


def city_tours(city):
    return [t for t in TOURS if tf.city_of(t['loc']) == city]


def city_label(city):
    return 'the UAE' if city == 'uae' else place_name(city)


def e(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def U(pid, w=900):
    return f'/assets/img/u/{pid}{"-lg" if w >= 1200 else ""}.webp'


UNSPLASH = re.compile(r'https://images\.unsplash\.com/photo-([0-9a-f-]+)\?[^"\'\s)]*')


def localize(text):
    """Use the copies in assets/img/u instead of loading photos from Unsplash."""
    def rep(m):
        lg = re.search(r'[?&]w=(\d+)', m.group(0))
        return U(m.group(1), int(lg.group(1)) if lg else 800)
    return UNSPLASH.sub(rep, text)


def wa(msg):
    return f'https://wa.me/{PHONE}?text={quote(msg)}'


def money(n):
    return f'AED {n:,.0f}' if float(n).is_integer() else f'AED {n:,.2f}'


def loc(id_):
    return next((l for l in LOCATIONS if l['id'] == id_), None)


ICON = {
    'flag': '<path d="M5 21V4m0 0h11l-2 4 2 4H5"/>',
    'mountain': '<path d="m3 20 6-12 4 7 3-4 5 9z"/>',
    'plane': '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    'doc': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    'ship': '<path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M19.4 17.5 21 11l-9-4-9 4 1.8 6.5M12 2v5M8 4h8"/>',
    'car': '<path d="M19 17h2v-5l-2-5H5L3 12v5h2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M9 17h6M3 12h18"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    'phone': '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
    'chat': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
    'chev': '<path d="m6 9 6 6 6-6"/>',
    'out': '<path d="M7 17 17 7M8 7h9v9"/>',
    'home': '<path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2z"/>',
    'ferris': '<circle cx="12" cy="10" r="7"/><path d="M12 3v14M5 10h14M7 5l10 10M17 5 7 15M8 22l4-5 4 5"/>',
    'bag': '<rect x="4" y="7" width="16" height="13" rx="2"/><path d="M9 7V4h6v3M9 20v2M15 20v2"/>',
    'help': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6M12 17h.01"/>',
    'id': '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="11" r="2.5"/><path d="M5.5 17c.8-2 2-3 3.5-3s2.7 1 3.5 3M15 9h3M15 13h3"/>',
}


def icon(name, cls='ico', color=None):
    style = f' style="color:{color}"' if color else ''
    return f'<svg class="{cls}" viewBox="0 0 24 24"{style} aria-hidden="true">{ICON[name]}</svg>'


# ---------------------------------------------------------------- navigation
UAE = [l for l in REAL_LOCATIONS if l['group'] == 'uae']
INTL_MENU = [loc(i) for i in ['singapore', 'bali', 'thailand', 'malaysia'] if loc(i)]
LIVE_UAE = [l for l in UAE if l['id'] in LIVE_LOCS]
LIVE_INTL_MENU = [l for l in INTL_MENU if l['id'] in LIVE_LOCS]
EXPERIENCE_TERMS = [('City Tours', 'city tour'), ('Theme Parks', 'theme park'), ('Desert Adventures', 'desert'), ('Water Activities', 'water'),
                    ('Cultural Experiences', 'museum'), ('Family Activities', 'family'), ('Luxury Experiences', 'luxury'), ('Attraction Tickets', 'ticket')]

NAV = [
    ('Destinations', '/destinations', 'flag', '#ff6a21'),
    ('Activities', '/activities', 'mountain', '#08b9bb'),
    ('Holidays', '/holidays', 'plane', '#5969e9'),
    ('Visas', '/visa', 'doc', '#ff9516'),
    ('Cruises', '/activities/cruises', 'ship', '#406bf2'),
    ('Transfers', '/transfers', 'car', '#2aba87'),
]
MENUS = {
    'Activities': [('Explore activities', [('City tours', '/activities/city-tours'), ('Desert adventures', '/activities/desert-adventures'), ('Theme parks', '/activities/theme-parks'), ('Water activities', '/activities/water-activities')]),
                   ('Popular choices', [('Burj Khalifa', '/search?q=Burj%20Khalifa'), ('Dubai safari', '/search?q=desert%20safari'), ('Abu Dhabi tours', '/destinations/abu-dhabi')])],
    'Holidays': [('Holiday destinations', [(c, f'/holidays?country={quote(c)}') for c in dict.fromkeys(h['country'] for h in HOLIDAYS)]),
                 ('Plan your trip', [('All holiday packages', '/holidays'), ('Request a tailored holiday', '/contact')])],
    'Visas': [('UAE visa options', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' in v['name']]),
              ('Other visa assistance', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' not in v['name']])],
    'Cruises': [('Cruise experiences', [('All cruises', '/activities/cruises'), ('Dubai Marina cruises', '/search?q=marina%20cruise'), ('Dhow cruises', '/search?q=dhow%20cruise'), ('Dinner cruises', '/search?q=dinner%20cruise')])],
    'Transfers': [('Your transfer', [('Airport transfers', '/transfers?service=Airport%20transfer#transfer-enquiry'), ('Point to point', '/transfers?service=Point%20to%20point#transfer-enquiry'), ('Hourly chauffeur', '/transfers?service=Hourly%20chauffeur#transfer-enquiry')]),
                  ('Browse vehicles', [(t, f'/transfers?type={quote(t)}') for t in dict.fromkeys(c['type'] for c in CARS)])],
}


def mega(label, href):
    arrow = '<span class="arrow-r" aria-hidden="true">›</span>'
    if label == 'Destinations':
        def dest(l):
            img = f'<img src="{e(l["img"])}" alt="" loading="lazy">' if l.get('img') else '<span class="thumb tone-city"></span>'
            sub = 'United Arab Emirates' if l['group'] == 'uae' else 'International experiences'
            return f'<a class="mega-dest" href="/destinations/{l["id"]}" data-menu-loc="{l["id"]}">{img}<span><strong>{e(l["name"])}</strong><small>{sub}</small></span>{arrow}</a>'
        cols = (f'<div class="mega-col"><h3>UAE destinations</h3>{"".join(dest(l) for l in LIVE_UAE) or "<a class=mega-empty href=/activities>Explore UAE experiences</a>"}</div>'
                f'<div class="mega-col"><h3>International destinations</h3>{"".join(dest(l) for l in LIVE_INTL_MENU) or "<a class=mega-empty href=/contact>Ask about worldwide experiences</a>"}</div>'
                f'<div class="mega-col"><h3>Experiences</h3>{"".join(f"<a href=\"/search?q={quote(q)}\">{e(n)} {arrow}</a>" for n, q in EXPERIENCE_TERMS)}</div>'
                '<a class="mega-feature" href="/destinations/dubai"><small>ICONIC · MODERN · UNFORGETTABLE</small><strong>Explore Dubai</strong><p>Landmarks, desert adventures and memorable days in the city.</p><span class="mega-feature-btn">Explore Dubai →</span></a>')
    else:
        groups = ''.join(f'<div class="mega-col"><h3>{e(t)}</h3>{"".join(f"<a href=\"{e(h)}\">{e(n)} {arrow}</a>" for n, h in items)}</div>' for t, items in MENUS[label])
        cols = (f'<div class="mega-col mega-intro"><span class="kicker">Explore KWIKAR</span><h2>{label}</h2><p>Find your next experience or tell us what you have in mind.</p>'
                f'<a class="link" href="{href}">View all {label.lower()} →</a></div>{groups}'
                '<div class="mega-help"><strong>Need help planning?</strong><p>Share your dates and interests. Our team will confirm options and prices.</p>'
                '<a class="link" href="/contact">Contact KWIKAR →</a></div>')
    return f'<div class="mega" id="menu-{label.lower()}"><div class="mega-inner">{cols}</div></div>'


def shortcuts(active):
    prim = [('Activities', '/activities', 'ferris'), ('Holidays', '/holidays', 'bag'), ('Transfers', '/transfers', 'car'), ('Visas', '/visa', 'id')]
    more = [(t, h) for t, h, slug in [('Destinations', '/destinations', None), ('Cruises', '/activities/cruises', 'cruises'), ('Events', '/activities/events', 'events')] if not slug or CAT_COUNT.get(slug)]
    items = ''.join(f'<a class="sc{" on" if active == t else ""}" href="{h}"><span><svg viewBox="0 0 24 24">{ICON[i]}</svg></span>{t}</a>' for t, h, i in prim)
    extra = ''.join(f'<a href="{h}">{t}<span aria-hidden="true">→</span></a>' for t, h in more)
    return (f'<nav class="shortcuts" aria-label="Travel services">{items}'
            f'<details class="sc-more"><summary class="sc"><span><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg></span>More</summary>'
            f'<div class="sc-panel">{extra}</div></details></nav>')


def header(active):
    items = ''.join(
        f'<li class="nav-item{" is-active" if label == active else ""}">'
        f'<a class="nav-link" href="{href}"{" aria-current=\"page\"" if label == active else ""}>{icon(ic, color=col)}{label}</a>'
        f'<button class="nav-toggle" type="button" aria-label="Open {label} menu" aria-expanded="false" aria-controls="menu-{label.lower()}">{icon("chev", "chev")}</button>'
        f'{mega(label, href)}</li>'
        for label, href, ic, col in NAV)
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a href="/" class="logo" aria-label="KWIKAR home"><img src="/assets/img/logo.webp" alt="KWIKAR — Fast service that matters" width="147" height="50"></a>
    <nav class="main-nav" id="main-nav" aria-label="Main">
      <form class="mobile-search" role="search" action="/search"><label class="sr-only" for="m-q">Search experiences</label><input id="m-q" type="search" name="q" placeholder="Tour, city or activity"><button type="submit">Search</button></form>
      <ul class="nav-list">{items}</ul>
    </nav>
    <div class="header-actions">
      <form class="search" role="search" action="/search">
        {icon("search")}
        <input type="search" name="q" placeholder="Search destinations, attractions…" aria-label="Search destinations or activities">
        <button type="submit" class="search-btn" aria-label="Search"><svg viewBox="0 0 24 24">{ICON["search"]}</svg></button>
      </form>
      <a href="tel:+{PHONE}" class="icon-btn" aria-label="Call us"><svg viewBox="0 0 24 24" style="color:#2563eb">{ICON["phone"]}</svg></a>
      <a href="{e(wa("Hi KWIKAR, I have an enquiry."))}" class="icon-btn" aria-label="WhatsApp" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" style="color:#16a34a">{ICON["chat"]}</svg></a>
    </div>
    <button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="main-nav"><span></span><span></span><span></span></button>
  </div>
</header>
{shortcuts(active)}'''


FOOTER_LINKS = [('/destinations', 'Destinations'), ('/activities', 'Activities'), ('/destinations/dubai', 'Dubai'), ('/holidays', 'Holidays'),
                ('/transfers', 'Transfers'), ('/visa', 'Visa'), ('/contact', 'Contact'), ('/about', 'About'), ('/privacy', 'Privacy policy'),
                ('/terms', 'Terms & conditions'), ('/booking-information', 'Booking information'), ('/refund-policy', 'Refund & cancellation')]


def footer(path):
    links = ''.join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in FOOTER_LINKS)
    bn = [('Home', '/', 'home'), ('Search', '/search', 'search'), ('WhatsApp', wa('Hi KWIKAR, I would like help planning my trip.'), 'chat'), ('Help', '/contact', 'help')]
    bottom = ''.join(f'<a class="bn{" on" if (h == "/" and path == "/") or (h.startswith("/") and h != "/" and path.startswith(h)) else ""}" href="{e(h)}"{" target=_blank rel=noopener" if h.startswith("http") else ""}><svg viewBox="0 0 24 24">{ICON[i]}</svg>{t}</a>' for t, h, i in bn)
    return f'''<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-brand">
      <a href="/" aria-label="KWIKAR home"><img src="/assets/img/logo-white.webp" alt="KWIKAR" width="185" height="62" loading="lazy"></a>
      <p>Travel experiences, holidays, transfers and visa assistance across the UAE and beyond.</p>
    </div>
    <div class="footer-explore"><h4>Explore</h4><ul>{links}</ul></div>
    <div><h4>Contact</h4><ul>
      <li><a href="tel:+{PHONE}">{PHONE_FMT}</a></li>
      <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      <li><a href="{e(wa("Hi KWIKAR, I have an enquiry."))}" target="_blank" rel="noopener">WhatsApp us</a></li>
    </ul></div>
  </div>
  <div class="container footer-bottom">© <span data-year>{datetime.date.today().year}</span> Kwikar LLC-FZ · United Arab Emirates · {PHONE_FMT} · {EMAIL}</div>
</footer>
<nav class="bottom-nav" aria-label="Quick links">{bottom}</nav>
<a href="{e(wa("Hi KWIKAR, I would like help planning my trip."))}" class="wa-float" target="_blank" rel="noopener" aria-label="Chat with KWIKAR on WhatsApp">WhatsApp</a>'''


ORG_LD = {
    '@context': 'https://schema.org',
    '@graph': [
        {'@type': 'TravelAgency', '@id': SITE + '/#organization', 'name': 'KWIKAR', 'legalName': 'Kwikar LLC-FZ', 'url': SITE + '/',
         'logo': SITE + '/assets/img/logo.webp', 'image': SITE + '/assets/img/kwikar-share.webp', 'telephone': '+' + PHONE,
         'email': EMAIL, 'address': {'@type': 'PostalAddress', 'addressCountry': 'AE'}, 'areaServed': 'United Arab Emirates'},
        {'@type': 'WebSite', '@id': SITE + '/#website', 'url': SITE + '/', 'name': 'KWIKAR', 'publisher': {'@id': SITE + '/#organization'}},
    ],
}


def crumbs_ld(crumbs):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + (u if u != '/' else '/')} for i, (n, u) in enumerate(crumbs)]}


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def page(path, title, desc, main, active=None, scripts=('site',), noindex=False, body_class='', og_image='/assets/img/kwikar-share.webp',
         full_title=False, head_extra='', canonical=True, crumbs=None, og_type='website'):
    t = title if full_title else f'{title} | KWIKAR'
    url = SITE + (path if path != '/' else '/')
    head_extra = ld(ORG_LD) + (ld(crumbs_ld(crumbs)) if crumbs else '') + head_extra
    if GOOGLE_VERIFY:
        head_extra += f'<meta name="google-site-verification" content="{e(GOOGLE_VERIFY)}">'
    if BING_VERIFY:
        head_extra += f'<meta name="msvalidate.01" content="{e(BING_VERIFY)}">'
    if GA4_ID:
        head_extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={e(GA4_ID)}"></script>'
                       f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{e(GA4_ID)}');</script>")
    scripts_html = ''.join(f'<script src="/assets/js/{s}.js?v={VERSION}" defer></script>' for s in scripts)
    og = og_image if og_image.startswith('http') else SITE + og_image
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t)}</title>
<meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex">' if noindex else ''}
{f'<link rel="canonical" href="{url}">' if canonical else '<link rel="canonical" href="' + url + '">'}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="KWIKAR">
<meta property="og:title" content="{e(t)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon-blue.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css?v={VERSION}">
{head_extra}
</head>
<body class="{body_class}">
{header(active)}
<main id="main"{main[0]}>
{main[1]}
</main>
{footer(path)}
{scripts_html}
</body>
</html>
'''
    doc = localize(re.sub(r'\n{2,}', '\n', doc))
    dest = os.path.join(OUT, 'index.html' if path == '/' else path.strip('/') + ('' if path.endswith('.html') else '/index.html'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(doc)
    return dest


# ---------------------------------------------------------------- shared bits
def section_head(title, view_href=None, carousel=False, kicker=None):
    k = f'<span class="kicker">{e(kicker)}</span>' if kicker else ''
    acts = ''
    if view_href:
        acts += f'<a href="{view_href}" class="view-all">View all <svg viewBox="0 0 24 24">{ICON["out"]}</svg></a>'
    if carousel:
        acts += f'<button class="arrow" type="button" data-dir="-1" aria-label="Previous {e(title)}">‹</button><button class="arrow" type="button" data-dir="1" aria-label="Next {e(title)}">›</button>'
    return f'<div class="section-head"><div>{k}<h2>{e(title)}</h2></div>{f"<div class=head-actions>{acts}</div>" if acts else ""}</div>'


def page_hero(kicker, title, subtitle, image, cta=True):
    btn = f'<a class="btn mt" href="{e(wa(f"Hi KWIKAR, I would like to enquire about {title}"))}" target="_blank" rel="noopener">Plan with us ↗</a>' if cta else ''
    return f'''<section class="page-hero"><div class="container wide page-hero-grid">
  <div><span class="kicker">{e(kicker)}</span><h1>{e(title)}</h1><p>{e(subtitle)}</p>{btn}</div>
  <div class="photo"><img src="{e(image)}" alt="" fetchpriority="high"></div>
</div></section>'''


def holiday_card(h, extra_attr=''):
    return f'''<article class="box-card hoverable"{extra_attr}>
  <div class="media tone-sea"><img src="{e(h["img"])}" alt="{e(h["name"])}" loading="lazy"></div>
  <div class="box-body"><p class="eyebrow-blue">{e(h["country"])} · {h["nights"]} nights / {h["days"]} days</p><h3>{e(h["name"])}</h3>
  <p class="muted">Get a tailored quote for your dates.</p>
  <div class="actions"><a class="link" href="{e(wa(f"Hi KWIKAR, please quote {h['name']} for my travel dates."))}" target="_blank" rel="noopener">Request a quote ↗</a></div></div>
</article>'''


def car_card(c, extra_attr=''):
    return f'''<article class="box-card hoverable"{extra_attr}>
  <div class="media car-media"><img src="{e(c["img"])}" alt="{e(c["name"])}" loading="lazy"></div>
  <div class="box-body"><p class="eyebrow-blue">{e(c["type"])} · up to {c["pax"]} guests</p><h3>{e(c["name"])}</h3>
  <p class="muted">Pricing depends on the route and booking details. See the standard journey estimator above.</p>
  <div class="actions"><a class="link" href="#transfer-enquiry" data-pick="{e(c["name"])}" data-pick-target="t-vehicle">Request this vehicle ↗</a><span class="muted">·</span><a class="link" href="tel:+{PHONE}">Call</a></div></div>
</article>'''


# ---------------------------------------------------------------- data file for JS
def write_catalog_js():
    data = {
        'locations': [{'id': l['id'], 'name': l['name'], 'group': l['group'], 'img': l.get('img')} for l in LOCATIONS],
        'categories': CATEGORIES,
    }
    path = os.path.join(OUT, 'assets', 'js', 'catalog.js')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('/* Generated by build.py from catalog.json — do not edit by hand. */\nwindow.KW = window.KW || {};\nwindow.KW.data = ' + localize(json.dumps(data, ensure_ascii=False)) + ';\n')


# ================================================================= PAGES

def build_home():
    cities = [
        ('dubai', 'Dubai', 'Modern city, iconic experiences', U('1512453979798-5ea266f8880c'), 'tone-city'),
        ('abu-dhabi', 'Abu Dhabi', 'Culture, heritage and beyond', '/assets/img/hero-abu-dhabi.webp', 'tone-dusk'),
        ('fujairah', 'Fujairah', 'Coast and mountains', U('1506929562872-bb421503ef21'), 'tone-sea'),
        ('sharjah', 'Sharjah', 'Culture and heritage', U('1580674684081-7617fbf3d745'), 'tone-sand'),
        ('ras-al-khaimah', 'Ras Al Khaimah', 'Mountains, beaches and more', U('1451337516015-6b6e9a44a8a3'), 'tone-desert'),
        ('ajman', 'Ajman', 'Coastal experiences', U('1518684079-3c830dcef090'), 'tone-sea'),
        ('singapore', 'Singapore', 'Iconic sights and family fun', U('1525625293386-3f8f99389edd'), 'tone-sky'),
    ]
    city_cards = ''.join(f'''<a href="/destinations/{i}" class="city-card" data-city="{i}">
        <div class="media {tone}"><img src="{e(img)}" alt="{e(n)}" loading="lazy"></div>
        <div class="city-body"><p class="city-title">Things to do in <strong>{e(n)}</strong></p><p class="muted">{e(sub)}</p></div></a>''' for i, n, sub, img, tone in cities)

    # best-sellers: most-booked tours with a price and photo, straight from the tours API
    seen, best_list = set(), []
    for t in TOURS:
        if t.get('price') and t.get('img') and t['img'] not in seen:
            seen.add(t['img'])
            best_list.append(t)
    best = tour_cards(best_list[:12], short=True)
    cities = [c for c in cities if c[0] in LIVE_LOCS]

    hol = ''.join(f'''<a href="/holidays?country={quote(h["country"])}" class="box-card">
        <div class="media tone-sea"><img src="{e(h["img"])}" alt="{e(h["name"])}" loading="lazy"></div>
        <div class="box-body"><p class="tag">{e(h["country"])}</p><h3>{e(h["name"])}</h3><p class="muted">{h["nights"]} nights · Request a quote</p></div></a>''' for h in [x for x in HOLIDAYS if x.get('img')][:6])
    cars = ''.join(f'''<a href="/transfers" class="box-card">
        <div class="media tone-car"><img src="{e(c["img"])}" alt="{e(c["name"])}" loading="lazy"></div>
        <div class="box-body"><p class="tag">{e(c["type"])}</p><h3>{e(c["name"])}</h3><p class="muted">Up to {c["pax"]} passengers · Enquire for a quote</p></div></a>''' for c in CARS[:5])
    visas = ''.join(f'''<a href="/visa?type={quote(v["name"])}#visa-enquiry" class="visa-card"><p class="eyebrow-blue">UAE Tourist Visa</p><h3>{e(v["name"])}</h3>
        <p class="muted actions">{("From " + money(v["price"])) if v.get("price") else "Request a quote"} →</p></a>''' for v in [v for v in VISAS if re.search(r'30 Days|60 Days', v['name'])][:4])

    main = f'''
<section class="hero" aria-label="Featured destinations">
  <div class="hero-track" data-hero>
    <article class="hero-slide tone-desert">
      <img src="/assets/img/hero-desert.webp" alt="4x4 desert safari in the dunes at sunset" width="1122" height="1402">
      <div class="hero-content"><span class="eyebrow">Desert</span><h2 class="hero-title">Desert Adventures</h2><p>Dunes, thrills and unforgettable moments</p>
      <a href="/activities/desert-adventures" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <article class="hero-slide tone-city">
      <img src="/assets/img/hero-dubai.webp" srcset="/assets/img/hero-dubai-mobile.webp 820w, /assets/img/hero-dubai.webp 1672w" sizes="(max-width: 760px) 100vw, 65vw" alt="Dubai skyline and Burj Khalifa at night" fetchpriority="high" width="1672" height="941">
      <div class="hero-content"><span class="eyebrow">Dubai</span><h1 class="hero-title">Discover Dubai</h1><p>Iconic experiences, modern attractions and unforgettable moments with KWIKAR.</p>
      <a href="/destinations/dubai" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <article class="hero-slide tone-dusk">
      <img src="/assets/img/hero-abu-dhabi.webp" alt="Sheikh Zayed Grand Mosque in Abu Dhabi at sunset" width="1122" height="1402">
      <div class="hero-content"><span class="eyebrow">Abu Dhabi</span><h2 class="hero-title">Abu Dhabi Awaits</h2><p>Culture, heritage and world-class attractions</p>
      <a href="/destinations/abu-dhabi" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <div class="hero-dots" aria-label="Choose slide"></div>
  </div>
</section>

<section class="section" data-carousel><div class="container">
  {section_head("Best cities to visit", "/destinations", True)}
  <div class="track cols-3">{city_cards}</div>
</div></section>

<section class="section alt" data-carousel><div class="container">
  {section_head("Best-selling experiences", "/activities", True)}
  <div class="track cols-4">{best}</div>
</div></section>

<section class="section" data-carousel><div class="container">
  {section_head("Holiday packages", "/holidays", True)}
  <div class="track cols-4">{hol}</div>
</div></section>

<section class="section alt" data-carousel><div class="container">
  {section_head("Private transfers", "/transfers", True)}
  <div class="track cols-4">{cars}</div>
</div></section>

<section class="section"><div class="container">
  {section_head("Visa assistance", "/visa")}
  <div class="grid-4">{visas}</div>
</div></section>

<section class="section alt"><div class="container">
  {section_head("Why KWIKAR")}
  <div class="grid-4">
    <div class="why-card"><h3>Clear choices</h3><p class="muted">Compare options and current supplier prices on one page.</p></div>
    <div class="why-card"><h3>Book on WhatsApp</h3><p class="muted">Send your request in a minute — no account or online payment needed.</p></div>
    <div class="why-card"><h3>Confirmed before you pay</h3><p class="muted">Our team confirms availability and the final AED price first.</p></div>
    <div class="why-card"><h3>Local help</h3><p class="muted">Plan experiences and transfers across the UAE.</p></div>
  </div>
</div></section>'''
    page('/', 'UAE Attractions, Tours & Holidays | KWIKAR', 'Explore UAE attractions, holiday packages, private transfers and visa assistance with KWIKAR. Book on WhatsApp.',
         ('', main), active='Destinations', scripts=('site',), full_title=True,
         head_extra='<link rel="preload" as="image" href="/assets/img/hero-dubai.webp" media="(min-width: 761px)"><link rel="preload" as="image" href="/assets/img/hero-dubai-mobile.webp" media="(max-width: 760px)">')


def side_nav(location=None, current_cat=None, city=None):
    """Sidebar with only the categories and places that have tours."""
    base = city_tours(city) if city else TOURS
    cats = ''.join(f'<a href="/activities/{c["slug"]}"{" class=current" if c["slug"] == current_cat else ""}>{e(c["name"])}</a>'
                   for c in CATEGORIES if any(tf.matches_category(t, c['slug'], c['term']) for t in base))
    dests = ''.join(f'<a href="/activities/{c}"{" class=current" if c == city else ""}>{e(place_name(c) if c != "uae" else "More UAE")}</a>' for c in CITY_IDS)
    allhref = f'/activities/{city}' if city else '/activities'
    return f'''<aside class="list-sidebar">
  <h2>Explore</h2><nav aria-label="Activity types"><a href="{allhref}"{" class=current" if not current_cat else ""}>All experiences</a>{cats}</nav>
  <h2>Destinations</h2><nav aria-label="Destinations">{dests}</nav>
</aside>'''


def results_block(items, location=None, current_cat=None, city=None, dest_select=True):
    sel = '<label>Destination<select data-dest-select><option value="all">All destinations</option></select></label>' if dest_select else ''
    n = len(items)
    word = 'experience' if n == 1 else 'experiences'
    return f'''<div class="container wide list-body" id="results">
  {side_nav(location, current_cat, city)}
  <section aria-live="polite">
    <div class="list-controls"><div><h2 data-count-title>{n} {word}</h2><p data-note>Supplier prices, last checked {CHECKED}. Final price and availability are confirmed on WhatsApp.</p></div>
      <div class="list-selects">{sel}<label>Sort by<select data-sort><option value="popular">Popular</option><option value="low">Price low to high</option><option value="high">Price high to low</option></select></label></div></div>
    <div class="list-grid" data-grid>{tour_cards(items) or '<div class="empty" style="grid-column:1/-1"><p>No experiences are listed here right now.</p><p style="margin-top:10px"><a href="/activities">Browse all experiences</a> or <a href="/contact">ask our team</a>.</p></div>'}</div>
    <button class="btn ghost more-btn is-hidden" type="button" data-more>Show more experiences →</button>
  </section>
</div>'''


def search_form(placeholder='Search experiences'):
    return f'<form class="hero-search" role="search" data-list-search><input type="search" placeholder="{placeholder}" aria-label="Search experiences"><button type="submit">Search</button></form>'


def related_links(links):
    return ''.join(f'<a href="{h}">{e(t)} <small>{e(sub)}</small></a>' for t, h, sub in links)


def build_listings():
    # all activities
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')"><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Activities</nav>
  <span class="kicker">Tours · tickets · experiences</span><h1>Activities &amp; attractions</h1>
  <p>Discover tours, tickets and experiences across the UAE and beyond. Compare the options, then send your request on WhatsApp.</p>{search_form()}
</div></section>
{results_block(TOURS)}'''
    page('/activities', 'Activities & Attractions', 'Browse KWIKAR experiences and attractions by destination, category and price.',
         (' data-listing data-kind="standard"', main), active='Activities', scripts=('site', 'catalog', 'tours'),
         crumbs=[('Home', '/'), ('Activities', '/activities')])

    # search (not indexed)
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')"><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Search</nav>
  <h1>Search experiences</h1><p>Search tours, tickets and activities by name, destination or category.</p>{search_form("Tour, attraction or activity")}
</div></section>
{results_block(TOURS)}'''
    page('/search', 'Search Experiences', 'Search KWIKAR experiences and attractions.', (' data-listing data-kind="search"', main),
         scripts=('site', 'catalog', 'tours'), noindex=True)

    # activity categories
    for c in CATEGORIES:
        items = [t for t in TOURS if tf.matches_category(t, c['slug'], c['term'])]
        marine = c['slug'] in ('cruises', 'yachts')
        photo = next((t['img'] for t in items if t.get('img')), None)
        crumb = f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/activities">Activities</a> / {e(c["name"])}</nav>'
        intro = f'Explore {e(c["name"].lower())} and send your request on WhatsApp. Our team confirms current availability and the final price.'
        if marine or c['slug'] == 'events':
            switch = ''
            if marine:
                switch = '<p style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">' + ''.join(
                    f'<a class="chip{" selected" if s == c["slug"] else ""}" href="/activities/{s}"{" aria-current=page" if s == c["slug"] else ""}>Explore {s}</a>'
                    for s in ('cruises', 'yachts') if CAT_COUNT[s] or s == c['slug']) + '</p>'
            bg = photo or U('1518684079-3c830dcef090', 1600)
            hero = f'''<section class="banner-hero" style="background-image:url('{e(bg)}')"><div class="container wide">
  {crumb}<span class="kicker">{"Experiences on the water" if marine else "Explore by activity"}</span><h1>{e(c["name"])}</h1>
  <p>{intro}</p>{switch}{search_form()}
</div></section>'''
        else:
            hero = f'''<section class="page-hero cat-hero"><div class="container wide page-hero-grid">
  <div>{crumb}<span class="kicker">Explore by activity</span><h1>{e(c["name"])}</h1><p>{intro}</p>{search_form()}</div>
  <div class="cat-photo">{f'<img src="{e(photo)}" alt="" fetchpriority="high">' if photo else ''}<span>{len(items)} experience{'s' if len(items) != 1 else ''} to explore</span></div>
</div></section>'''
        places = [l for l in CITY_IDS if any(tf.city_of(t['loc']) == l for t in items)]
        place_row = ''
        if len(places) > 1:
            tiles = ''
            for p_ in places:
                lo = loc(p_)
                img = (lo.get('img') if lo else None) or ('/assets/img/hero-dubai-mobile.webp' if p_ == 'uae' else None)
                cnt = sum(1 for t in items if tf.city_of(t['loc']) == p_)
                tiles += (f'<button type="button" class="place-btn" data-place-id="{p_}">' + (f'<img src="{e(img)}" alt="" loading="lazy">' if img else '<div class="thumb tone-city"></div>')
                          + f'<span>{e(place_name(p_))}<small>{cnt} experience{"s" if cnt != 1 else ""}</small></span></button>')
            place_row = f'<section class="section" style="padding-bottom:0"><div class="container wide"><div class="section-head"><h2>Explore {e(c["name"].lower())} by destination</h2></div><div class="place-row">{tiles}</div></div></section>'
        rel = related_links([(x['name'], f'/activities/{x["slug"]}', '↗') for x in LIVE_CATS if x['slug'] != c['slug']])
        main = f'''{hero}
{place_row}
{results_block(items, current_cat=c["slug"])}
<section class="section alt"><div class="container wide"><div class="section-head"><h2>Keep exploring</h2></div><div class="related-links">{rel}</div></div></section>'''
        page(f'/activities/{c["slug"]}', f'{c["name"]} Experiences', f'Browse {c["name"].lower()} experiences with KWIKAR. Compare options and prices, then enquire for current availability.',
             (f' data-listing data-kind="category" data-category="{c["slug"]}" data-term="{e(c["term"])}"', main),
             active='Cruises' if c['slug'] == 'cruises' else 'Activities', scripts=('site', 'catalog', 'tours'), noindex=not items,
             crumbs=[('Home', '/'), ('Activities', '/activities'), (c['name'], f'/activities/{c["slug"]}')])

    # city category hubs: /activities/{city}
    for city in CITY_IDS:
        items = city_tours(city)
        name = place_name(city)
        h1 = 'More experiences in the UAE' if city == 'uae' else f'Activities in {name}'
        lo = loc(city)
        bg = (lo or {}).get('img') or next((t['img'] for t in items if t.get('img')), '/assets/img/hero-dubai.webp')
        if city == 'dubai':
            bg = '/assets/img/hero-dubai.webp'
        crumb_name = 'More UAE' if city == 'uae' else name
        main = f'''<section class="banner-hero" style="background-image:url('{e(bg)}')"><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/activities">Activities</a> / {e(crumb_name)}</nav>
  <span class="kicker">{len(items)} experience{"s" if len(items) != 1 else ""}</span><h1>{e(h1)}</h1>
  <p>All {e("UAE " if city == "uae" else "")}tours, tickets and experiences{"" if city == "uae" else " in " + e(name)} that you can book with KWIKAR. Filter, compare prices and send your request on WhatsApp.</p>{search_form()}
</div></section>
{results_block(items, city=city, dest_select=False)}'''
        page(f'/activities/{city}', h1, f'{h1}: compare {len(items)} tours, tickets and experiences with current supplier prices. Book with KWIKAR on WhatsApp.',
             (f' data-listing data-kind="city" data-city="{city}"', main), active='Activities', scripts=('site', 'catalog', 'tours'),
             crumbs=[('Home', '/'), ('Activities', '/activities'), (crumb_name, f'/activities/{city}')])


def build_destinations():
    """/destinations hub and one city hub per destination."""
    live_uae = [l for l in UAE if l['id'] in LIVE_LOCS]
    live_world = [l for l in REAL_LOCATIONS if l['group'] != 'uae' and l['id'] in LIVE_LOCS]
    uae_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in live_uae)
    intl_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in live_world)

    def count(lid):
        n = sum(1 for t in TOURS if t['loc'] == lid)
        return f'{n} experience{"s" if n != 1 else ""}'
    tiles = ''.join(f'''<a class="tile tone-city" href="/destinations/{l["id"]}">{f'<img src="{e(l["img"])}" alt="" loading="lazy">' if l.get("img") else ''}
      <span><strong>{e(l["name"])}</strong><small>{count(l["id"])} ↗</small></span></a>''' for l in live_uae)
    world = ''.join(f'<a href="/destinations/{l["id"]}"><strong>{e(l["name"])}</strong><small>{count(l["id"])} ↗</small></a>' for l in live_world)
    world_block = f'''<section class="section alt"><div class="container wide">
  <div class="section-head"><div><span class="kicker">Travel further</span><h2>Worldwide destinations</h2></div></div>
  <p class="section-intro">International experiences from our current catalogue. Ask our team about other countries.</p>
  <div class="world-grid">{world}</div>
</div></section>''' if world else ''
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')"><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Destinations</nav>
  <span class="kicker">KWIKAR destinations</span><h1>Where would you like to explore?</h1>
  <p>Browse by city, then choose an experience or ask our team to plan your day.</p>
  <form class="discover-form" action="/search" role="search">
    <label>Destination<select name="destination"><option value="">All destinations</option><optgroup label="United Arab Emirates">{uae_opts}</optgroup>{f'<optgroup label="Worldwide">{intl_opts}</optgroup>' if intl_opts else ''}</select></label>
    <label>What would you like to do?<input type="search" name="q" placeholder="Tour, attraction or activity" autocomplete="off"></label>
    <button type="submit">Find experiences →</button>
  </form>
</div></section>
<section class="section"><div class="container wide">
  <div class="section-head"><div><span class="kicker">Explore the Emirates</span><h2>United Arab Emirates</h2></div><a class="view-all" href="/activities">Browse by activity <svg viewBox="0 0 24 24">{ICON["out"]}</svg></a></div>
  <div class="tile-grid">{tiles}</div>
</div></section>
{world_block}'''
    page('/destinations', 'Destinations', 'Browse KWIKAR experiences by UAE city and worldwide destination.', ('', main),
         active='Destinations', crumbs=[('Home', '/'), ('Destinations', '/destinations')])

    for l in REAL_LOCATIONS:
        lid, name = l['id'], l['name']
        items = [t for t in TOURS if t['loc'] == lid]
        uae = l['group'] == 'uae'
        img = '/assets/img/hero-dubai.webp' if lid == 'dubai' else (l.get('img') or (items[0].get('img') if items else None))
        crumbs_html = f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/destinations">Destinations</a> / {e(name)}</nav>'
        if not items:
            main = f'''<section class="page-hero"><div class="container wide"><div style="padding:56px 0">{crumbs_html}
  <h1>Things to do in {e(name)}</h1><p>We don't have {e(name)} experiences listed right now. Tell us your dates and what you'd like to do, and our team will check options for you.</p>
  <p style="margin-top:22px;display:flex;gap:10px;flex-wrap:wrap"><a class="btn" href="{e(wa(f"Hi KWIKAR, I am looking for experiences in {name}."))}" target="_blank" rel="noopener">Ask on WhatsApp ↗</a><a class="btn ghost" href="/destinations">All destinations</a></p></div></div></section>'''
            page(f'/destinations/{lid}', f'Things to Do in {name}', f'Ask KWIKAR about experiences in {name}.', ('', main), active='Destinations', noindex=True)
            continue
        top = items[:8]
        cats = [(c['name'], f'/activities/{c["slug"]}', f'{sum(1 for t in items if tf.matches_category(t, c["slug"], c["term"]))} in {name}')
                for c in LIVE_CATS if any(tf.matches_category(t, c['slug'], c['term']) for t in items)]
        city = tf.city_of(lid)
        others = [(x['name'], f'/destinations/{x["id"]}', 'See experiences ↗') for x in REAL_LOCATIONS if x['id'] != lid and x['id'] in LIVE_LOCS and x['group'] == l['group']][:4]
        plan = ''
        if uae:
            plan = f'''<section class="section"><div class="container wide"><div class="section-head"><h2>Plan the rest of your trip</h2></div>
  <div class="related-links">{related_links([("Holiday packages", "/holidays?country=UAE", "Hotels, tours and transfers in one quote"), ("Private transfers", "/transfers", "Airport pickups and chauffeur service"), ("UAE tourist visas", "/visa", "14, 30 and 60 day visas")])}</div></div></section>'''
        main = f'''<section class="page-hero"><div class="container wide page-hero-grid">
  <div>{crumbs_html}
  <span class="kicker">{"United Arab Emirates" if uae else "Worldwide experiences"}</span>
  <h1>Things to do in {e(name)}</h1>
  <p>Compare {len(items)} tours, tickets and experiences in {e(name)} with current supplier prices. Choose your favourite and send your request on WhatsApp; our team confirms availability and the final price.</p>
  <p style="margin-top:20px"><a class="btn" href="/activities/{city}">See all {len(items)} experiences →</a></p></div>
  <div class="photo" data-hero-img>{f'<img src="{e(img)}" alt="Explore {e(name)}" fetchpriority="high">' if img else ''}</div>
</div></section>
<section class="section"><div class="container wide">
  {section_head(f"Popular things to do in {name}", f"/activities/{city}")}
  <div class="list-grid grid-cards-4">{tour_cards(top)}</div>
</div></section>
{f'''<section class="section alt"><div class="container wide"><div class="section-head"><h2>Browse {e(name)} by activity</h2></div><div class="related-links">{related_links(cats)}</div></div></section>''' if cats else ''}
{plan}
{f'''<section class="section alt"><div class="container wide"><div class="section-head"><h2>Explore more destinations</h2></div><div class="related-links">{related_links(others)}</div></div></section>''' if others else ''}'''
        page(f'/destinations/{lid}', f'Things to Do in {name}', f'Things to do in {name}: compare {len(items)} tours, attraction tickets and experiences with current prices. Book with KWIKAR on WhatsApp.',
             ('', main), active='Destinations', crumbs=[('Home', '/'), ('Destinations', '/destinations'), (name, f'/destinations/{lid}')])


# ---------------------------------------------------------------- product pages
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _plain(htmltext, n=None):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(htmltext or ''))).strip()
    return t[:n].rsplit(' ', 1)[0] + '…' if n and len(t) > n else t


def _hours(o):
    h = o.get('hours')
    if not h:
        return ''
    h = float(h)
    h = int(h) if h.is_integer() else h
    return f'{h} hour' + ('' if h == 1 else 's')


def _opt_price(o):
    if not o.get('price'):
        return 'On request'
    unit = 'booking' if o.get('unit') == 'trip' else (o.get('unit') or 'person')
    s = f'From {money(o["price"])} / {unit}'
    if o.get('tripFee') and o.get('adultBase'):
        s += f' + {money(o["tripFee"])} / booking'
    return s


def _transfer(o):
    k = o.get('transferKind')
    return {'private': 'Private transfer', 'sharing': 'Sharing transfer', 'meet_at_location': 'Meet at the venue'}.get(k, '—')


def build_product(t, d):
    tid = str(t['id'])
    x = EXTRAS.get(tid, {})
    path = tour_href(t)
    city = tf.city_of(t['loc'])
    cname = place_name(t['loc'])
    name = d.get('name') or t['name']
    offers = d.get('offers') or []
    priced = [o for o in offers if o.get('price')]
    low = min((o['price'] for o in priced), default=t.get('price'))
    high = max((o['price'] for o in priced), default=t.get('price'))
    low_unit = 'per booking' if (min(priced, key=lambda o: o['price']).get('unit') if priced else t.get('unit')) == 'trip' else 'per person'
    cats = d.get('categories') or t.get('cats') or []
    photos = [p for p in [d.get('img') or t.get('img')] + (d.get('photos') or []) if p][:3]
    faqs = [(f['q'], f['a']) for f in (d.get('faq') or []) if f.get('q') and f.get('a')]
    faqs += [tuple(f) for f in x.get('faqs', [])]
    kfaqs = [('How do I book this with KWIKAR?', f'Tap Check availability, choose your date, guests and option, and send the request on WhatsApp. Our team checks availability with the supplier and replies with the final AED price before you pay.'),
             ('Are there booking or card fees?', 'No. The price our team confirms on WhatsApp is the total you pay. KWIKAR does not add a separate booking or card fee.'),
             ('Can I cancel or change my booking?', 'Changes and refunds follow the supplier\'s rules for this experience, shown in the cancellation policy on this page. Contact us as soon as possible and we will check what applies to your booking.')]
    cancel = [c for c in (d.get('cancellation') or []) if c]
    h1 = x.get('h1') or name
    first_cat = next(iter(cats), '')

    # ---- head
    title = x.get('title')
    if not title:
        title = f'{name} – From {money(low)} | KWIKAR' if low else f'{name} | KWIKAR'
        if len(title) > 60:
            title = f'{name} | KWIKAR'
        if len(title) > 60:
            title = name[:60 - 10].rsplit(' ', 1)[0] + ' | KWIKAR'
    desc = x.get('description')
    if not desc:
        head_ = f'Book {name} in {cname}' + (f' from {money(low)} {low_unit}' if low else '') + '.'
        tails = [' Confirm availability and the final price with KWIKAR on WhatsApp.', ' Book with KWIKAR on WhatsApp.', '']
        opts = []
        if len(offers) > 1:
            n1, n2 = offers[0]['name'], offers[1]['name']
            opts = [f' {len(offers)} options, including {n1} and {n2}.', f' {len(offers)} options, including {n1}.', f' {len(offers)} options to choose from.']
        desc = None
        for o_ in opts + ['']:
            for t_ in tails:
                if len(head_ + o_ + t_) <= 160:
                    desc = head_ + o_ + t_
                    break
            if desc:
                break
        desc = desc or head_[:157] + '…'

    # ---- 3. quick answer + at a glance
    quick = x.get('quick_answer') or (
        f'You can book {name} in {cname} with KWIKAR' + (f' from {money(low)} {low_unit}' if low else '') + '. '
        + (f'There are {len(offers)} options to choose from. ' if len(offers) > 1 else '')
        + 'Send your preferred date and number of guests on WhatsApp; our team confirms availability and the final price before you pay.')
    glance = [('Location', cname)]
    hrs = sorted({float(o['hours']) for o in offers if o.get('hours')})
    if hrs:
        f_ = lambda h: str(int(h)) if h.is_integer() else str(h)
        glance.append(('Duration', f'{f_(hrs[0])} hour{"s" if hrs[0] != 1 else ""}' if len(hrs) == 1 else f'{f_(hrs[0])}–{f_(hrs[-1])} hours'))
    if low:
        glance.append(('Price', f'From {money(low)} {low_unit}' + (f' (up to {money(high)})' if high and high != low else '')))
    if len(offers) > 1:
        glance.append(('Options', f'{len(offers)} ticket or tour options'))
    if any(o.get('pickupRequired') for o in offers):
        glance.append(('Transfers', 'Hotel pickup options available'))
    elif offers and all(o.get('transferKind') == 'meet_at_location' for o in offers):
        glance.append(('Getting there', 'Meet at the venue (no transfer)'))
    if any(o.get('child') for o in offers):
        glance.append(('Children', 'Child prices available on some options'))
    days = set()
    for o in offers:
        days.update(o.get('daysOffered') or [])
    if days and len(days) < 7:
        glance.append(('Runs on', ', '.join(dd[:3].title() for dd in DAYS if dd in days)))
    elif days:
        glance.append(('Runs on', 'Every day'))
    if cancel:
        glance.append(('Cancellation', _plain(cancel[0], 110)))
    glance += [tuple(g) for g in x.get('at_a_glance', [])]
    glance_html = ''.join(f'<li><span>{e(k)}</span><strong>{e(v)}</strong></li>' for k, v in glance)

    # ---- 6. options table + which to choose
    rows = ''.join(f'<tr><th scope="row">{e(o["name"])}</th><td>{e(_hours(o) or "—")}</td><td>{e(_transfer(o))}</td><td class="num">{e(_opt_price(o))}</td></tr>' for o in offers)
    choose = []
    if len(priced) >= 2:
        cheap = min(priced, key=lambda o: o['price'])
        choose.append(('Lowest price', f'{cheap["name"]} ({_opt_price(cheap)})'))
        tr = [o for o in priced if o.get('pickupRequired')]
        if tr:
            tc = min(tr, key=lambda o: o['price'])
            if tc is not cheap:
                choose.append(('With hotel transfer', f'{tc["name"]} ({_opt_price(tc)})'))
        top_ = max(priced, key=lambda o: o['price'])
        if top_ is not cheap:
            choose.append(('Most premium', f'{top_["name"]} ({_opt_price(top_)})'))
    details = ''.join(f'<details class="opt-detail"><summary>{e(o["name"])}: details and inclusions</summary><div class="rich">{o["desc"]}</div></details>' for o in offers if o.get('desc'))
    options_html = ''
    if offers:
        options_html = f'''<section class="block" id="options"><h2>Compare the options</h2>
  <div class="table-wrap"><table class="opt-table"><thead><tr><th scope="col">Option</th><th scope="col">Duration</th><th scope="col">Transfer</th><th scope="col" class="num">Price</th></tr></thead><tbody>{rows}</tbody></table></div>
  {f'''<div class="choose"><h3>Which should I choose?</h3><ul>{"".join(f"<li><strong>{e(k)}:</strong> {e(v)}</li>" for k, v in choose)}</ul><p class="muted">Not sure? Ask our team on WhatsApp and we will suggest the right option for your group.</p></div>''' if choose else ''}
  {details}
</section>'''

    # ---- 7/8. included, visitor info (hand-written only)
    inc = ''
    if x.get('included') or x.get('not_included'):
        inc = '<section class="block"><h2>What\'s included</h2><div class="inc-grid">' + \
              (f'<div><h3>Included</h3><ul class="ticks">{"".join(f"<li>{e(i)}</li>" for i in x.get("included", []))}</ul></div>' if x.get('included') else '') + \
              (f'<div><h3>Not included</h3><ul class="crosses">{"".join(f"<li>{e(i)}</li>" for i in x.get("not_included", []))}</ul></div>' if x.get('not_included') else '') + '</div></section>'
    vis = ''
    if x.get('visitor_info'):
        vis = '<section class="block"><h2>Visitor information</h2><dl class="visitor">' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in x['visitor_info']) + '</dl></section>'
    best_for = f'<h3>Best for</h3><ul>{"".join(f"<li>{e(b)}</li>" for b in x["best_for"])}</ul>' if x.get('best_for') else ''
    tip = f'<aside class="kw-tip"><strong>KWIKAR tip</strong><p>{e(x["tip"])}</p></aside>' if x.get('tip') else ''

    # ---- 9. how it works
    itin = d.get('itinerary') or []
    if itin:
        how = '<section class="block"><h2>How it works</h2><ol class="steps">' + ''.join(f'<li><strong>{e(s_["name"])}</strong>{f"<p>{e(s_.get("desc"))}</p>" if s_.get("desc") else ""}</li>' for s_ in itin if s_.get('name')) + '</ol></section>'
    else:
        how = '''<section class="block"><h2>How booking works</h2><ol class="steps">
  <li><strong>Choose your option and date</strong><p>Compare the options above and pick a preferred date.</p></li>
  <li><strong>Send your request on WhatsApp</strong><p>Tap Check availability. Your request opens in WhatsApp so you can review and send it.</p></li>
  <li><strong>We confirm availability and price</strong><p>Our team checks with the supplier and replies with the final AED price.</p></li>
  <li><strong>Pay and get your confirmation</strong><p>Pay as agreed with our team and receive your booking details.</p></li></ol></section>'''

    faq_html = ''
    if faqs:
        faq_html += '<h3 class="faq-group">About this experience</h3>' + ''.join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)
    faq_html += '<h3 class="faq-group">Booking with KWIKAR</h3>' + ''.join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in kfaqs)

    terms = ''
    if cancel or d.get('terms'):
        terms = '<section class="block" id="terms"><h2>Cancellation and terms</h2>' + \
                (f'<h3>Cancellation policy</h3>{"".join(f"<p>{e(_plain(c))}</p>" for c in cancel)}' if cancel else '') + \
                (f'<h3>Supplier terms</h3><div class="rich">{d["terms"]}</div>' if d.get('terms') else '') + \
                '<p class="muted" style="margin-top:12px">Also read our <a href="/booking-information">booking information</a> and <a href="/refund-policy">refund and cancellation policy</a>.</p></section>'

    rel = [r for r in TOURS if r['id'] != t['id'] and tf.city_of(r['loc']) == city and set(r.get('cats') or []) & set(cats)]
    rel += [r for r in TOURS if r['id'] != t['id'] and tf.city_of(r['loc']) == city and r not in rel]
    rel = rel[:8]
    cat_links = [(c['name'], f'/activities/{c["slug"]}') for c in LIVE_CATS if tf.matches_category(t, c['slug'], c['term'])]
    hub_links = ''.join(f'<a class="chip" href="{h}">{e(n)} ↗</a>' for n, h in [(f'All experiences in {city_label(city)}', f'/activities/{city}')] + cat_links)
    checked = x.get('last_checked')
    checked_txt = (f'Details checked by our team on {datetime.date.fromisoformat(checked).strftime("%-d %b %Y")}. ' if checked else '') + f'Prices and options from the supplier, last checked {CHECKED}.'
    wa_q = wa(f'Hi KWIKAR, I would like to book {name}. Please share availability.')
    gallery = ''.join(f'<img src="{e(p)}" alt="{e(name)}{"" if i == 0 else f" – photo {i + 1}"}"{" fetchpriority=high" if i == 0 else " loading=lazy"} width="{800 if i == 0 else 400}" height="{600 if i == 0 else 300}">' for i, p in enumerate(photos))
    price_box = f'''<div class="book-card"><span>From</span><strong>{money(low) if low else "Price on request"}</strong><small>{low_unit + " · no booking or card fees" if low else "Our team will confirm the price"}</small>
  <button class="btn block" type="button" data-book>Check availability</button>
  <a class="btn ghost block wa-link" href="{e(wa_q)}" target="_blank" rel="noopener">Ask on WhatsApp</a>
  <a class="call" href="tel:+{PHONE}">Need help? Call {PHONE_FMT}</a>
  <p class="seller">Booking handled by Kwikar LLC-FZ, United Arab Emirates. Availability and final price confirmed before you pay.</p></div>'''

    main = f'''<div class="container wide tour-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/activities">Activities</a> / <a href="/activities/{city}">{e("More UAE" if city == "uae" else cname)}</a> / {e(name)}</nav>
  <h1>{e(h1)}</h1>
  <p class="tour-meta">{e(cname)}{f" · {e(first_cat)}" if first_cat else ""}</p>
  {f'<div class="gallery n{len(photos)}">{gallery}</div>' if photos else ''}
  <div class="tour-grid"><div>
    <section class="quick" aria-label="Quick answer"><p class="quick-answer">{e(quick)}</p><ul class="glance">{glance_html}</ul></section>
    {f'''<section class="block"><h2>Overview</h2><div class="rich">{d["description"]}</div>{best_for}</section>''' if d.get("description") or best_for else ''}
    {tip}
    {options_html}
    {inc}{vis}
    {how}
    <section class="block" id="faq"><h2>Questions</h2>{faq_html}</section>
    {terms}
    <p class="checked">{e(checked_txt)}</p>
  </div><aside>{price_box}</aside></div>
</div>
{f'''<section class="section alt"><div class="container wide">{section_head(f"More things to do in {city_label(city)}", f"/activities/{city}")}<div class="list-grid grid-cards-4">{tour_cards(rel)}</div><div class="chips" style="margin:24px 0 0">{hub_links}</div></div></section>''' if rel else ''}
<section class="final-cta"><div class="container wide"><div><h2>Ready to book {e(name)}?</h2><p>Send your date and guests. Our team replies on WhatsApp with availability and the final price.</p></div>
  <div class="final-cta-btns"><button class="btn" type="button" data-book>Check availability</button><a class="btn ghost" href="{e(wa_q)}" target="_blank" rel="noopener">WhatsApp us</a></div></div></section>
<div class="sticky-book"><div><span>From</span><strong>{money(low) if low else "On request"}</strong></div><button class="btn" type="button" data-book>Check availability</button></div>
<script type="application/json" id="kw-tour">{json.dumps({"id": t["id"], "name": name, "url": SITE + path, "offers": [{k: o.get(k) for k in ("name", "hours", "price", "unit", "child", "tripFee", "adultBase", "daysOffered", "pricingPeriods", "transferKind", "pickupRequired")} for o in offers]}, ensure_ascii=False).replace("</", "<\\/")}</script>'''

    # ---- structured data (matches what the page shows; no borrowed ratings)
    lds = ''
    product = {'@context': 'https://schema.org', '@type': 'Product', 'name': name, 'sku': tid, 'url': SITE + path,
               'description': _plain(d.get('description') or quick, 300), 'image': photos, 'category': first_cat or 'Tours & activities',
               'brand': {'@type': 'Brand', 'name': 'KWIKAR'}}
    if priced:
        product['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'AED', 'lowPrice': low, 'highPrice': high, 'offerCount': len(priced),
                             'availability': 'https://schema.org/InStock', 'url': SITE + path, 'seller': {'@id': SITE + '/#organization'}}
    lds += ld(product)
    lds += ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs + kfaqs]})
    page(path, title, desc, (' data-tour', main), active='Cruises' if tf.matches_category(t, 'cruises', '') else 'Activities',
         scripts=('site', 'catalog', 'tours'), body_class='tour-body', full_title=True, og_image=photos[0] if photos and photos[0].startswith('https://') else '/assets/img/kwikar-share.webp',
         noindex=not tf.visible(t), head_extra=lds,
         crumbs=[('Home', '/'), ('Activities', '/activities'), ('More UAE' if city == 'uae' else cname, f'/activities/{city}'), (name, path)])


def build_products():
    for t in ALL_TOURS:
        build_product(t, DETAILS.get(t['id']) or DETAILS.get(str(t['id'])) or {})


def build_gone():
    main = f'''<div class="status-page"><h1>This experience is no longer available</h1><p>The supplier has stopped offering it. Browse similar experiences or ask our team for an alternative.</p>
<div class="btns"><a class="btn" href="/activities">Browse experiences</a><a class="btn ghost" href="{e(wa("Hi KWIKAR, the experience I was looking for is no longer available. Can you suggest an alternative?"))}" target="_blank" rel="noopener">Ask on WhatsApp</a></div></div>'''
    page('/410.html', 'No longer available', 'This experience is no longer available.', ('', main), noindex=True)


def write_tours_json():
    """Same tours as the HTML, for filters and search in the browser."""
    items = [{'id': t['id'], 'name': t['name'], 'img': t.get('img'), 'cats': t.get('cats') or [], 'price': t.get('price'),
              'unit': t.get('unit'), 'loc': t['loc'], 'url': tour_href(t)} for t in TOURS]
    os.makedirs(os.path.join(OUT, 'assets', 'data'), exist_ok=True)
    json.dump({'checked': CHECKED, 'items': items}, open(os.path.join(OUT, 'assets', 'data', 'tours.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))



def build_holidays():
    countries = list(dict.fromkeys(h['country'] for h in HOLIDAYS))
    tiles = ''.join(f'<button type="button" class="filter-tile" data-filter="country" data-value="{e(c)}" aria-pressed="false"><img src="{e(next(h["img"] for h in HOLIDAYS if h["country"] == c))}" alt="" loading="lazy"><span>{e(c)}</span></button>' for c in countries)
    chips = ''.join(f'<button type="button" class="chip" data-filter="country" data-value="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in ['All'] + countries)
    groups = ''.join(f'''<section data-country="{e(c)}"><h2 class="group-title">{e(c)} holiday packages</h2>
      <div class="grid-3">{"".join(holiday_card(h) for h in HOLIDAYS if h["country"] == c)}</div></section>''' for c in countries)
    main = f'''{page_hero("Tailored getaways", "Holidays designed around you.", "Discover destinations and let us put together the right hotel, activities and transfers for your journey.", U("1525625293386-3f8f99389edd", 1400))}
<section class="section"><div class="container wide" data-filter-group="country">
  {section_head("Explore holiday ideas", kicker="Where to next")}
  <p class="section-intro">Holiday prices are confirmed by our team on WhatsApp for your dates and preferred hotels.</p>
  <div class="filter-tiles" aria-label="Holiday destinations">{tiles}</div>
  <div class="chips">{chips}</div>
  {groups}
</div></section>'''
    page('/holidays', 'Holiday Packages', 'Explore KWIKAR holiday ideas in the UAE, Singapore, Thailand and beyond. Enquire for a tailored travel quote.',
         ('', main), active='Holidays')


def build_transfers():
    est = {
        'airport': [
            {'name': 'DXB → Downtown / DIFC', 'from': 'Dubai International Airport (DXB)', 'to': 'Downtown Dubai / DIFC', 'rates': {'Mercedes E-Class': 150, 'Mercedes S-Class': 220, 'Mercedes V-Class': 250, 'Cadillac Escalade': 280}},
            {'name': 'DXB → Marina / JBR / Palm', 'from': 'Dubai International Airport (DXB)', 'to': 'Dubai Marina / JBR / Palm', 'rates': {'Mercedes E-Class': 180, 'Mercedes S-Class': None, 'Mercedes V-Class': None, 'Cadillac Escalade': None}},
        ],
        'intercity': [{'name': 'Dubai → Abu Dhabi', 'from': 'Dubai', 'to': 'Abu Dhabi', 'rates': {'Mercedes E-Class': 450, 'Mercedes S-Class': 650, 'Mercedes V-Class': 750, 'Cadillac Escalade': None}}],
        'hourly': {'Mercedes E-Class': 150, 'Mercedes S-Class': 280, 'Mercedes V-Class': 320, 'Cadillac Escalade': 350},
    }
    vehicles = ''.join(f'<option>{v}</option>' for v in est['hourly'])
    types = list(dict.fromkeys(c['type'] for c in CARS))
    chips = ''.join(f'<button type="button" class="chip" data-filter="type" data-value="{e(t)}" aria-pressed="false">{e(t)}</button>' for t in ['All'] + types)
    fleet = ''.join(car_card(c, f' data-type="{e(c["type"])}"') for c in CARS)
    car_opts = ''.join(f'<option>{e(c["name"])}</option>' for c in CARS)
    faqs = [('What happens if my flight is delayed?', 'Share your flight number when enquiring. We will confirm pickup arrangements and any waiting charges before booking.'),
            ('Can I change or cancel a booking?', 'Tell us as soon as possible. We will confirm the applicable change and cancellation terms for your chosen service before you pay.'),
            ('Can I extend my chauffeur booking?', 'Extensions depend on driver availability and will be quoted before you confirm.')]
    main = f'''{page_hero("Private mobility", "The journey is part of the experience.", "Airport pickups, point to point rides and chauffeur service with the car that fits your plans.", U("1518684079-3c830dcef090", 1400))}
<section class="section"><div class="container wide">
  {section_head("Estimate your transfer", kicker="Standard journeys")}
  <p class="section-intro">Select a standard journey and vehicle to see a starting AED price. Our team confirms your custom request and final price on WhatsApp. No online payment.</p>
  <div class="estimator" data-estimator='{e(json.dumps(est))}'>
    <div>
      <div class="tabs" role="group" aria-label="Transfer service"><button type="button" data-service="airport">Airport transfer</button><button type="button" data-service="hourly">Hourly chauffeur</button><button type="button" data-service="intercity">Inter-emirate</button></div>
      <label class="route-field">Standard route<select name="route"></select></label>
      <label class="hours-field" hidden>Hours (minimum 3)<input type="number" name="hours" min="3" max="12" value="3"></label>
      <label>Vehicle<select name="vehicle">{vehicles}</select></label>
    </div>
    <div class="est-result"><span>Indicative service price</span><strong data-out>—</strong><p class="sel" data-sel></p>
      <p>Custom locations, extra stops, child seats or waiting time are assessed by our team using your booking details. The final price is confirmed with you on WhatsApp.</p>
      <a class="btn" href="#transfer-enquiry" data-request>Request final quote →</a></div>
  </div>
</div></section>
<section class="section alt"><div class="container wide" data-filter-group="type">
  {section_head("Find your ride", kicker="Our fleet")}
  <p class="section-intro">Select a vehicle for your enquiry. Standard-route and hourly starting prices are shown in the estimator above.</p>
  <div class="chips">{chips}</div>
  <div class="grid-3">{fleet}</div>
</div></section>
<section class="section" id="transfer-enquiry"><div class="container wide service-layout">
  <div>{section_head("Request a transfer quote", kicker="Your ride")}
    <p>Tell us your route and any extras. Our team calculates your journey and sends the final AED quote on WhatsApp before you pay.</p>
    <h3>What your quote can include</h3>
    <p>Professional chauffeur, vehicle and route details. Fuel, tolls, waiting time and any additional charges are stated in your confirmed quote.</p></div>
  <form class="form" id="transfer-form" data-wa="Transfer enquiry — KWIKAR">
    <label>Service type<select name="service" data-label="Service" data-prefill="service"><option>Airport transfer</option><option>Point to point</option><option>Hourly chauffeur</option></select></label>
    <label>Vehicle<select name="vehicle" id="t-vehicle" data-label="Vehicle">{car_opts}</select></label>
    <label>Pickup location<input name="pickup" required data-label="Pickup"></label>
    <label>Drop-off location<input name="dropoff" required data-label="Drop-off"></label>
    <div class="two-fields"><label>Date<input type="date" name="date" required data-label="Date"></label><label>Time<input type="time" name="time" required data-label="Time"></label></div>
    <div class="two-fields"><label>Passengers<input type="number" name="pax" min="1" value="1" required data-label="Passengers"></label><label>Your name<input name="name" required autocomplete="name" data-label="Name"></label></div>
    <label>Extra stops, child seats or special requests<textarea name="special" data-label="Special requests" placeholder="Flight number, luggage, child seats…"></textarea></label>
    <button class="btn wa" type="submit">Send enquiry on WhatsApp ↗</button>
    <small>WhatsApp opens with your message so you can review and send it.</small>
  </form>
</div></section>
<section class="section alt"><div class="container">
  {section_head("Transfer questions")}
  {"".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)}
</div></section>'''
    page('/transfers', 'Private Transfers & Chauffeur', 'Arrange airport pickups, private transfers and chauffeur services in the UAE with KWIKAR.',
         ('', main), active='Transfers')


def build_visa():
    def vcard(v):
        tag = ''
        price = f'From {money(v["price"])} · final fee confirmed by our team' if v.get('price') else 'Fee on request'
        return f'''<article class="visa-card"><p class="eyebrow-blue">{tag}{e(v["stay"])} · Estimate {e(v["processing"])}</p><h3>{e(v["name"])}</h3>
          <p class="muted">{e(price)}</p><p class="actions" style="margin-top:14px"><a class="link" href="#visa-enquiry" data-pick="{e(v["name"])}" data-pick-target="v-type">Ask about this visa ↗</a></p></article>'''
    groups = ''.join(f'<h2 class="group-title">{g}</h2><div class="grid-3">{"".join(vcard(v) for v in VISAS if ("UAE" in v["name"]) == (g == "UAE visas"))}</div>' for g in ('UAE visas', 'Other destinations'))
    opts = ''.join(f'<option>{e(v["name"])}</option>' for v in VISAS)
    faqs = [('Is approval guaranteed?', 'No. Visa decisions are made by the issuing authority. We help you understand requirements and submit your application.'),
            ('How long does processing take?', 'Processing estimates vary by visa and application. We confirm the current expected timing before you apply.'),
            ('What if I need an urgent visa?', 'Ask us about express processing for your nationality and travel date. Availability and fees vary.')]
    main = f'''{page_hero("Travel documents", "Visa guidance, made easier.", "Tell us about your travel plans and our team will explain the visa options, documents and current processing estimates.", U("1436491865332-7a61a109cc05", 1400))}
<section class="section"><div class="container wide">
  {section_head("Find the right visa", kicker="Visa options")}
  <p class="section-intro">Starting prices are indicative for eligible applications. Our team confirms your actual visa cost after checking nationality, eligibility and processing. No payment is taken on this website.</p>
  {groups}
</div></section>
<section class="section alt" id="visa-enquiry"><div class="container wide service-layout">
  <div>{section_head("How to get started", kicker="Application")}
    <ol class="process"><li>Choose the visa and share your travel date.</li><li>We check eligibility and confirm current fees and document requirements on WhatsApp.</li><li>Share your documents through the channel our team confirms.</li><li>We update you on the application outcome.</li></ol>
    <h3>Documents to prepare</h3>
    <p>Typically a clear passport copy with at least six months validity and a recent colour photograph. Further documents may be required based on nationality and visa type. Please do not attach passport documents to this first message.</p></div>
  <form class="form" data-wa="Visa enquiry — KWIKAR">
    <label>Visa type<select name="type" id="v-type" data-label="Visa type" data-prefill="type">{opts}</select></label>
    <label>Nationality<input name="nationality" required data-label="Nationality"></label>
    <label>Planned travel date<input type="date" name="date" data-label="Travel date"></label>
    <label>Your name<input name="name" required autocomplete="name" data-label="Name"></label>
    <label>Phone or email<input name="contact" required data-label="Contact"></label>
    <button class="btn wa" type="submit">Enquire on WhatsApp ↗</button>
    <small>WhatsApp opens with your message so you can review and send it.</small>
  </form>
</div></section>
<section class="section"><div class="container">
  {section_head("Visa questions")}
  {"".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)}
</div></section>'''
    page('/visa', 'Visa Assistance', 'Explore UAE tourist visa options and enquire with KWIKAR about eligibility, documents and current processing times.',
         ('', main), active='Visas')


def build_contact():
    main = f'''{page_hero("Let's plan together", "Tell us where you're going.", "Our team can help with experiences, holidays, transfers and visa enquiries.", U("1512453979798-5ea266f8880c", 1400))}
<section class="section"><div class="container wide service-layout">
  <div>{section_head("We're here to help", kicker="Speak to our team")}
    <p>Share what you need and continue the conversation on WhatsApp.</p>
    <div class="contact-list">
      <a href="{e(wa("Hi KWIKAR, I have an enquiry."))}" target="_blank" rel="noopener">WhatsApp<strong>Chat with our team</strong></a>
      <a href="tel:+{PHONE}">Call us<strong>{PHONE_FMT}</strong></a>
      <a href="mailto:{EMAIL}">Email us<strong>{EMAIL}</strong></a>
    </div></div>
  <form class="form" data-wa="KWIKAR enquiry">
    <label>Your name<input name="name" required autocomplete="name" data-label="Name"></label>
    <label>Phone or email<input name="contact" required data-label="Contact"></label>
    <label>How can we help?<select name="service" data-label="Service" data-prefill="service"><option>Attractions</option><option>Holidays</option><option>Transfers</option><option>Visa</option><option>Other</option></select></label>
    <label>Travel details<textarea name="details" required rows="5" data-label="Details" placeholder="Dates, number of travellers and what you're looking for"></textarea></label>
    <button class="btn wa" type="submit">Continue on WhatsApp ↗</button>
    <small>WhatsApp opens with your message so you can review and send it.</small>
    <a href="#" class="alt-link" data-mail>Prefer email? Open your email app ↗</a>
  </form>
</div></section>'''
    page('/contact', 'Contact', 'Contact KWIKAR for attractions, holidays, private transfers and visa assistance.', ('', main))


def info(path, title, desc, body):
    page(path, title, desc, ('', f'<article class="info-page">{body}</article>'))


def build_info_pages():
    info('/about', 'About KWIKAR', 'Learn how KWIKAR helps travellers explore experiences, holidays, transfers and visa assistance in the UAE.', '''
<h1>Travel plans, made simpler.</h1>
<p>KWIKAR LLC-FZ helps travellers explore experiences, holiday ideas, private transfers and visa assistance in the UAE and beyond. Browse what interests you, then send your dates and requirements to our team on WhatsApp.</p>
<h2>How booking works</h2>
<ol><li>Explore experiences and indicative prices on this website.</li><li>Send your request on WhatsApp with your preferred date and number of guests.</li><li>Our team confirms availability, the final AED price and the booking terms before you pay.</li></ol>
<p>Questions? <a href="/contact">Get in touch</a>.</p>''')

    info('/privacy', 'Privacy', 'How KWIKAR uses the information you share in WhatsApp and email enquiries.', f'''
<h1>Privacy and enquiries</h1>
<p>KWIKAR LLC-FZ uses the details you share to respond to travel enquiries and arrange the services you request. This website does not take online payments and does not ask for or store card details.</p>
<h2>How our forms work</h2>
<p>Booking and enquiry forms on this website do not send your details to us directly. They open WhatsApp (or your email app) with a prepared message, which you can review before you send it.</p>
<h2>Information you share</h2>
<p>When you contact us we receive the details you choose to send — for example your name, phone number or email, selected tour or service, travel date, number of guests, pickup location and any notes. We use them to answer you, confirm availability and price, arrange your booking and contact you about it. Visa documents should be shared only after our team confirms the appropriate process.</p>
<h2>Other services</h2>
<p>WhatsApp and your email provider handle messages under their own terms. A tour or transfer supplier may receive the booking details needed to provide your service. Tour information and prices on this website are loaded from our supplier’s catalogue.</p>
<h2>Your questions</h2>
<p>Contact <a href="mailto:{EMAIL}">{EMAIL}</a> about your information or a data request. See our <a href="/booking-information">booking information</a>.</p>''')

    info('/terms', 'Terms & conditions', 'Terms for KWIKAR travel enquiries, quotes and confirmed bookings.', '''
<h1>Terms &amp; conditions</h1>
<p>Kwikar LLC-FZ provides travel enquiries and booking assistance for attractions, holidays, transfers and visas. Information and prices on this website may change with supplier availability, dates and guest details.</p>
<h2>Requests and quotes</h2>
<p>Sending a request on WhatsApp or by email does not reserve a service. Before you pay, KWIKAR confirms the final AED amount, what is included and the applicable supplier conditions. Prices shown on this website are indicative starting prices.</p>
<h2>Booking and payment</h2>
<p>No payment is taken on this website. Our team agrees the payment method with you directly. A booking is confirmed only when KWIKAR sends you a written confirmation (on WhatsApp or by email) with your booking details.</p>
<h2>Changes and cancellations</h2>
<p>Supplier rules for each service govern changes, cancellation charges and refunds. Read the specific tour conditions and our <a href="/refund-policy">refund and cancellation policy</a>. Visa issuance is determined by the issuing authority; processing times and approval are not guaranteed.</p>
<p>Read <a href="/booking-information">booking information</a> or <a href="/contact">contact our team</a> with questions.</p>''')

    info('/refund-policy', 'Refund & cancellation policy', 'How KWIKAR handles unavailable experiences, changes and refunds.', f'''
<h1>Refund &amp; cancellation policy</h1>
<h2>Before confirmation</h2>
<p>If an experience or service cannot be confirmed with the supplier, we tell you on WhatsApp and suggest alternatives. Nothing is booked until you accept the final quote.</p>
<h2>After confirmation</h2>
<p>Cancellation or changes to a confirmed booking depend on the supplier’s policy for that exact tour, option and travel date. The applicable conditions are shown on the tour page when provided by the supplier and are shared with your confirmation. Some tickets are non-refundable or carry a cancellation charge. Contact us as soon as possible with your booking details; we will check the supplier’s terms and tell you the refundable amount, if any, before processing a request.</p>
<h2>Other services</h2>
<p>Transfers, visas and holiday packages can have different cancellation terms. KWIKAR shares the applicable terms with your quote before you pay. Visa approval is determined by the issuing authority; an application fee may not be refundable after processing starts.</p>
<p>For assistance email <a href="mailto:{EMAIL}">{EMAIL}</a> or <a href="/contact">contact our team</a>. See <a href="/booking-information">how booking works</a>.</p>''')

    info('/booking-information', 'Booking information', 'How booking with KWIKAR works — requests on WhatsApp, confirmation and payment.', '''
<h1>Booking information</h1>
<p>Prices are shown in AED. Some services need a quote before we can confirm the total.</p>
<h2>Tours and attractions</h2>
<p>Choose an experience, option, date and guests, then tap <strong>Send booking request on WhatsApp</strong>. The prices shown are the supplier’s recommended prices and are indicative. Our team checks availability and age-based prices for your date, then replies with the final AED amount and how to pay. Your booking is confirmed when we send your confirmation and voucher reference.</p>
<h2>Transfers, visas and holidays</h2>
<p>Send an enquiry with your travel details. Transfers and holidays are arranged on WhatsApp. For visas, our team checks requirements and pricing for your nationality first. A starting price on this website does not reserve a vehicle, visa or holiday.</p>
<h2>Fees</h2>
<p>The confirmed AED quote is the total you pay. There is no separate booking or card fee from KWIKAR.</p>
<p>Read our <a href="/terms">terms</a>, <a href="/refund-policy">refund and cancellation policy</a> and <a href="/privacy">privacy policy</a>. Questions? <a href="/contact">Contact KWIKAR</a>.</p>''')


def build_404():
    main = f'''<div class="status-page"><h1>Page not found</h1><p>The page you are looking for has moved or no longer exists.</p>
<div class="btns"><a class="btn" href="/">Go to homepage</a><a class="btn ghost" href="/activities">Browse experiences</a><a class="btn wa" href="{e(wa("Hi KWIKAR, I need help finding something on your website."))}" target="_blank" rel="noopener">Ask on WhatsApp</a></div></div>'''
    page('/404.html', 'Page not found', 'This page could not be found.', ('', main), noindex=True)


def build_seo_files():
    """Split sitemaps (pages / hubs / products), robots.txt and the .htaccess tour redirects."""
    today = datetime.date.today().isoformat()

    def urlset(paths):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + ''.join(f'  <url><loc>{SITE}{p_}</loc><lastmod>{today}</lastmod></url>\n' for p_ in paths) + '</urlset>\n')
    pages = ['/', '/holidays', '/transfers', '/visa', '/contact', '/about', '/privacy', '/terms', '/booking-information', '/refund-policy']
    hubs = (['/destinations', '/activities'] + [f'/destinations/{l["id"]}' for l in REAL_LOCATIONS if l['id'] in LIVE_LOCS]
            + [f'/activities/{c}' for c in CITY_IDS] + [f'/activities/{c["slug"]}' for c in LIVE_CATS])
    products = [tour_href(t) for t in ALL_TOURS if tf.visible(t)]
    for name, paths in (('pages', pages), ('hubs', hubs), ('products', products)):
        open(os.path.join(OUT, f'sitemap-{name}.xml'), 'w').write(urlset(paths))
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <sitemap><loc>{SITE}/sitemap-{n}.xml</loc><lastmod>{today}</lastmod></sitemap>\n' for n in ('pages', 'hubs', 'products'))
        + '</sitemapindex>\n')
    rules = 'Disallow: /search\nDisallow: /api/\n'
    open(os.path.join(OUT, 'robots.txt'), 'w').write(
        f'# Search engines and AI search (ChatGPT search = OAI-SearchBot) may crawl the site.\n'
        f'User-agent: *\nAllow: /\n{rules}\nUser-agent: OAI-SearchBot\nAllow: /\n{rules}\nSitemap: {SITE}/sitemap.xml\n')

    # .htaccess: old /tour/{id} and /tour.html?id= addresses -> new address (one hop); removed tours -> 410 Gone
    lines = []
    for tid, path in sorted(SLUGS.items(), key=lambda kv: int(kv[0])):
        if tid in LIVE_IDS:
            lines += [f'RewriteRule ^(?:ar/)?tour/{tid}/?$ {path} [R=301,L]',
                      f'RewriteCond %{{QUERY_STRING}} (?:^|&)id={tid}(?:&|$)',
                      f'RewriteRule ^tour\\.html$ {path}? [R=301,L]']
        else:
            lines += [f'RewriteRule ^(?:ar/)?tour/{tid}/?$ - [G,L]', f'RewriteRule ^{path.strip("/")}/?$ - [G,L]']
    tpl = open(os.path.join(ROOT, 'htaccess.template'), encoding='utf-8').read()
    open(os.path.join(OUT, '.htaccess'), 'w', encoding='utf-8').write(tpl.replace('# {{TOUR_RULES}}', '\n'.join(lines)))


def clean_output():
    """Remove previously generated pages so renamed or removed pages don't linger."""
    import shutil
    keep = {'assets', 'api'}
    for name in os.listdir(OUT):
        full = os.path.join(OUT, name)
        if os.path.isdir(full) and name not in keep and not name.startswith('.'):
            shutil.rmtree(full)
        elif os.path.isfile(full) and (name.endswith(('.html', '.xml')) or name in ('robots.txt', '.htaccess')):
            os.remove(full)


if __name__ == '__main__':
    clean_output()
    write_catalog_js()
    write_tours_json()
    build_home()
    build_listings()
    build_destinations()
    build_products()
    build_holidays()
    build_transfers()
    build_visa()
    build_contact()
    build_info_pages()
    build_404()
    build_gone()
    build_seo_files()
    n = sum(len([f for f in fs if f.endswith('.html')]) for _, _, fs in os.walk(OUT))
    print(f'Built {n} HTML pages ({len(ALL_TOURS)} tour pages) into {OUT}')
