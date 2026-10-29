/* =========================================================
   KWIKAR — tours in the browser
   Tour cards and tour pages are already in the HTML (written by build.py
   from the tours API). This file adds filtering, sorting, search and the
   booking-request sheet. The tour list comes from /assets/data/tours.json,
   generated in the same build, so links and prices match the HTML.
   ========================================================= */
(function () {
  'use strict';
  var KW = window.KW, D = KW.data, esc = KW.esc;
  var FALLBACK_IMG = KW.u('/assets/img/hero-dubai-mobile.webp');
  var cityOf = function (loc) { return !loc || loc === 'other' ? 'uae' : loc; };
  var placeName = function (id) {
    if (!id || id === 'other' || id === 'uae') return 'UAE';
    var l = D.locations.filter(function (x) { return x.id === id; })[0];
    return l ? l.name : 'UAE';
  };

  /* ---------- tours list (same snapshot as the HTML) ---------- */
  var feedPromise = null;
  KW.loadTours = function () {
    if (feedPromise) return feedPromise;
    feedPromise = fetch(KW.u('/assets/data/tours.json'), { headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error('tours'); return r.json(); })
      .then(function (d) { return { ok: true, items: (d.items || []).filter(function (t) { return t && t.name && t.loc; }) }; })
      .catch(function () { feedPromise = null; return { ok: false, items: [] }; });
    return feedPromise;
  };

  KW.matchesCategory = function (t, slug, term) {
    if (/russian.speaking guide/i.test(t.name)) return false;
    var name = t.name.toLowerCase(), tags = (t.cats || []).join(' ').toLowerCase();
    if (slug === 'yachts') return /yacht/.test(name) || /yacht/.test(tags);
    if (slug === 'cruises') return !/yacht/.test(name) && /cruise|dhow/.test(name);
    if (slug === 'events') return /event|concert|festival|performance|live show/.test(name) || (t.cats || []).some(function (c) { return /^events?$/i.test(c.trim()); });
    return !term || term.toLowerCase().split('|').some(function (w) { return (name + ' ' + tags).indexOf(w) !== -1; });
  };

  KW.money = KW.money || function (n) { return 'AED ' + Number(n).toLocaleString('en-AE', { maximumFractionDigits: 2 }); };

  /* Same markup as tf.card() in build.py (no supplier ratings) */
  KW.tourCard = function (t, short) {
    var href = KW.u(t.url || ('/tour/' + t.id));
    var cat = '';
    if (!short && t.cats && t.cats.length) {
      cat = ' · ' + (t.cats.filter(function (c) { return /desert/i.test(t.name) && /desert/i.test(c); })[0] || t.cats[0]);
    }
    var price = t.price ? 'From <strong>' + KW.money(t.price) + '</strong>' + (t.unit ? ' / ' + esc(t.unit) : '') : 'Price on request';
    return '<article class="exp-card"><a href="' + esc(href) + '" class="media tall" aria-label="' + esc(t.name) + '">' +
      '<img src="' + esc(t.img || FALLBACK_IMG) + '" alt="' + esc(t.name) + '" loading="lazy" width="400" height="453"></a>' +
      '<p class="tag">' + esc(placeName(t.loc)) + esc(cat) + '</p><h3><a href="' + esc(href) + '">' + esc(t.name) + '</a></h3>' +
      '<p class="price">' + price + '</p><a href="' + esc(href) + '" class="link">View experience →</a></article>';
  };

  /* ---------- listing pages: /activities, categories, /activities/{city}, search ---------- */
  var main = document.querySelector('[data-listing]');
  if (main) listing(main);

  function listing(main) {
    var ds = main.dataset;
    var slug = ds.category || '', term = ds.term || '', kind = ds.kind || 'standard', fixedCity = ds.city || '';
    var isSearch = kind === 'search';
    var query = isSearch ? (KW.params.get('q') || '').slice(0, 100) : '';
    var selected = 'all';
    var dp = KW.params.get('destination');
    if (dp) selected = cityOf(dp);
    var sort = 'popular', visible = 12, items = null;
    var grid = main.querySelector('[data-grid]'), countEl = main.querySelector('[data-count-title]');
    var destSel = main.querySelector('[data-dest-select]'), sortSel = main.querySelector('[data-sort]');
    var moreBtn = main.querySelector('[data-more]'), searchForm = main.querySelector('[data-list-search]');
    var input = searchForm ? searchForm.querySelector('input') : null;

    if (isSearch && (query || selected !== 'all')) {
      var h = main.querySelector('h1');
      h.textContent = query ? 'Results for “' + query.slice(0, 70) + '”' : 'Things to do in ' + placeName(selected);
      document.title = h.textContent + ' | KWIKAR';
    }
    if (input) input.value = query;

    KW.loadTours().then(function (f) {
      if (!f.ok) return; // keep the cards that are already in the page
      items = f.items;
      setup();
      if (query || selected !== 'all' || grid.children.length > visible) render();
    });

    if (searchForm) searchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      query = input.value.trim().slice(0, 100); visible = 12;
      if (items) render();
      document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    sortSel.addEventListener('change', function () { sort = sortSel.value; if (items) render(); });
    if (destSel) destSel.addEventListener('change', function () { selected = destSel.value; visible = 12; if (items) render(); });
    moreBtn.addEventListener('click', function () { visible += 12; if (items) render(); });
    main.querySelectorAll('[data-place-id]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        selected = selected === btn.dataset.placeId ? 'all' : btn.dataset.placeId;
        if (destSel) destSel.value = selected;
        visible = 12; if (items) render();
        document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    function base() {
      return items.filter(function (t) { return (!fixedCity || cityOf(t.loc) === fixedCity) && KW.matchesCategory(t, slug, term); });
    }

    function setup() {
      if (!destSel) return;
      var b = base(), cities = [];
      b.forEach(function (t) { var c = cityOf(t.loc); if (cities.indexOf(c) === -1) cities.push(c); });
      if (cities.length > 1) {
        destSel.innerHTML = '<option value="all">All destinations</option>' + cities.map(function (c) {
          return '<option value="' + c + '">' + esc(c === 'uae' ? 'More UAE' : placeName(c)) + '</option>';
        }).join('');
        destSel.value = cities.indexOf(selected) !== -1 ? selected : 'all';
        selected = destSel.value;
      } else destSel.closest('label').classList.add('is-hidden');
    }

    function render() {
      var q = query.toLowerCase();
      var list = base().filter(function (t) {
        var text = (t.name + ' ' + (t.cats || []).join(' ') + ' ' + placeName(t.loc)).toLowerCase();
        return (selected === 'all' || cityOf(t.loc) === selected) && (!q || text.indexOf(q) !== -1);
      });
      if (sort === 'low') list.sort(function (a, c) { return (a.price == null ? Infinity : a.price) - (c.price == null ? Infinity : c.price); });
      else if (sort === 'high') list.sort(function (a, c) { return (c.price == null ? -1 : c.price) - (a.price == null ? -1 : a.price); });
      main.querySelectorAll('[data-place-id]').forEach(function (btn) { btn.classList.toggle('selected', btn.dataset.placeId === selected); });
      var word = list.length === 1 ? (slug === 'yachts' ? 'yacht' : slug === 'cruises' ? 'cruise' : slug === 'events' ? 'event' : 'experience')
        : (slug === 'yachts' ? 'yachts' : slug === 'cruises' ? 'cruises' : slug === 'events' ? 'events' : 'experiences');
      countEl.textContent = list.length + ' ' + word;
      if (list.length) {
        grid.innerHTML = list.slice(0, visible).map(function (t) { return KW.tourCard(t); }).join('');
        KW.watchImages(grid);
      } else {
        grid.innerHTML = '<div class="empty" style="grid-column:1/-1"><p>No experiences match your search.</p><p style="margin-top:10px">' +
          '<button type="button" data-clear>Clear search</button> · <a href="' + KW.u('/activities') + '">Browse all experiences</a> or ' +
          '<a href="' + esc(KW.whatsapp('Hi KWIKAR, can you help me find an experience?')) + '" target="_blank" rel="noopener">ask our team on WhatsApp</a>.</p></div>';
        grid.querySelector('[data-clear]').addEventListener('click', function () {
          query = ''; selected = 'all'; if (destSel) destSel.value = 'all';
          if (input) input.value = ''; render();
        });
      }
      moreBtn.classList.toggle('is-hidden', list.length <= visible);
    }
  }

  /* ---------- tour page: the page is in the HTML; add the booking sheet ---------- */
  var tourData = document.getElementById('kw-tour');
  if (tourData) {
    var tour = null;
    try { tour = JSON.parse(tourData.textContent); } catch (e) { tour = null; }
    if (tour) {
      document.querySelectorAll('[data-book]').forEach(function (b) {
        b.addEventListener('click', function () {
          KW.track('check_availability_click', { item_name: tour.name, item_id: String(tour.id) });
          openSheet(tour);
        });
      });
    }
  }

  function openSheet(t) {
    var today = new Date(); today.setDate(today.getDate() + 1);
    var minDate = today.toISOString().slice(0, 10);
    var st = { adults: 2, children: 0 };
    var wrap = document.createElement('div');
    wrap.className = 'sheet-backdrop';
    wrap.innerHTML = '<section class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-title">' +
      '<header><div><small>Booking request</small><h2 id="sheet-title">' + esc(t.name) + '</h2></div><button type="button" class="sheet-close" aria-label="Close">×</button></header>' +
      '<form novalidate>' +
      '<fieldset><legend>1. Date</legend><label class="field">Preferred date<input type="date" name="date" min="' + minDate + '" required></label><div class="warn is-hidden" data-daywarn></div></fieldset>' +
      '<fieldset><legend>2. Guests</legend>' + stepper('adults', 'Adults', 'Age 12+ (supplier age rules apply)', 1) + stepper('children', 'Children', 'Ages confirmed by our team', 0) +
      '<label class="field is-hidden" data-ages style="margin-top:10px">Children\'s ages<input name="ages" placeholder="e.g. 5, 9"></label></fieldset>' +
      '<fieldset><legend>3. Option</legend><div data-options></div></fieldset>' +
      '<div class="total-bar"><div><small>Estimated total</small><strong data-total>Select an option</strong></div><small style="max-width:170px;text-align:right">Final price confirmed on WhatsApp. No booking or card fees.</small></div>' +
      '<fieldset><legend>4. Your details</legend><div style="display:grid;gap:12px">' +
      '<label class="field">Full name<input name="name" autocomplete="name" required></label>' +
      '<label class="field">Mobile / WhatsApp number<input name="phone" type="tel" autocomplete="tel" placeholder="+971 …" required></label>' +
      '<label class="field">Hotel or pickup address<input name="pickup" placeholder="Optional — can be shared later"></label>' +
      '<label class="field">Notes<textarea name="notes" placeholder="Anything we should know?"></textarea></label></div></fieldset>' +
      '<button class="btn wa block" type="submit">Send booking request on WhatsApp</button>' +
      '<p class="note">WhatsApp opens with your request so you can review and send it. Your booking is confirmed only after our team replies with availability and the final price.</p>' +
      '</form></section>';
    document.body.appendChild(wrap);
    document.body.style.overflow = 'hidden';
    var form = wrap.querySelector('form'), dateIn = form.elements.date, optWrap = wrap.querySelector('[data-options]'), totalEl = wrap.querySelector('[data-total]');
    var lastFocus = document.activeElement;
    setTimeout(function () { dateIn.focus(); }, 50);

    function stepper(key, label, hint, min) {
      return '<div class="stepper"><div><strong>' + label + '</strong><small>' + hint + '</small></div><div class="ctrl"><button type="button" data-dec="' + key + '" aria-label="Fewer ' + label.toLowerCase() + '">−</button><output data-val="' + key + '"></output><button type="button" data-inc="' + key + '" aria-label="More ' + label.toLowerCase() + '">+</button></div></div>';
    }
    function close() {
      wrap.remove(); document.body.style.overflow = '';
      if (lastFocus) lastFocus.focus();
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);
    wrap.querySelector('.sheet-close').addEventListener('click', close);
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });

    function availableOn(o, date) {
      if (!date || !o.pricingPeriods || !o.pricingPeriods.length) return true;
      return o.pricingPeriods.some(function (p) { return p.dateStart <= date && date <= p.dateEnd; });
    }
    function priceFor(o, date) {
      // use the pricing period for the chosen date when available
      var p = (o.pricingPeriods || []).filter(function (x) { return date && x.dateStart <= date && date <= x.dateEnd; })[0];
      var adult = p ? (p.adult || 0) : (o.adultBase || 0), child = p ? (p.child || 0) : (o.child || 0), trip = p ? (p.trip || 0) : (o.tripFee || 0);
      var tripOnly = adult === 0 && child === 0 && trip > 0;
      if (!tripOnly && adult <= 0) return null;
      if (!tripOnly && st.children > 0 && child <= 0) return null;
      return Math.round((adult * st.adults + child * st.children + trip) * 100) / 100;
    }
    function renderOptions() {
      var date = dateIn.value, cur = (form.querySelector('[name=offer]:checked') || {}).value;
      if (!t.offers.length) { optWrap.innerHTML = '<p class="muted">Our team will suggest the right option for you.</p>'; return; }
      optWrap.innerHTML = t.offers.map(function (o, i) {
        var ok = availableOn(o, date), total = ok ? priceFor(o, date) : null;
        var sub = [];
        if (o.hours) sub.push(o.hours + (o.hours === 1 ? ' hour' : ' hours'));
        if (o.transferKind === 'private') sub.push('Private transfer'); else if (o.transferKind === 'sharing') sub.push('Sharing transfer'); else if (o.transferKind === 'meet_at_location') sub.push('Meet at location');
        if (!ok) sub.push('Not priced for this date — ask us');
        return '<label class="option-card"><input type="radio" name="offer" value="' + i + '"' + ((cur === String(i)) || (!cur && i === 0) ? ' checked' : '') + '><div><strong>' + esc(o.name) + '</strong><small>' + esc(sub.join(' · ')) + '</small></div><b>' + (total != null ? KW.money(total) : 'On request') + '</b></label>';
      }).join('');
      optWrap.querySelectorAll('input').forEach(function (r) { r.addEventListener('change', function () { renderTotal(); var o = chosen(); if (o) KW.track('option_select', { item_name: t.name, option: o.name }); }); });
      renderTotal();
    }
    function chosen() { var r = form.querySelector('[name=offer]:checked'); return r ? t.offers[Number(r.value)] : null; }
    function renderTotal() {
      var o = chosen(), date = dateIn.value;
      var total = o && availableOn(o, date) ? priceFor(o, date) : null;
      totalEl.textContent = !o ? (t.offers.length ? 'Select an option' : 'On request') : total != null ? KW.money(total) : 'On request';
      // operating day warning
      var warn = wrap.querySelector('[data-daywarn]');
      var days = o && o.daysOffered && o.daysOffered.length ? o.daysOffered : null;
      if (days && date) {
        var name = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][new Date(date + 'T12:00:00').getDay()];
        var ok = days.indexOf(name) !== -1;
        warn.textContent = ok ? '' : 'This option usually runs on ' + days.map(function (d) { return d.slice(0, 3); }).join(', ') + '. You can still send the request and we will suggest alternatives.';
        warn.classList.toggle('is-hidden', ok);
      } else warn.classList.add('is-hidden');
    }
    function renderGuests() {
      ['adults', 'children'].forEach(function (k) { wrap.querySelector('[data-val=' + k + ']').textContent = st[k]; });
      wrap.querySelector('[data-dec=adults]').disabled = st.adults <= 1;
      wrap.querySelector('[data-dec=children]').disabled = st.children <= 0;
      wrap.querySelector('[data-inc=adults]').disabled = st.adults + st.children >= 30;
      wrap.querySelector('[data-inc=children]').disabled = st.adults + st.children >= 30;
      wrap.querySelector('[data-ages]').classList.toggle('is-hidden', st.children === 0);
      renderOptions();
    }
    wrap.querySelectorAll('[data-inc]').forEach(function (b) { b.addEventListener('click', function () { st[b.dataset.inc]++; renderGuests(); }); });
    wrap.querySelectorAll('[data-dec]').forEach(function (b) { b.addEventListener('click', function () { st[b.dataset.dec]--; renderGuests(); }); });
    dateIn.addEventListener('change', renderOptions);
    renderGuests();

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var missing = ['date', 'name', 'phone'].filter(function (k) { return !form.elements[k].value.trim(); });
      if (missing.length) { form.elements[missing[0]].focus(); form.elements[missing[0]].reportValidity && form.elements[missing[0]].reportValidity(); return; }
      var o = chosen(), date = dateIn.value, total = o && availableOn(o, date) ? priceFor(o, date) : null;
      var guests = st.adults + ' adult' + (st.adults !== 1 ? 's' : '') + (st.children ? ', ' + st.children + ' child' + (st.children !== 1 ? 'ren' : '') : '');
      var ages = form.elements.ages.value.trim();
      var lines = [
        'Booking request — KWIKAR',
        'Tour: ' + t.name,
        o ? 'Option: ' + o.name : null,
        'Date: ' + new Date(date + 'T12:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }),
        'Guests: ' + guests + (st.children && ages ? ' (children\'s ages: ' + ages + ')' : ''),
        'Estimated total: ' + (total != null ? KW.money(total) : 'please quote'),
        'Name: ' + form.elements.name.value.trim(),
        'Phone: ' + form.elements.phone.value.trim(),
        form.elements.pickup.value.trim() ? 'Hotel / pickup: ' + form.elements.pickup.value.trim() : null,
        form.elements.notes.value.trim() ? 'Notes: ' + form.elements.notes.value.trim() : null,
        'Link: ' + t.url
      ].filter(Boolean);
      KW.track('begin_checkout', { currency: 'AED', value: total || 0, item_name: t.name, item_id: String(t.id) });
      KW.openWA(KW.whatsapp(lines.join('\n')));
    });
  }

})();
