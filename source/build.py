#!/usr/bin/env python3
"""
KWIKAR static site generator.

Reads data/catalog.json and writes plain HTML pages into ../kwikar-site/public_html.
Run:  python3 build.py
Edit holidays, cars, visas or destinations in data/catalog.json, then run again.
"""
import json, html, os, re, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, '..', 'public_html'))
SITE = 'https://kwikar.com'
PHONE = '971505599243'
PHONE_FMT = '+971 50 559 9243'
EMAIL = 'info@kwikar.com'
VERSION = datetime.datetime.now().strftime('%Y%m%d%H%M')

cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
LOCATIONS = [l for l in cat['locations'] if l['id'] != 'other']
HOLIDAYS, CARS, VISAS, FALLBACK = cat['holidays'], cat['cars'], cat['visas'], cat['fallback']
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
UAE = [l for l in LOCATIONS if l['group'] == 'uae']
INTL_MENU = [loc(i) for i in ['singapore', 'bali', 'thailand', 'malaysia'] if loc(i)]
EXPERIENCE_TERMS = [('City Tours', 'city tour'), ('Theme Parks', 'theme park'), ('Desert Adventures', 'desert'), ('Water Activities', 'water'),
                    ('Cultural Experiences', 'museum'), ('Family Activities', 'family'), ('Luxury Experiences', 'luxury'), ('Attraction Tickets', 'ticket')]

