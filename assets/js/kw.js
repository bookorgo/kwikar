/* KWIKAR — site behaviour (menus, slider, listings, forms, booking sheet).
   Pages are complete HTML; this file only adds interaction.
   No online payment: every booking and enquiry opens WhatsApp. */
(function () {
  'use strict';
  var PHONE = '971505599243';
  var KW = window.KW = window.KW || {};
  var params = new URLSearchParams(location.search);
  KW.params = params;
  var esc = KW.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  };
  var money = KW.money = function (n) {
    n = Number(n);
    return 'AED ' + n.toLocaleString('en-US', { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2 });
  };
  KW.whatsapp = function (msg) { return 'https://wa.me/' + PHONE + '?text=' + encodeURIComponent(msg); };
  KW.openWA = function (msg) {
    var url = KW.whatsapp(msg);
    var w = window.open(url, '_blank', 'noopener');
    if (!w) location.href = url;
  };

  /* ---------- GA4 events (only sent when GA4 is installed) ---------- */
  KW.track = function (name, data) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, data || {}); } catch (e) { /* ignore */ }
  };
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var h = a.getAttribute('href');
    if (/^https:\/\/wa\.me\//.test(h)) KW.track('whatsapp_click', { link_url: h.split('?')[0], page_path: location.pathname });
    else if (/^tel:/.test(h)) KW.track('call_click', { page_path: location.pathname });
  });

  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- header: mega menus + mobile menu ---------- */
  var header = document.querySelector('.kw-header-vb');
  if (header) {
    var nav = header.querySelector('.kw-main-nav');
    var burger = header.querySelector('.kw-mobile-menu');
    var groups = header.querySelectorAll('.kw-nav-group');
    var panels = header.querySelectorAll('.kw-mega-menu');
    var initialActive = header.querySelector('.kw-nav-group.active');
    var mobileOpen = false, active = null;
    var setMenu = function (label) {
      active = label;
      panels.forEach(function (p) { p.hidden = p.dataset.menu !== label; });
      groups.forEach(function (g) {
        var on = label ? g.dataset.group === label : g === initialActive;
        g.classList.toggle('active', on);
        g.querySelector('.kw-nav-toggle').setAttribute('aria-expanded', String(label === g.dataset.group));
      });
    };
    var setMobile = function (open) {
      mobileOpen = open;
      nav.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      burger.querySelector('.kw-ico-open').hidden = open;
      burger.querySelector('.kw-ico-close').hidden = !open;
    };
    groups.forEach(function (g) {
      g.addEventListener('mouseenter', function () { if (!mobileOpen && window.matchMedia('(hover: hover)').matches) setMenu(g.dataset.group); });
      g.querySelector('.kw-nav-toggle').addEventListener('click', function () { setMenu(active === g.dataset.group ? null : g.dataset.group); });
    });
    header.addEventListener('mouseleave', function () { if (!mobileOpen) setMenu(null); });
    burger.addEventListener('click', function () { setMobile(!mobileOpen); setMenu(null); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setMenu(null); setMobile(false); } });
    document.addEventListener('pointerdown', function (e) { if (!header.contains(e.target)) setMenu(null); });
  }

  /* ---------- mobile "More" shortcuts ---------- */
  var more = document.querySelector('.kw-mobile-extra');
  if (more) {
    document.addEventListener('pointerdown', function (e) { if (!more.contains(e.target)) more.removeAttribute('open'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') more.removeAttribute('open'); });
  }

  /* ---------- carousels (section arrows) ---------- */
  document.querySelectorAll('[data-scroll]').forEach(function (b) {
    b.addEventListener('click', function () {
      var row = document.getElementById(b.dataset.scroll);
      if (row) row.scrollBy({ left: 310 * Number(b.dataset.dir), behavior: 'smooth' });
    });
  });

  /* ---------- home hero slider ---------- */
  var slider = document.querySelector('.kw-slider[data-slider]');
  if (slider) {
    var slides = JSON.parse(slider.dataset.slider), cur = 0, paused = false;
    var mainEl = slider.querySelector('.kw-slider-main');
    var left = slider.querySelector('.kw-peek-left'), right = slider.querySelector('.kw-peek-right');
    var dots = slider.querySelectorAll('[data-slide]');
    slides.forEach(function (s) { var i = new Image(); i.src = s.image; });
    var peek = function (el, s) {
      el.style.backgroundImage = "url('" + s.image + "')";
      el.setAttribute('aria-label', 'View ' + s.title);
      el.querySelector('.kw-peek-eyebrow').textContent = s.eyebrow;
      el.querySelector('strong').textContent = s.title;
      el.querySelector('small').textContent = s.description;
    };
    var show = function (n) {
      cur = (n + slides.length) % slides.length;
      var s = slides[cur];
      mainEl.style.backgroundImage = "url('" + s.image + "')";
      mainEl.classList.toggle('first-slide', cur === 0);
      mainEl.querySelector('.kw-slide-eyebrow').textContent = s.eyebrow;
      mainEl.querySelector('h2').textContent = s.title;
      mainEl.querySelector('.kw-slider-copy p').textContent = s.description;
      mainEl.querySelector('.kw-slider-copy a').setAttribute('href', s.href);
      peek(left, slides[(cur + slides.length - 1) % slides.length]);
      peek(right, slides[(cur + 1) % slides.length]);
      dots.forEach(function (d, i) { d.classList.toggle('selected', i === cur); });
    };
    left.addEventListener('click', function () { show(cur - 1); });
    right.addEventListener('click', function () { show(cur + 1); });
    dots.forEach(function (d) { d.addEventListener('click', function () { show(Number(d.dataset.slide)); }); });
    slider.addEventListener('mouseenter', function () { paused = true; });
    slider.addEventListener('mouseleave', function () { paused = false; });
    slider.addEventListener('focusin', function () { paused = true; });
    slider.addEventListener('focusout', function (e) { if (!slider.contains(e.relatedTarget)) paused = false; });
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setInterval(function () { if (!paused && !document.hidden) show(cur + 1); }, 5500);
    }
  }

  /* ---------- listings: activities, categories, destinations, search ---------- */
  var listing = document.querySelector('[data-listing]');
  if (listing) setupListing(listing);

  function setupListing(main) {
    var ds = main.dataset, kind = ds.kind, slug = ds.category || '', term = ds.term || '', fixedLoc = ds.location || '';
    var grid = main.querySelector('[data-grid]'), countEl = main.querySelector('[data-count-title]');
    var sortSel = main.querySelector('[data-sort]'), destSel = main.querySelector('[data-dest-select]'), moreBtn = main.querySelector('[data-more]');
    var forms = main.querySelectorAll('[data-list-search]');
    var PAGE = 24, visible = PAGE, sort = 'popular', selected = 'all', query = '', data = null, lastCount = 0;
    if (kind === 'search') { query = (params.get('q') || '').slice(0, 100); selected = params.get('destination') || 'all'; }
    forms.forEach(function (f) { f.querySelector('input').value = query; });

    // Show the first page straight away using the cards already in the HTML
    var cards = grid.querySelectorAll('.kw-list-card');
    if (cards.length > PAGE && kind !== 'search') {
      cards.forEach(function (c, i) { if (i >= PAGE) c.hidden = true; });
      moreBtn.hidden = false;
    }
    moreBtn.addEventListener('click', function () {
      visible += PAGE;
      if (data) render(); else grid.querySelectorAll('.kw-list-card').forEach(function (c, i) { c.hidden = i >= visible; });
      if (!data) moreBtn.hidden = grid.querySelectorAll('.kw-list-card').length <= visible;
    });

    fetch('/assets/data/tours.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      data = d;
      if (kind === 'search') {
        if (destSel && selected !== 'all') destSel.value = selected;
        var h = main.querySelector('h1');
        if (query) h.textContent = 'Results for “' + query.slice(0, 70) + '”';
        else if (selected !== 'all') h.textContent = 'Things to do in ' + locName(selected);
        if (query || selected !== 'all') document.title = h.textContent + ' | KWIKAR';
      }
      render();
      if (kind === 'search' && query) KW.track('site_search', { search_term: query, results: lastCount });
    }).catch(function () { /* keep the HTML cards */ });

    forms.forEach(function (f) {
      f.addEventListener('submit', function (e) {
        e.preventDefault();
        query = f.querySelector('input').value.trim().slice(0, 100);
        forms.forEach(function (o) { o.querySelector('input').value = query; });
        visible = PAGE;
        if (data) render();
        if (query) KW.track('site_search', { search_term: query, results: lastCount, page_path: location.pathname });
        document.getElementById('kw-page-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    var filterEvent = function (type, value) { KW.track('filter_apply', { filter_type: type, filter_value: value, page_path: location.pathname }); };
    if (sortSel) sortSel.addEventListener('change', function () { sort = sortSel.value; if (data) render(); filterEvent('sort', sort); });
    if (destSel) destSel.addEventListener('change', function () { selected = destSel.value; visible = PAGE; if (data) render(); filterEvent('destination', selected); });
    main.querySelectorAll('[data-place-id]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        selected = selected === btn.dataset.placeId ? 'all' : btn.dataset.placeId;
        filterEvent('destination', selected);
        if (destSel) destSel.value = selected;
        visible = PAGE;
        if (data) render();
        document.getElementById('kw-page-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    function locName(id) {
      if (id === 'other') return 'More';
      var l = (data && data.locations || []).filter(function (x) { return x.id === id; })[0];
      return l ? l.name : 'More';
    }
    function matches(t) {
      var name = t.name.toLowerCase(), tags = (t.cats || []).join(' ').toLowerCase();
      if (/russian.speaking guide/i.test(t.name)) return false;
      if (!slug) return true;
      if (slug === 'yachts') return /yacht/.test(name) || /yacht/.test(tags);
      if (slug === 'cruises') return !/yacht/.test(name) && /cruise|dhow/.test(name);
      if (slug === 'events') return /event|concert|festival|performance|live show/.test(name) || (t.cats || []).some(function (c) { return /^events?$/i.test(c.trim()); });
      return term.toLowerCase().split('|').some(function (w) { return (name + ' ' + tags).indexOf(w) !== -1; });
    }
    function card(t) {
      var cats = t.cats || [], cat = '';
      if (cats.length) cat = ' · ' + (cats.filter(function (c) { return /desert/i.test(t.name) && /desert/i.test(c); })[0] || cats[0]);
      var price = t.price ? 'From <strong>' + money(t.price) + '</strong> ' + (t.unit ? '/ ' + esc(t.unit) : '') : 'Price on request';
      return '<article class="kw-list-card"><a href="' + esc(t.url) + '"><img src="' + esc(t.img || '/assets/img/hero-dubai.webp') + '" loading="lazy" alt="' + esc(t.name) + '"></a><div><span>' +
        esc(locName(t.loc) + cat) + '</span><h3><a href="' + esc(t.url) + '">' + esc(t.name) + '</a></h3><p>' + price + '</p><a class="kw-card-view" href="' + esc(t.url) + '">View experience →</a></div></article>';
    }
    function render() {
      var q = query.toLowerCase();
      var list = data.items.filter(function (t) {
        if (fixedLoc && t.loc !== fixedLoc) return false;
        if (!matches(t)) return false;
        if (selected !== 'all' && t.loc !== selected) return false;
        if (q && (t.name + ' ' + (t.cats || []).join(' ') + ' ' + locName(t.loc)).toLowerCase().indexOf(q) === -1) return false;
        return true;
      });
      if (sort === 'low') list.sort(function (a, b) { return (a.price == null ? Infinity : a.price) - (b.price == null ? Infinity : b.price); });
      if (sort === 'high') list.sort(function (a, b) { return (b.price == null ? -1 : b.price) - (a.price == null ? -1 : a.price); });
      main.querySelectorAll('[data-place-id]').forEach(function (b) { b.classList.toggle('selected', b.dataset.placeId === selected); });
      var sing = { yachts: 'yacht', cruises: 'cruise', events: 'event' }[slug] || 'experience';
      var plur = { yachts: 'yachts', cruises: 'cruises', events: 'events' }[slug] || 'experiences';
      lastCount = list.length;
      countEl.textContent = list.length + ' ' + (list.length === 1 ? sing : plur);
      if (list.length) grid.innerHTML = list.slice(0, visible).map(card).join('');
      else {
        grid.innerHTML = '<div class="kw-market-empty"><p>No experiences match your search.</p> <button type="button" data-clear>Clear search</button> · <a href="/activities">Browse all experiences</a> or <a href="' +
          esc(KW.whatsapp('Hi KWIKAR, can you help me find an experience?')) + '" target="_blank" rel="noopener noreferrer">ask our team on WhatsApp</a>.</div>';
        grid.querySelector('[data-clear]').addEventListener('click', function () {
          query = ''; selected = 'all'; if (destSel) destSel.value = 'all';
          forms.forEach(function (f) { f.querySelector('input').value = ''; });
          render();
        });
      }
      moreBtn.hidden = list.length <= visible;
    }
  }

  /* ---------- prefill selects from the address (?service=, ?type=, ?country=) ---------- */
  document.querySelectorAll('[data-prefill]').forEach(function (sel) {
    var v = params.get(sel.dataset.prefill);
    if (v && Array.prototype.some.call(sel.options, function (o) { return o.value === v || o.text === v; })) sel.value = v;
  });

  /* ---------- holidays: country filter ---------- */
  var hol = document.querySelector('[data-holidays]');
  if (hol) {
    var country = 'All';
    var applyCountry = function (c) {
      country = c;
      hol.querySelectorAll('.kw-filter-row [data-country]').forEach(function (b) { b.classList.toggle('selected', b.dataset.country === c); });
      hol.querySelectorAll('.kw-holiday-destinations [data-country]').forEach(function (b) { b.classList.toggle('selected', b.dataset.country === c); });
      hol.querySelectorAll('[data-group]').forEach(function (g) { g.hidden = c !== 'All' && g.dataset.group !== c; });
    };
    hol.querySelectorAll('.kw-filter-row [data-country]').forEach(function (b) { b.addEventListener('click', function () { applyCountry(b.dataset.country); }); });
    hol.querySelectorAll('.kw-holiday-destinations [data-country]').forEach(function (b) {
      b.addEventListener('click', function () { applyCountry(country === b.dataset.country ? 'All' : b.dataset.country); });
    });
    var pc = params.get('country');
    if (pc && hol.querySelector('.kw-filter-row [data-country="' + CSS.escape(pc) + '"]')) applyCountry(pc);
  }

  /* ---------- transfers: fleet filter, estimator, vehicle picks ---------- */
  var fleet = document.querySelector('[data-fleet]');
  if (fleet) {
    var applyType = function (t) {
      fleet.querySelectorAll('[data-type]').forEach(function (b) { b.classList.toggle('selected', b.dataset.type === t); });
      fleet.querySelectorAll('[data-car-type]').forEach(function (c) { c.hidden = t !== 'All' && c.dataset.carType !== t; });
    };
    fleet.querySelectorAll('[data-type]').forEach(function (b) { b.addEventListener('click', function () { applyType(b.dataset.type); }); });
    var pt = params.get('type');
    if (pt && fleet.querySelector('[data-type="' + CSS.escape(pt) + '"]')) applyType(pt);
  }
  var setFormValue = function (form, name, value) {
    var el = form && form.elements[name];
    if (!el || value == null) return;
    if (el.tagName === 'SELECT') { if (Array.prototype.some.call(el.options, function (o) { return o.text === value; })) el.value = value; }
    else el.value = value;
  };
  document.querySelectorAll('[data-pick]').forEach(function (a) {
    a.addEventListener('click', function () {
      var form = document.querySelector('.kw-form[data-wa]');
      setFormValue(form, form && form.elements.vehicle ? 'vehicle' : 'type', a.dataset.pick);
    });
  });
  var est = document.querySelector('[data-estimator]');
  if (est) {
    var E = JSON.parse(est.dataset.estimator), service = 'airport';
    var routeSel = est.querySelector('[name=route]'), hoursIn = est.querySelector('[name=hours]'), vehSel = est.querySelector('[name=vehicle]');
    var routes = function () { return service === 'airport' ? E.airport : E.intercity; };
    var update = function () {
      var r = routes()[Math.min(Number(routeSel.value) || 0, routes().length - 1)], v = vehSel.value;
      var hours = Math.min(12, Math.max(3, Number(hoursIn.value) || 3));
      var base = service === 'hourly' ? E.hourly[v] * hours : r.rates[v];
      est.querySelector('[data-out]').textContent = base != null ? money(base) : 'Request a quote';
      est.querySelector('[data-sel]').textContent = service === 'hourly' ? hours + ' hours · ' + v : r.name + ' · ' + v;
      est.querySelector('[data-route-field]').hidden = service === 'hourly';
      est.querySelector('[data-hours-field]').hidden = service !== 'hourly';
    };
    est.querySelectorAll('[data-service]').forEach(function (b) {
      b.addEventListener('click', function () {
        service = b.dataset.service;
        est.querySelectorAll('[data-service]').forEach(function (x) { x.classList.toggle('selected', x === b); x.setAttribute('aria-pressed', String(x === b)); });
        routeSel.innerHTML = routes().map(function (r, i) { return '<option value="' + i + '">' + esc(r.name) + '</option>'; }).join('');
        update();
      });
    });
    [routeSel, vehSel].forEach(function (el) { el.addEventListener('change', update); });
    hoursIn.addEventListener('input', update);
    hoursIn.addEventListener('change', function () { hoursIn.value = Math.min(12, Math.max(3, Number(hoursIn.value) || 3)); update(); });
    est.querySelector('[data-request]').addEventListener('click', function () {
      var form = document.querySelector('.kw-form[data-wa]'), r = routes()[Number(routeSel.value) || 0];
      setFormValue(form, 'vehicle', vehSel.value);
      setFormValue(form, 'service', service === 'hourly' ? 'Hourly chauffeur' : service === 'airport' ? 'Airport transfer' : 'Point to point');
      if (service !== 'hourly') { setFormValue(form, 'pickup', r.from); setFormValue(form, 'dropoff', r.to); }
    });
    update();
  }

  /* ---------- enquiry forms → WhatsApp ---------- */
  document.querySelectorAll('form[data-wa]').forEach(function (form) {
    var build = function () {
      var lines = [form.dataset.wa];
      form.querySelectorAll('[data-label]').forEach(function (el) { if (el.value.trim()) lines.push(el.dataset.label + ': ' + el.value.trim()); });
      return lines.join('\n');
    };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      KW.track('generate_lead', { form_name: form.dataset.wa, method: 'whatsapp' });
      KW.openWA(build());
    });
    var mail = form.querySelector('[data-mail]');
    if (mail) mail.addEventListener('click', function (e) {
      e.preventDefault();
      location.href = 'mailto:info@kwikar.com?subject=' + encodeURIComponent(form.dataset.wa) + '&body=' + encodeURIComponent(build());
    });
  });

  /* ---------- tour page: booking sheet → WhatsApp ---------- */
  var tourEl = document.getElementById('kw-tour');
  if (tourEl) {
    var tour = null;
    try { tour = JSON.parse(tourEl.textContent); } catch (e) { /* ignore */ }
    if (tour) KW.track('product_view', { item_id: String(tour.id), item_name: tour.name, page_path: location.pathname });
    if (tour) document.querySelectorAll('[data-book]').forEach(function (b) {
      b.addEventListener('click', function () {
        KW.track('check_availability_click', { item_id: String(tour.id), item_name: tour.name });
        openSheet(tour);
      });
    });
  }

  function openSheet(t) {
    var DAY = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    var draftKey = 'kwikar-booking-draft:' + t.id;
    var s = { stage: 'date', date: '', adults: 2, children: 0, infants: 0, ages: [], offer: -1, month: null,
              d: { name: '', countryCode: '+971', mobile: '', email: '', residence: '', pickupMode: 'address', hotel: '', room: '', special: '' } };
    try { var saved = JSON.parse(localStorage.getItem(draftKey) || 'null'); if (saved) { ['date', 'adults', 'children', 'infants', 'ages', 'offer'].forEach(function (k) { if (saved[k] != null) s[k] = saved[k]; }); if (saved.d) Object.assign(s.d, saved.d); } } catch (e) { /* ignore */ }
    var save = function () { try { localStorage.setItem(draftKey, JSON.stringify({ date: s.date, adults: s.adults, children: s.children, infants: s.infants, ages: s.ages, offer: s.offer, d: s.d })); } catch (e) { /* ignore */ } };
    var iso = function (d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
    var fromIso = function (v) { var p = v.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2]); };
    var fmt = function (v, long) { return new Intl.DateTimeFormat('en-AE', long ? { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' } : { day: 'numeric', month: 'short' }).format(fromIso(v)); };
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var offers = t.offers || [];
    var days = (offers.filter(function (o) { return o.daysOffered && o.daysOffered.length; })[0] || {}).daysOffered || [];
    var allDays = {};
    offers.forEach(function (o) { (o.daysOffered && o.daysOffered.length ? o.daysOffered : DAY).forEach(function (d) { allDays[String(d).toLowerCase()] = 1; }); });
    var dateAllowed = function (d) { return d >= today && (!days.length || allDays[DAY[d.getDay()]]); };
    var periodFor = function (o, date) {
      if (!o.pricingPeriods || !o.pricingPeriods.length) return { adult: o.adultBase || 0, child: o.child || 0, trip: o.tripFee || 0 };
      return o.pricingPeriods.filter(function (p) { return p.dateStart <= date && date <= p.dateEnd; })[0] || null;
    };
    var issue = function (o) {
      var party = s.adults + s.children + s.infants;
      if (o.daysOffered && o.daysOffered.length && s.date && o.daysOffered.map(function (x) { return String(x).toLowerCase(); }).indexOf(DAY[fromIso(s.date).getDay()]) === -1) return 'Not offered on this day of the week.';
      var p = periodFor(o, s.date);
      if (!p) return 'This option has no price for the selected date.';
      if (o.minPeople != null && party < o.minPeople) return 'Minimum ' + o.minPeople + ' guests required.';
      if (o.maxPeople != null && party > o.maxPeople) return 'Maximum ' + o.maxPeople + ' guests allowed.';
      if (s.children > 0 && o.childrenAllowed === false) return 'Children are not allowed for this option.';
      var tripOnly = !p.adult && !p.child && p.trip > 0;
      if (!tripOnly && !(p.adult > 0)) return 'Adult price on request for this option.';
      if (!tripOnly && s.children > 0 && !(p.child > 0)) return 'Child price on request for this option.';
      return null;
    };
    var total = function (o) {
      if (!o || issue(o)) return null;
      var p = periodFor(o, s.date);
      return Math.round(((p.adult || 0) * s.adults + (p.child || 0) * s.children + (p.trip || 0)) * 100) / 100;
    };
    var selected = function () { return offers[s.offer] || null; };
    var titles = { date: 'When are you going?', guests: "Who's going?", options: 'Choose an option', details: 'Your details', review: 'Review your request' };
    var back = { date: null, guests: 'date', options: 'guests', details: 'options', review: 'details' };

    var wrap = document.createElement('div');
    wrap.className = 'kw-sheet-backdrop';
    wrap.innerHTML = '<section tabindex="-1" class="kw-booking-sheet" role="dialog" aria-modal="true" aria-labelledby="booking-title"><header><button type="button" data-back aria-label="Go back">‹</button><div><span>KWIKAR booking request</span><h2 id="booking-title"></h2></div><button type="button" data-close aria-label="Close">×</button></header><div data-body></div></section>';
    document.body.appendChild(wrap);
    var sheet = wrap.querySelector('.kw-booking-sheet'), body = wrap.querySelector('[data-body]');
    var prevOverflow = document.body.style.overflow, lastFocus = document.activeElement;
    document.body.style.overflow = 'hidden';
    var close = function () { wrap.remove(); document.body.style.overflow = prevOverflow; document.removeEventListener('keydown', onKey); if (lastFocus) lastFocus.focus(); };
    var onKey = function (e) { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });
    wrap.querySelector('[data-close]').addEventListener('click', close);
    wrap.querySelector('[data-back]').addEventListener('click', function () { if (back[s.stage]) go(back[s.stage]); else close(); });

    function go(stage) { s.stage = stage; save(); render(); sheet.scrollTop = 0; sheet.focus(); }
    function guestSummary() {
      return s.adults + ' adult' + (s.adults !== 1 ? 's' : '') + (s.children ? ', ' + s.children + ' child' + (s.children !== 1 ? 'ren' : '') : '') + (s.infants ? ', ' + s.infants + ' infant' + (s.infants !== 1 ? 's' : '') : '');
    }
    function render() {
      wrap.querySelector('#booking-title').textContent = titles[s.stage];
      sheet.classList.toggle('kw-booking-sheet-wide', s.stage === 'options');
      ({ date: renderDate, guests: renderGuests, options: renderOptions, details: renderDetails, review: renderReview })[s.stage]();
    }

    function renderDate() {
      if (s.date && !dateAllowed(fromIso(s.date))) s.date = '';
      var base = s.month || (s.date ? fromIso(s.date) : new Date(today));
      var m = new Date(base.getFullYear(), base.getMonth(), 1);
      s.month = m;
      var first = (m.getDay() + 6) % 7, dim = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
      var cells = '', i;
      for (i = 0; i < first; i++) cells += '<td></td>';
      for (i = 1; i <= dim; i++) {
        var d = new Date(m.getFullYear(), m.getMonth(), i), v = iso(d), ok = dateAllowed(d);
        cells += '<td><button type="button" data-day="' + v + '"' + (ok ? '' : ' disabled') + ' class="' + (v === s.date ? 'selected ' : '') + (d.getTime() === today.getTime() ? 'today' : '') + '" aria-label="' + esc(fmt(v, true)) + '">' + i + '</button></td>';
        if ((first + i) % 7 === 0) cells += '</tr><tr>';
      }
      var canPrev = m > new Date(today.getFullYear(), today.getMonth(), 1);
      body.innerHTML = '<div class="kw-sheet-content kw-calendar-step"><div class="kw-cal"><div class="kw-cal-head"><button type="button" data-m="-1" aria-label="Previous month"' + (canPrev ? '' : ' disabled') + '>‹</button><strong>' +
        new Intl.DateTimeFormat('en-AE', { month: 'long', year: 'numeric' }).format(m) + '</strong><button type="button" data-m="1" aria-label="Next month">›</button></div><table><thead><tr>' +
        ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].map(function (x) { return '<th scope="col">' + x + '</th>'; }).join('') + '</tr></thead><tbody><tr>' + cells + '</tr></tbody></table></div>' +
        '<p>' + (days.length ? 'Dates the supplier does not operate are disabled.' : 'Choose your preferred future date. Your request is subject to availability and staff confirmation.') + '</p>' +
        '<button class="kw-button" type="button" data-next' + (s.date ? '' : ' disabled') + '>Continue' + (s.date ? ' · ' + esc(fmt(s.date)) : '') + '</button></div>';
      body.querySelectorAll('[data-m]').forEach(function (b) { b.addEventListener('click', function () { s.month = new Date(m.getFullYear(), m.getMonth() + Number(b.dataset.m), 1); renderDate(); }); });
      body.querySelectorAll('[data-day]').forEach(function (b) { b.addEventListener('click', function () { s.date = b.dataset.day; save(); renderDate(); }); });
      body.querySelector('[data-next]').addEventListener('click', function () { if (s.date) go('guests'); });
    }

    function renderGuests() {
      var maxP = Math.max.apply(null, offers.map(function (o) { return o.maxPeople || 0; }).concat([20]));
      var row = function (key, label, hint, min) {
        var max = Math.max(min, maxP - (s.adults + s.children + s.infants - s[key]));
        return '<div class="kw-guest-row"><div><strong>' + label + '</strong><small>' + hint + '</small></div><div class="kw-stepper"><button type="button" data-dec="' + key + '"' + (s[key] <= min ? ' disabled' : '') +
          ' aria-label="Remove ' + label + '">−</button><output>' + s[key] + '</output><button type="button" data-inc="' + key + '"' + (s[key] >= max ? ' disabled' : '') + ' aria-label="Add ' + label + '">+</button></div></div>';
      };
      while (s.ages.length < s.children) s.ages.push(-1);
      s.ages.length = s.children;
      var ages = s.children ? '<div class="kw-child-age-list">' + s.ages.map(function (a, i) {
        var opts = '<option value="">Select age</option>';
        for (var y = 0; y <= 17; y++) opts += '<option value="' + y + '"' + (a === y ? ' selected' : '') + '>' + y + ' years</option>';
        return '<label>Age of child ' + (i + 1) + '<select required data-age="' + i + '">' + opts + '</select></label>';
      }).join('') + '</div>' : '';
      var ready = s.ages.every(function (a) { return a >= 0; });
      body.innerHTML = '<div class="kw-sheet-content">' + row('adults', 'Adults', 'Lead traveller must be an adult', 1) + row('children', 'Children', 'Supplier age eligibility will be confirmed', 0) + ages +
        row('infants', 'Infants', 'Age and price eligibility confirmed by our team', 0) + '<p class="kw-guest-note">Option limits are checked by our team before you pay. Child ages are required.</p>' +
        '<button class="kw-button" type="button" data-next' + (ready ? '' : ' disabled') + '>See options</button></div>';
      body.querySelectorAll('[data-inc]').forEach(function (b) { b.addEventListener('click', function () { s[b.dataset.inc]++; save(); renderGuests(); }); });
      body.querySelectorAll('[data-dec]').forEach(function (b) { b.addEventListener('click', function () { s[b.dataset.dec]--; save(); renderGuests(); }); });
      body.querySelectorAll('[data-age]').forEach(function (sel) { sel.addEventListener('change', function () { s.ages[Number(sel.dataset.age)] = sel.value === '' ? -1 : Number(sel.value); save(); renderGuests(); }); });
      body.querySelector('[data-next]').addEventListener('click', function () {
        if (!s.ages.every(function (a) { return a >= 0; })) return;
        if (selected() && issue(selected())) s.offer = -1;
        if (offers.length === 1 && !issue(offers[0])) s.offer = 0;
        go('options');
      });
    }

    function renderOptions() {
      var transfer = function (o) { return o.transferKind === 'private' ? 'Private transfer' : o.transferKind === 'sharing' ? 'Sharing transfer' : 'Meet at location'; };
      var list = offers.map(function (o, i) {
        var bad = issue(o), tot = total(o);
        return '<label class="kw-option-card ' + (s.offer === i ? 'selected ' : '') + (bad ? 'disabled' : '') + '"><input type="radio" name="offer" value="' + i + '"' + (bad ? ' disabled' : '') + (s.offer === i ? ' checked' : '') +
          '><div><strong>' + esc(o.name) + '</strong><span>' + (o.hours ? esc(o.hours) + ' hours · ' : '') + transfer(o) + '</span>' +
          (o.pickupRequired ? '<small>' + (o.transferPricingMode === 'per_booking' ? money(o.tripFee || 0) + ' per car, added once' : 'Transfer included in per-person price') + '</small>' : '') +
          (bad ? '<small>' + esc(bad) + '</small>' : '') + '</div><b>' + (tot != null ? money(tot) : 'Unavailable for this selection') + '</b></label>';
      }).join('');
      var o = selected(), tot = total(o);
      body.innerHTML = '<div class="kw-sheet-content kw-options-step"><div class="kw-selected-summary"><span>' + esc(fmt(s.date, true)) + ' · ' + guestSummary() +
        '</span><div><button type="button" data-goto="date">Edit date</button><button type="button" data-goto="guests">Edit guests</button></div></div><div class="kw-option-list">' +
        (list || '<p class="kw-guest-note">Options for this experience are confirmed by our team. Continue to send your request.</p>') +
        '</div><div class="kw-option-total"><div><span>Estimated total</span><strong>' + (tot != null ? money(tot) : (offers.length ? 'Select an option' : 'On request')) + '</strong><small>No booking or card fees</small></div>' +
        '<button class="kw-button" type="button" data-next' + ((o && tot != null) || !offers.length ? '' : ' disabled') + '>Continue to details</button></div></div>';
      body.querySelectorAll('[data-goto]').forEach(function (b) { b.addEventListener('click', function () { go(b.dataset.goto); }); });
      body.querySelectorAll('input[name=offer]').forEach(function (r) {
        r.addEventListener('change', function () {
          s.offer = Number(r.value); save(); renderOptions();
          KW.track('option_select', { item_id: String(t.id), item_name: t.name, option: offers[s.offer].name });
        });
      });
      body.querySelector('[data-next]').addEventListener('click', function () { go('details'); });
    }

    function renderDetails() {
      var o = selected(), d = s.d;
      var pickup = o && o.pickupRequired;
      body.innerHTML = '<form class="kw-sheet-content kw-checkout-form" novalidate>' +
        '<div class="kw-two-fields"><label>Full name<input name="name" required minlength="2" autocomplete="name" value="' + esc(d.name) + '"></label><label>Email (optional)<input name="email" type="email" autocomplete="email" value="' + esc(d.email) + '"></label></div>' +
        '<div class="kw-two-fields kw-phone-fields"><label>Country code<input name="countryCode" required autocomplete="tel-country-code" value="' + esc(d.countryCode) + '" inputmode="tel"></label><label>Mobile / WhatsApp number<input name="mobile" required type="tel" inputmode="tel" autocomplete="tel-national" pattern="[0-9 ()-]{6,24}" maxlength="24" value="' + esc(d.mobile) + '"></label></div>' +
        '<label>Country of residence<input name="residence" autocomplete="country-name" value="' + esc(d.residence) + '"></label>' +
        (pickup ? '<fieldset class="kw-pickup-fields"><legend>Pickup details</legend><label class="kw-check-row"><input type="radio" name="pickupMode" value="address"' + (d.pickupMode !== 'later' ? ' checked' : '') + '><span>Share hotel or address now</span></label>' +
          '<div class="kw-two-fields" data-addr' + (d.pickupMode === 'later' ? ' hidden' : '') + '><label>Hotel or pickup address<input name="hotel" value="' + esc(d.hotel) + '"></label><label>Room number (optional)<input name="room" value="' + esc(d.room) + '"></label></div>' +
          '<label class="kw-check-row"><input type="radio" name="pickupMode" value="later"' + (d.pickupMode === 'later' ? ' checked' : '') + '><span>I will share pickup details later</span></label></fieldset>' : '') +
        '<label>Special requests (optional)<textarea name="special" rows="3" maxlength="500" placeholder="Accessibility, dietary or other useful details">' + esc(d.special) + '</textarea></label>' +
        '<p class="kw-draft-note">Saved on this device so you can return after refreshing.</p><p class="kw-sheet-error" data-err hidden></p><button class="kw-button" type="submit">Review request</button></form>';
      var form = body.querySelector('form');
      form.addEventListener('input', function (e) {
        var el = e.target; if (el.name && el.name in d) d[el.name] = el.value;
        if (el.name === 'pickupMode') form.querySelector('[data-addr]').hidden = el.value === 'later';
        save();
      });
      form.addEventListener('change', function (e) { if (e.target.name === 'pickupMode') { d.pickupMode = e.target.value; form.querySelector('[data-addr]').hidden = d.pickupMode === 'later'; save(); } });
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var err = form.querySelector('[data-err]'), msg = '';
        if (d.name.trim().length < 2) msg = 'Please enter your full name.';
        else if (!/^\+?\d{1,4}$/.test(d.countryCode.trim()) || !/^[0-9 ()-]{6,24}$/.test(d.mobile.trim())) msg = 'Please enter a valid mobile number.';
        else if (d.email.trim() && !/^\S+@\S+\.\S+$/.test(d.email.trim())) msg = 'Please check your email address.';
        else if (pickup && d.pickupMode !== 'later' && d.hotel.trim().length < 3) msg = 'Please add your hotel or pickup address, or choose to share it later.';
        err.textContent = msg; err.hidden = !msg;
        if (!msg) go('review');
      });
    }

    function message() {
      var o = selected(), d = s.d, tot = total(o);
      var lines = ['Hi KWIKAR, I would like to book:', '', t.name];
      if (o) lines.push('Option: ' + o.name);
      lines.push('Date: ' + fmt(s.date, true), 'Guests: ' + guestSummary() + (s.children ? ' (child ages: ' + s.ages.join(', ') + ')' : ''));
      if (tot != null) lines.push('Estimated total: ' + money(tot));
      if (o && o.pickupRequired) lines.push('Pickup: ' + (d.pickupMode === 'later' ? 'I will share later' : d.hotel + (d.room ? ', room ' + d.room : '')));
      lines.push('', 'Name: ' + d.name.trim(), 'Mobile: ' + d.countryCode.trim() + ' ' + d.mobile.trim());
      if (d.email.trim()) lines.push('Email: ' + d.email.trim());
      if (d.residence.trim()) lines.push('Country of residence: ' + d.residence.trim());
      if (d.special.trim()) lines.push('Requests: ' + d.special.trim());
      lines.push('', 'Link: ' + t.url, '', 'Please confirm availability and the final price.');
      return lines.join('\n');
    }

    function renderReview() {
      var o = selected(), d = s.d, tot = total(o);
      var row = function (k, v) { return '<div><dt>' + k + '</dt><dd>' + v + '</dd></div>'; };
      var pol = (t.cancellation || []).length ? '<details class="kw-review-policy"><summary>Cancellation policy</summary>' + t.cancellation.map(function (l) { return '<p>' + esc(l) + '</p>'; }).join('') + '</details>' : '';
      body.innerHTML = '<div class="kw-sheet-content kw-review-step"><div class="kw-review-card"><h3>' + esc(t.name) + '</h3><dl>' + row('Date', esc(fmt(s.date, true))) +
        (o ? row('Option', esc(o.name)) : '') + row('Guests', esc(guestSummary()) + (s.children ? ' (ages ' + esc(s.ages.join(', ')) + ')' : '')) +
        (o && o.pickupRequired ? row('Pickup', d.pickupMode === 'later' ? 'Share later' : esc(d.hotel + (d.room ? ' · Room ' + d.room : ''))) : '') +
        row('Contact', esc(d.name) + '<br>' + esc(d.countryCode + ' ' + d.mobile) + (d.email ? '<br>' + esc(d.email) : '')) + '</dl></div>' +
        '<div class="kw-review-total"><span>Estimated total in AED</span><strong>' + (tot != null ? money(tot) : 'On request') + '</strong><small>Final price confirmed by our team on WhatsApp. No booking or card fees.</small></div>' + pol +
        '<p class="kw-guest-note">WhatsApp opens with your request so you can review and send it. Nothing is booked or paid until our team confirms availability and the final price.</p>' +
        '<button class="kw-button kw-wa-send" type="button" data-send>Send request on WhatsApp ↗</button><button class="kw-link-button" type="button" data-goto="details">Edit traveller details</button></div>';
      body.querySelector('[data-goto]').addEventListener('click', function () { go('details'); });
      body.querySelector('[data-send]').addEventListener('click', function () {
        KW.track('begin_checkout', { currency: 'AED', value: tot || 0, items: [{ item_id: String(t.id), item_name: t.name, item_variant: o ? o.name : '' }] });
        KW.track('generate_lead', { form_name: 'Tour booking', method: 'whatsapp', currency: 'AED', value: tot || 0 });
        KW.openWA(message());
      });
    }

    render();
    sheet.focus();
  }
})();