NAV = [
    ('Destinations', '/attractions', 'flag', '#ff6a21'),
    ('Activities', '/activities', 'mountain', '#08b9bb'),
    ('Holidays', '/holidays', 'plane', '#5969e9'),
    ('Visas', '/visa', 'doc', '#ff9516'),
    ('Cruises', '/activities/cruises', 'ship', '#406bf2'),
    ('Transfers', '/transfers', 'car', '#2aba87'),
]
MENUS = {
    'Activities': [('Explore activities', [('City tours', '/activities/city-tours'), ('Desert adventures', '/activities/desert-adventures'), ('Theme parks', '/activities/theme-parks'), ('Water activities', '/activities/water-activities'), ('Events', '/activities/events')]),
                   ('Popular choices', [('Burj Khalifa', '/search?q=Burj%20Khalifa'), ('Dubai desert safari', '/search?q=desert%20safari'), ('Abu Dhabi tours', '/destinations/abu-dhabi'), ('Yachts', '/activities/yachts')])],
    'Holidays': [('Holiday destinations', [(c, f'/holidays?country={quote(c)}') for c in dict.fromkeys(h['country'] for h in HOLIDAYS)]),
                 ('Plan your trip', [('All holiday packages', '/holidays'), ('Request a tailored holiday', '/contact')])],
    'Visas': [('UAE visa options', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' in v['name']]),
              ('Other visa assistance', [(v['name'], f"/visa?type={quote(v['name'])}#visa-enquiry") for v in VISAS if 'UAE' not in v['name']])],
    'Cruises': [('Cruise experiences', [('All cruises', '/activities/cruises'), ('Dubai Marina cruises', '/search?q=marina%20cruise'), ('Dhow cruises', '/search?q=dhow%20cruise'), ('Dinner cruises', '/search?q=dinner%20cruise')]),
                ('On the water', [('Yacht experiences', '/activities/yachts'), ('Water activities', '/activities/water-activities')])],
    'Transfers': [('Your transfer', [('Airport transfers', '/transfers?service=Airport%20transfer#transfer-enquiry'), ('Point to point', '/transfers?service=Point%20to%20point#transfer-enquiry'), ('Hourly chauffeur', '/transfers?service=Hourly%20chauffeur#transfer-enquiry')]),
                  ('Browse vehicles', [(t, f'/transfers?type={quote(t)}') for t in dict.fromkeys(c['type'] for c in CARS)])],
}


def mega(label, href):
    arrow = '<span class="arrow-r" aria-hidden="true">›</span>'
    if label == 'Destinations':
        def dest(l):
            img = f'<img src="{e(l["img"])}" alt="" loading="lazy">' if l.get('img') else '<span class="thumb tone-city"></span>'
            sub = 'United Arab Emirates' if l['group'] == 'uae' else 'International experiences'
            return f'<a class="mega-dest" href="/destinations/{l["id"]}">{img}<span><strong>{e(l["name"])}</strong><small>{sub}</small></span></a>'
        cols = (f'<div class="mega-col"><h3>UAE destinations</h3>{"".join(dest(l) for l in UAE)}</div>'
                f'<div class="mega-col"><h3>International</h3>{"".join(dest(l) for l in INTL_MENU)}<a href="/attractions">All destinations {arrow}</a></div>'
                f'<div class="mega-col"><h3>Experiences</h3>{"".join(f"<a href=\"/search?q={quote(q)}\">{e(n)} {arrow}</a>" for n, q in EXPERIENCE_TERMS)}</div>'
                '<a class="mega-feature" href="/destinations/dubai"><small>ICONIC · MODERN · UNFORGETTABLE</small><strong>Explore Dubai</strong><p>Landmarks, desert adventures and memorable days in the city.</p></a>')
    else:
        groups = ''.join(f'<div class="mega-col"><h3>{e(t)}</h3>{"".join(f"<a href=\"{e(h)}\">{e(n)} {arrow}</a>" for n, h in items)}</div>' for t, items in MENUS[label])
        cols = (f'<div class="mega-col mega-intro"><span>Explore KWIKAR</span><h2>{label}</h2><p>Find your next experience or tell us what you have in mind.</p>'
                f'<a class="link" href="{href}">View all {label.lower()} →</a></div>{groups}'
                '<div class="mega-help"><strong>Need help planning?</strong><p>Share your dates and interests. Our team will confirm options and prices on WhatsApp.</p>'
                '<a class="link" href="/contact">Contact KWIKAR →</a></div>')
    return f'<div class="mega" id="menu-{label.lower()}"><div class="mega-inner">{cols}</div></div>'


def shortcuts(active):
    prim = [('Activities', '/activities', 'ferris'), ('Holidays', '/holidays', 'bag'), ('Transfers', '/transfers', 'car'), ('Visas', '/visa', 'id')]
    more = [('Destinations', '/attractions'), ('Cruises', '/activities/cruises'), ('Events', '/activities/events')]
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


FOOTER_LINKS = [('/attractions', 'Destinations'), ('/activities', 'Activities'), ('/destinations/dubai', 'Dubai'), ('/holidays', 'Holidays'),
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


def page(path, title, desc, main, active=None, scripts=('site',), noindex=False, body_class='', og_image='/assets/img/kwikar-share.webp',
         full_title=False, head_extra='', canonical=True):
    t = title if full_title else f'{title} | KWIKAR'
    url = SITE + (path if path != '/' else '/')
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
<meta property="og:type" content="website">
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
    btn = f'<a class="btn wa mt" href="{e(wa(f"Hi KWIKAR, I would like to enquire about {title}"))}" target="_blank" rel="noopener">Plan with us on WhatsApp ↗</a>' if cta else ''
    return f'''<section class="page-hero"><div class="container wide page-hero-grid">
  <div><span class="kicker">{e(kicker)}</span><h1>{e(title)}</h1><p>{e(subtitle)}</p>{btn}</div>
  <div class="photo"><img src="{e(image)}" alt="" fetchpriority="high"></div>
</div></section>'''


def holiday_card(h, extra_attr=''):
    tag = f'<span class="badge">{e(h["tag"])}</span> ' if h.get('tag') else ''
    return f'''<article class="box-card hoverable"{extra_attr}>
  <div class="media tone-sea"><img src="{e(h["img"])}" alt="{e(h["name"])}" loading="lazy"></div>
  <div class="box-body"><p class="tag">{tag}{e(h["country"])} · {h["nights"]} nights / {h["days"]} days</p><h3>{e(h["name"])}</h3>
  <p class="muted">Get a tailored quote for your dates and preferred hotels.</p>
  <div class="actions"><a class="link" href="{e(wa(f"Hi KWIKAR, please quote {h['name']} for my travel dates."))}" target="_blank" rel="noopener">Request a quote on WhatsApp ↗</a></div></div>
</article>'''


def car_card(c, extra_attr=''):
    return f'''<article class="box-card hoverable"{extra_attr}>
  <div class="media tone-car"><img src="{e(c["img"])}" alt="{e(c["name"])}" loading="lazy"></div>
  <div class="box-body"><p class="tag">{e(c["type"])} · up to {c["pax"]} guests</p><h3>{e(c["name"])}</h3>
  <p class="muted">Price depends on route and timing — see the estimator above or ask for a quote.</p>
  <div class="actions"><a class="link" href="#transfer-enquiry" data-pick="{e(c["name"])}" data-pick-target="t-vehicle">Request this vehicle ↗</a><a class="link" href="tel:+{PHONE}">Call</a></div></div>
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

    # best-sellers come only from the live tours feed (tours.js); placeholders while it loads
    best = ''.join('<div class="exp-card skeleton" aria-hidden="true"><div class="media tall"></div><div class="line short"></div><div class="line"></div><div class="line short"></div></div>' for _ in range(4))

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
      <img src="/assets/img/hero-desert.webp" alt="4x4 desert safari in the dunes at sunset">
      <div class="hero-content"><span class="eyebrow">Desert</span><h2 class="hero-title">Desert Adventures</h2><p>Dunes, thrills and unforgettable moments</p>
      <a href="/activities/desert-adventures" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <article class="hero-slide tone-city">
      <img src="/assets/img/hero-dubai.webp" srcset="/assets/img/hero-dubai-mobile.webp 820w, /assets/img/hero-dubai.webp 1672w" sizes="(max-width: 760px) 100vw, 65vw" alt="Dubai skyline and Burj Khalifa at night" fetchpriority="high">
      <div class="hero-content"><span class="eyebrow">Dubai</span><h1 class="hero-title">Discover Dubai</h1><p>Iconic experiences, modern attractions and unforgettable moments with KWIKAR.</p>
      <a href="/destinations/dubai" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <article class="hero-slide tone-dusk">
      <img src="/assets/img/hero-abu-dhabi.webp" alt="Sheikh Zayed Grand Mosque in Abu Dhabi at sunset">
      <div class="hero-content"><span class="eyebrow">Abu Dhabi</span><h2 class="hero-title">Abu Dhabi Awaits</h2><p>Culture, heritage and world-class attractions</p>
      <a href="/destinations/abu-dhabi" class="btn-hero">Explore <span aria-hidden="true">→</span></a></div>
    </article>
    <div class="hero-dots" aria-label="Choose slide"></div>
  </div>
</section>

<section class="section" data-carousel><div class="container">
  {section_head("Best cities to visit", "/attractions", True)}
  <div class="track cols-3">{city_cards}</div>
</div></section>

<section class="section alt" data-carousel><div class="container">
  {section_head("Best-selling experiences", "/activities", True)}
  <div class="track cols-4" data-home-best aria-live="polite">{best}</div>
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
    <div class="why-card"><h3>Clear choices</h3><p class="muted">Explore experiences and current supplier prices.</p></div>
    <div class="why-card"><h3>Book on WhatsApp</h3><p class="muted">Send your request in a minute — no account or online payment needed.</p></div>
    <div class="why-card"><h3>Confirmed before you pay</h3><p class="muted">Our team confirms availability and the final AED price first.</p></div>
    <div class="why-card"><h3>Local help</h3><p class="muted">Plan experiences and transfers across the UAE.</p></div>
  </div>
</div></section>'''
    ld = {'@context': 'https://schema.org', '@type': 'TravelAgency', 'name': 'KWIKAR', 'legalName': 'Kwikar LLC-FZ', 'url': SITE, 'logo': SITE + '/assets/img/logo.webp',
          'image': SITE + '/assets/img/kwikar-share.webp', 'telephone': '+' + PHONE, 'email': EMAIL, 'address': {'@type': 'PostalAddress', 'addressCountry': 'AE'}}
    page('/', 'UAE Attractions, Tours & Holidays | KWIKAR', 'Explore UAE attractions, holiday packages, private transfers and visa assistance with KWIKAR. Book on WhatsApp.',
         ('', main), active='Destinations', scripts=('site', 'catalog', 'tours'), full_title=True,
         head_extra=f'<link rel="preload" as="image" href="/assets/img/hero-dubai.webp" media="(min-width: 761px)"><link rel="preload" as="image" href="/assets/img/hero-dubai-mobile.webp" media="(max-width: 760px)"><script type="application/ld+json">{json.dumps(ld)}</script>')


def side_nav(location=None, current_cat=None):
    cats = ''.join(f'<a href="/activities/{c["slug"]}" data-cat="{c["slug"]}"{" class=current" if c["slug"] == current_cat else ""}>{e(c["name"])}</a>' for c in CATEGORIES)
    dests = ''.join(f'<a href="/destinations/{l["id"]}" data-dest="{l["id"]}"{" class=current" if l["id"] == location else ""}>{e(l["name"])}</a>' for l in LOCATIONS[:14])
    allhref = f'/destinations/{location}' if location else '/activities'
    return f'''<aside class="list-sidebar">
  <h2>Explore</h2><nav data-side-cats aria-label="Activity types"><a href="{allhref}"{" class=current" if not current_cat else ""}>All experiences</a>{cats}</nav>
  <h2>Destinations</h2><nav data-side-dests aria-label="Destinations">{dests}</nav>
</aside>'''


def results_block(location=None, current_cat=None, dest_select=True):
    sel = '<label>Destination<select data-dest-select><option value="all">All destinations</option></select></label>' if dest_select else ''
    return f'''<div class="container wide list-body" id="results">
  {side_nav(location, current_cat)}
  <section aria-live="polite">
    <div class="list-controls"><div><h2 data-count-title>Loading experiences…</h2><p data-note>Loading current experiences…</p></div>
      <div class="list-selects">{sel}<label>Sort by<select data-sort><option value="popular">Popular</option><option value="low">Price low to high</option><option value="high">Price high to low</option></select></label></div></div>
    <div class="list-grid" data-grid></div>
    <button class="btn ghost more-btn is-hidden" type="button" data-more>Show more experiences →</button>
  </section>
</div>'''


def search_form(placeholder='Search experiences'):
    return f'<form class="hero-search" role="search" data-list-search><input type="search" placeholder="{placeholder}" aria-label="Search experiences"><button type="submit">Search</button></form>'


def build_listings():
    # all activities
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')" data-hero-img><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Activities</nav>
  <span class="kicker">Tours · tickets · experiences</span><h1>Activities &amp; attractions</h1>
  <p>Discover tours, tickets and experiences across the UAE and beyond. Choose your favourite and book on WhatsApp.</p>{search_form()}
</div></section>
{results_block()}'''
    page('/activities', 'Activities & Attractions', 'Browse KWIKAR experiences and attractions by destination, category and price.',
         (' data-listing data-kind="standard"', main), active='Activities', scripts=('site', 'catalog', 'tours'))

    # search
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')"><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / Search</nav>
  <h1>Search experiences</h1><p>Search tours, tickets and activities by name, destination or category.</p>{search_form("Tour, attraction or activity")}
</div></section>
{results_block()}'''
    page('/search', 'Search Experiences', 'Search KWIKAR experiences and attractions.', (' data-listing data-kind="search"', main),
         scripts=('site', 'catalog', 'tours'), noindex=True)

    # categories
    for c in CATEGORIES:
        marine = c['slug'] in ('cruises', 'yachts')
        img = U('1777231755912-109c409e760e', 1600) if c['slug'] == 'events' else ('/assets/img/hero-dubai.webp' if not marine else U('1518684079-3c830dcef090', 1600))
        kicker = 'Experiences on the water' if marine else 'Explore by activity'
        switch = ''
        if marine:
            switch = '<p style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">' + ''.join(
                f'<a class="chip{" selected" if s == c["slug"] else ""}" href="/activities/{s}"{" aria-current=page" if s == c["slug"] else ""}>Explore {s}</a>' for s in ('cruises', 'yachts')) + '</p>'
        related = ''.join(f'<a href="/activities/{x["slug"]}" data-cat="{x["slug"]}">{e(x["name"])} <small>↗</small></a>' for x in CATEGORIES if x['slug'] != c['slug'])
        main = f'''<section class="banner-hero" style="background-image:url('{e(img)}')" data-hero-img><div class="container wide">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/activities">Activities</a> / {e(c["name"])}</nav>
  <span class="kicker">{kicker}</span><h1>{e(c["name"])}</h1>
  <p>Explore {e(c["name"].lower())} and enquire with our team on WhatsApp for current availability.</p>{switch}{search_form()}
</div></section>
<section class="section is-hidden" data-places style="padding-bottom:0"><div class="container wide"><div class="section-head"><h2>Explore {e(c["name"].lower())} by destination</h2></div><div class="place-row"></div></div></section>
{results_block(current_cat=c["slug"])}
<section class="section alt" data-related-cats><div class="container wide"><div class="section-head"><h2>Keep exploring</h2></div><div class="related-links">{related}</div></div></section>'''
        page(f'/activities/{c["slug"]}', f'{c["name"]} Experiences', f'Browse {c["name"].lower()} experiences with KWIKAR. Enquire for current availability.',
             (f' data-listing data-kind="category" data-category="{c["slug"]}" data-term="{e(c["term"])}"', main),
             active='Cruises' if c['slug'] == 'cruises' else 'Activities', scripts=('site', 'catalog', 'tours'))

    # destinations
    for l in LOCATIONS:
        uae = l['group'] == 'uae'
        img = l.get('img') or '/assets/img/hero-dubai-mobile.webp'
        if l['id'] == 'abu-dhabi':
            img = '/assets/img/hero-abu-dhabi.webp'
        if l['id'] == 'dubai':
            img = '/assets/img/hero-dubai.webp'
        main = f'''<section class="page-hero"><div class="container wide page-hero-grid">
  <div><nav class="breadcrumb" aria-label="Breadcrumb"><a href="/attractions">Destinations</a> / {e(l["name"])}</nav>
  <span class="kicker">{"United Arab Emirates" if uae else "Worldwide experiences"}</span>
  <h1>Things to do in {e(l["name"])}</h1>
  <p>Explore experiences in {e(l["name"])}, compare options and send your request on WhatsApp for your preferred travel date.</p>
  <p style="margin-top:16px"><a class="link" href="#results" data-hero-count>Browse experiences ↓</a></p>{search_form(f"Search {l['name']} experiences")}</div>
  <div class="photo {"tone-city" if uae else "tone-sky"}" data-hero-img style="background-size:cover;background-position:center">{f'<img src="{e(img)}" alt="Explore {e(l["name"])}" fetchpriority="high">' if (uae or l.get("img")) else ''}</div>
</div></section>
<div class="container wide themes is-hidden" data-themes></div>
{results_block(location=l["id"], dest_select=False)}
<section class="section alt is-hidden" data-other-places><div class="container wide"><div class="section-head"><h2>Explore more destinations</h2></div><div class="related-links"></div></div></section>'''
        page(f'/destinations/{l["id"]}', f'Things to Do in {l["name"]}', f'Explore {l["name"]} attractions and experiences with KWIKAR.',
             (f' data-listing data-kind="destination" data-location="{l["id"]}"', main), active='Destinations', scripts=('site', 'catalog', 'tours'))


def build_attractions():
    uae_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in UAE)
    intl_opts = ''.join(f'<option value="{l["id"]}">{e(l["name"])}</option>' for l in LOCATIONS if l['group'] != 'uae')
    tiles = ''.join(f'''<a class="tile tone-city" href="/destinations/{l["id"]}" data-place>{f'<img src="{e(l["img"])}" alt="" loading="lazy">' if l.get("img") else ''}
      <span><strong>{e(l["name"])}</strong><small data-count="{l["id"]}">Explore attractions ↗</small></span></a>''' for l in UAE)
    world = ''.join(f'<a href="/destinations/{l["id"]}" data-place><strong>{e(l["name"])}</strong><small data-count="{l["id"]}">Explore ↗</small></a>' for l in LOCATIONS if l['group'] != 'uae')
    main = f'''<section class="banner-hero" style="background-image:url('/assets/img/hero-dubai.webp')"><div class="container wide">
  <span class="kicker">KWIKAR destinations</span><h1>Where would you like to explore?</h1>
  <p>Browse by city, then choose an experience or ask our team to plan your day.</p>
  <form class="discover-form" action="/search" role="search">
    <label>Destination<select name="destination"><option value="">All destinations</option><optgroup label="United Arab Emirates">{uae_opts}</optgroup><optgroup label="Worldwide">{intl_opts}</optgroup></select></label>
    <label>What would you like to do?<input type="search" name="q" placeholder="Tour, attraction or activity" autocomplete="off"></label>
    <button type="submit">Find experiences →</button>
  </form>
</div></section>
<section class="section"><div class="container wide">
  <div class="section-head"><div><span class="kicker">Explore the Emirates</span><h2>United Arab Emirates</h2></div><a class="view-all" href="/activities">Browse by activity <svg viewBox="0 0 24 24">{ICON["out"]}</svg></a></div>
  <div class="tile-grid">{tiles}</div>
</div></section>
<section class="section alt"><div class="container wide">
  <div class="section-head"><div><span class="kicker">Travel further</span><h2>Worldwide destinations</h2></div></div>
  <p class="section-intro">Explore international experiences from our current catalogue.</p>
  <div class="world-grid">{world}</div>
</div></section>'''
    page('/attractions', 'Destinations', 'Browse KWIKAR experiences by UAE city and worldwide destination.', (' data-hub', main),
         active='Destinations', scripts=('site', 'catalog', 'tours'))


def build_tour():
    main = '''<div class="container wide tour-page" aria-busy="true">
  <div class="skeleton"><div class="line short"></div><div class="line" style="height:30px;width:70%"></div><div class="line short"></div>
  <div class="media" style="margin-top:20px;aspect-ratio:21/8;border-radius:14px"></div><div class="line"></div><div class="line"></div><div class="line short"></div></div>
</div>
<noscript><div class="status-page"><h1>Please enable JavaScript</h1><p>Or message us on WhatsApp and we will share the tour details.</p></div></noscript>'''
    page('/tour', 'Experience', 'Explore this experience with KWIKAR and book on WhatsApp.', (' data-tour', main), active='Activities',
         scripts=('site', 'catalog', 'tours'), body_class='tour-body')


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
        tag = f'<span class="badge">{e(v["tag"])}</span> ' if v.get('tag') else ''
        price = f'From {money(v["price"])} · final fee confirmed by our team' if v.get('price') else 'Fee on request'
        return f'''<article class="visa-card"><p class="eyebrow-blue">{tag}{e(v["stay"])} · Estimate {e(v["processing"])}</p><h3>{e(v["name"])}</h3>
          <p class="muted">{e(price)}</p><p class="actions" style="margin-top:14px"><a class="link" href="#visa-enquiry" data-pick="{e(v["name"])}" data-pick-target="v-type">Ask about this visa ↗</a></p></article>'''
    groups = ''.join(f'<h2 class="group-title">{g}</h2><div class="grid-4">{"".join(vcard(v) for v in VISAS if ("UAE" in v["name"]) == (g == "UAE visas"))}</div>' for g in ('UAE visas', 'Other destinations'))
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
    core = ['/', '/attractions', '/activities', '/holidays', '/transfers', '/visa', '/contact', '/about', '/privacy', '/terms', '/booking-information', '/refund-policy']
    urls = core + [f'/destinations/{l["id"]}' for l in LOCATIONS] + [f'/activities/{c["slug"]}' for c in CATEGORIES]
    today = datetime.date.today().isoformat()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
        f'  <url><loc>{SITE}{"" if u == "/" else u}{"/" if u == "/" else ""}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n'
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(xml)
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nDisallow: /search\n\nSitemap: {SITE}/sitemap.xml\nSitemap: {SITE}/api/sitemap-tours.php\n')


if __name__ == '__main__':
    write_catalog_js()
    build_home()
    build_listings()
    build_attractions()
    build_tour()
    build_holidays()
    build_transfers()
    build_visa()
    build_contact()
    build_info_pages()
    build_404()
    build_seo_files()
    n = sum(len([f for f in fs if f.endswith('.html')]) for _, _, fs in os.walk(OUT))
    print(f'Built {n} HTML pages into {OUT}')
