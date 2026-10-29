/* =========================================================
   KWIKAR — tours: live feed, listing pages, home, tour detail
   Tours, prices, ratings and tour photos come only from
   /api/tours.php (TravelDesk). If the feed cannot be loaded, an
   "unavailable" message with a WhatsApp link is shown instead.
   ========================================================= */
(function () {
  'use strict';
  var KW = window.KW, D = KW.data, esc = KW.esc;
  var FALLBACK_IMG = KW.u('/assets/img/hero-dubai-mobile.webp');
  var placeName = function (id) { var l = D.locations.filter(function (x) { return x.id === id; })[0]; return l ? l.name : 'More destinations'; };
  var place = function (id) { return D.locations.filter(function (x) { return x.id === id; })[0]; };

  /* ---------- feed ---------- */
  var feedPromise = null;
  KW.loadTours = function () {
    if (feedPromise) return feedPromise;
    try {
      var c = JSON.parse(sessionStorage.getItem('kw-tours') || 'null');
      if (c && Date.now() - c.at < 5 * 60 * 1000 && c.feed && c.feed.items) return (feedPromise = Promise.resolve(c.feed));
    } catch (e) { /* storage unavailable */ }
    var ctrl = 'AbortController' in window ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 15000);
    feedPromise = fetch(KW.u('/api/tours.php'), { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        clearTimeout(timer);
        if (d && d.ok && Array.isArray(d.items) && d.items.length) {
          var feed = { live: true, stale: !!d.stale, items: d.items.filter(function (t) { return t && t.name && t.loc; }) };
          try { sessionStorage.setItem('kw-tours', JSON.stringify({ at: Date.now(), feed: feed })); } catch (e) { /* ignore */ }
          return feed;
        }
        throw new Error('no feed');
      })
      .catch(function () {
        clearTimeout(timer);
        feedPromise = null; // allow a retry
        return { live: false, failed: true, stale: false, items: [] };
      });
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

  KW.reviewText = function (rating, count) {
    if (typeof rating !== 'number' || !isFinite(rating) || rating < 0 || rating > 5) return '';
    if (typeof count !== 'number' || count <= 0) return '';
    return '★ ' + rating.toFixed(1) + ' · ' + Math.round(count).toLocaleString('en-US') + (count === 1 ? ' review' : ' reviews');
  };

  KW.tourHref = function (t, live) {
    return live && t.id ? KW.u('/tour/' + t.id) : KW.whatsapp('Hi KWIKAR, I am interested in ' + t.name + '.');
  };

  KW.tourCard = function (t, live) {
    var href = KW.tourHref(t, live), ext = href.indexOf('https://wa.me') === 0 ? ' target="_blank" rel="noopener"' : '';
    var cat = t.cats && t.cats.length ? ' · ' + (t.cats.filter(function (c) { return /desert/i.test(t.name) && /desert/i.test(c); })[0] || t.cats[0]) : '';
    var review = KW.reviewText(t.rating, t.reviews);
    var price = live && t.price ? 'From <strong>' + KW.money(t.price) + '</strong>' + (t.unit ? ' / ' + esc(t.unit) : '') : 'Price on request';
    return '<article class="exp-card">' +
      '<a href="' + esc(href) + '"' + ext + ' class="media tall" aria-label="' + esc(t.name) + '"><img src="' + esc(t.img || FALLBACK_IMG) + '" alt="' + esc(t.name) + '" loading="lazy"></a>' +
      '<p class="tag">' + esc(placeName(t.loc)) + esc(cat) + '</p>' +
      '<h3><a href="' + esc(href) + '"' + ext + '>' + esc(t.name) + '</a></h3>' +
      (review ? '<p class="rating">' + esc(review) + '</p>' : '') +
      '<p class="price">' + price + '</p>' +
      '<a href="' + esc(href) + '"' + ext + ' class="link">' + (live && t.id ? 'View experience →' : 'Enquire on WhatsApp →') + '</a>' +
      '</article>';
  };

  KW.unavailable = function (mode) {
    var wa = esc(KW.whatsapp('Hi KWIKAR, which tours and prices are available for my dates?'));
    return '<div class="empty" style="grid-column:1/-1' + (mode === 'compact' ? ';width:100%' : '') + '"><p><strong>Tours could not be loaded right now.</strong></p>' +
      '<p style="margin-top:8px">Please try again in a moment, or ask our team on WhatsApp for current tours and prices.</p>' +
      '<p style="margin-top:14px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap"><button type="button" class="btn ghost" onclick="location.reload()">Try again</button>' +
      '<a class="btn wa" href="' + wa + '" target="_blank" rel="noopener">Ask on WhatsApp</a></p></div>';
  };

  function skeletons(n) {
    var s = '';
    for (var i = 0; i < n; i++) s += '<div class="exp-card skeleton"><div class="media tall"></div><div class="line short"></div><div class="line"></div><div class="line short"></div></div>';
    return s;
  }

  /* ---------- Home page ---------- */
  var best = document.querySelector('[data-home-best]');
  if (best) {
    KW.loadTours().then(function (feed) {
      if (!feed.live) {
        best.innerHTML = KW.unavailable('compact');
        KW.initCarousels();
        return;
      }
      var seen = {};
      var list = feed.items.filter(function (t) { return t.price && t.img && !/russian.speaking guide/i.test(t.name); })
        .sort(function (a, b) { return (b.reviews || 0) - (a.reviews || 0); })
        .filter(function (t) { if (seen[t.img]) return false; seen[t.img] = 1; return true; }).slice(0, 12);
      if (list.length) {
        best.innerHTML = list.map(function (t) { return KW.tourCard(t, true); }).join('');
        KW.watchImages(best);
      } else best.innerHTML = KW.unavailable('compact');
      document.querySelectorAll('[data-city]').forEach(function (el) {
        var has = feed.items.some(function (t) { return t.loc === el.dataset.city; });
        el.classList.toggle('is-hidden', !has);
      });
      KW.initCarousels();
    });
  }

  /* ---------- Destinations hub ---------- */
  var hub = document.querySelector('[data-hub]');
  if (hub) {
    KW.loadTours().then(function (feed) {
      if (!feed.live) return;
      hub.querySelectorAll('[data-count]').forEach(function (el) {
        var n = feed.items.filter(function (t) { return t.loc === el.dataset.count; }).length;
        var box = el.closest('[data-place]');
        if (box) box.classList.toggle('is-hidden', n === 0);
        el.textContent = n + (n === 1 ? ' experience' : ' experiences') + ' ↗';
      });
    });
  }

  /* ---------- Listing pages (activities, categories, destinations, search) ---------- */
  var main = document.querySelector('[data-listing]');
  if (main) listing(main);

  function listing(main) {
    var ds = main.dataset;
    var location = ds.location || '', slug = ds.category || '', term = ds.term || '', kind = ds.kind || 'standard';
    var isSearch = kind === 'search';
    var query = isSearch ? (KW.params.get('q') || '').slice(0, 100) : '';
    var selected = 'all';
    if (isSearch) {
      var dp = KW.params.get('destination');
      if (dp && place(dp)) selected = dp;
    }
    var sort = 'popular', visible = 12, feed = null;
    var grid = main.querySelector('[data-grid]'), countEl = main.querySelector('[data-count-title]'), noteEl = main.querySelector('[data-note]');
    var destSel = main.querySelector('[data-dest-select]'), sortSel = main.querySelector('[data-sort]');
    var moreBtn = main.querySelector('[data-more]'), searchForm = main.querySelector('[data-list-search]');
    grid.innerHTML = skeletons(6);

    if (isSearch) {
      var h = main.querySelector('h1');
      if (query) { h.textContent = 'Results for “' + query.slice(0, 70) + '”'; document.title = 'Results for ' + query.slice(0, 70) + ' | KWIKAR'; }
      else if (selected !== 'all') h.textContent = 'Things to do in ' + placeName(selected);
    }
    if (searchForm) {
      var input = searchForm.querySelector('input');
      input.value = query;
      searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        query = input.value.trim().slice(0, 100); visible = 12; render();
        document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
    sortSel.addEventListener('change', function () { sort = sortSel.value; render(); });
    if (destSel) destSel.addEventListener('change', function () { selected = destSel.value; visible = 12; render(); });
    moreBtn.addEventListener('click', function () { visible += 12; render(); });

    KW.loadTours().then(function (f) { feed = f; setup(); render(); });

    function base() {
      return feed.items.filter(function (t) { return (!location || t.loc === location) && KW.matchesCategory(t, slug, term); });
    }

    function setup() {
      var b = base();
      // destination select
      if (destSel) {
        var rel = D.locations.filter(function (l) { return (slug ? b : feed.items).some(function (t) { return t.loc === l.id; }); });
        if (rel.length > 1) {
          destSel.innerHTML = '<option value="all">All destinations</option>' + rel.map(function (l) { return '<option value="' + l.id + '">' + esc(l.name) + '</option>'; }).join('');
          destSel.value = rel.some(function (l) { return l.id === selected; }) ? selected : 'all';
          selected = destSel.value;
        } else destSel.closest('label').classList.add('is-hidden');
      }
      if (!feed.live) return; // keep static sidebar & hero when showing samples
      // sidebar: only categories / destinations that have tours
      var side = main.querySelector('[data-side-cats]');
      if (side) side.querySelectorAll('[data-cat]').forEach(function (a) {
        var c = D.categories.filter(function (x) { return x.slug === a.dataset.cat; })[0];
        var has = feed.items.some(function (t) { return (!location || t.loc === location) && KW.matchesCategory(t, c.slug, c.term); });
        a.classList.toggle('is-hidden', !has);
      });
      var sideDest = main.querySelector('[data-side-dests]');
      if (sideDest) sideDest.querySelectorAll('[data-dest]').forEach(function (a) {
        a.classList.toggle('is-hidden', !(slug ? b : feed.items).some(function (t) { return t.loc === a.dataset.dest; }));
      });
      // hero image from the first matching tour (category pages)
      var heroImg = main.querySelector('[data-hero-img]');
      var first = b.filter(function (t) { return t.img; })[0];
      if (heroImg && first) heroImg.style.backgroundImage = "url('" + first.img.replace(/'/g, '%27') + "')";
      // themes on destination pages
      var themes = main.querySelector('[data-themes]');
      if (themes) {
        var seen = {}, list = [];
        b.forEach(function (t) { (t.cats || []).forEach(function (c) { if (c && !seen[c]) { seen[c] = 1; list.push(c); } }); });
        list = list.slice(0, 5);
        if (list.length) {
          themes.innerHTML = '<span>Popular themes in ' + esc(placeName(location)) + '</span>' + list.map(function (c) {
            return '<a class="chip" href="' + esc(KW.u('/search?destination=' + encodeURIComponent(location) + '&q=' + encodeURIComponent(c))) + '">' + esc(c) + ' ↗</a>';
          }).join('');
          themes.classList.remove('is-hidden');
        }
      }
      // places row on category pages
      var places = main.querySelector('[data-places]');
      if (places) {
        var pl = D.locations.filter(function (l) { return b.some(function (t) { return t.loc === l.id; }); }).slice(0, 8);
        if (pl.length > 1) {
          places.querySelector('.place-row').innerHTML = pl.map(function (l) {
            var n = b.filter(function (t) { return t.loc === l.id; }).length;
            return '<button type="button" class="place-btn" data-place-id="' + l.id + '">' + (l.img ? '<img src="' + esc(l.img) + '" alt="" loading="lazy">' : '<div class="thumb tone-city"></div>') +
              '<span>' + esc(l.name) + '<small>' + n + ' experiences</small></span></button>';
          }).join('');
          places.classList.remove('is-hidden');
          places.querySelectorAll('[data-place-id]').forEach(function (btn) {
            btn.addEventListener('click', function () {
              selected = selected === btn.dataset.placeId ? 'all' : btn.dataset.placeId;
              if (destSel) destSel.value = selected;
              visible = 12; render();
              document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
          });
        }
      }
      // related destinations (destination pages) / categories (category pages)
      var other = main.querySelector('[data-other-places]');
      if (other) {
        var me = place(location);
        var op = D.locations.filter(function (l) { return l.id !== location && me && l.group === me.group && feed.items.some(function (t) { return t.loc === l.id; }); }).slice(0, 3);
        if (op.length) {
          other.querySelector('.related-links').innerHTML = op.map(function (l) { return '<a href="' + KW.u('/destinations/' + l.id) + '">' + esc(l.name) + ' <small>See experiences ↗</small></a>'; }).join('');
          other.classList.remove('is-hidden');
        } else other.classList.add('is-hidden');
      }
      var rel2 = main.querySelector('[data-related-cats]');
      if (rel2) rel2.querySelectorAll('[data-cat]').forEach(function (a) {
        var c = D.categories.filter(function (x) { return x.slug === a.dataset.cat; })[0];
        a.classList.toggle('is-hidden', !feed.items.some(function (t) { return KW.matchesCategory(t, c.slug, c.term); }));
      });
      var heroCount = main.querySelector('[data-hero-count]');
      if (heroCount) heroCount.textContent = 'Browse ' + b.length + ' experiences ↓';
    }

    function render() {
      if (feed.failed) {
        countEl.textContent = 'Tours unavailable';
        noteEl.textContent = 'Live tours and prices could not be loaded.';
        grid.innerHTML = KW.unavailable();
        moreBtn.classList.add('is-hidden');
        var sel = main.querySelector('.list-selects'); if (sel) sel.classList.add('is-hidden');
        return;
      }
      var b = base();
      var q = query.toLowerCase();
      var list = b.filter(function (t) {
        var text = (t.name + ' ' + (t.cats || []).join(' ') + ' ' + placeName(t.loc)).toLowerCase();
        return (selected === 'all' || t.loc === selected) && (!q || text.indexOf(q) !== -1);
      }).sort(function (a, c) {
        if (sort === 'low') return (a.price == null ? Infinity : a.price) - (c.price == null ? Infinity : c.price);
        if (sort === 'high') return (c.price == null ? -1 : c.price) - (a.price == null ? -1 : a.price);
        return (c.reviews || 0) - (a.reviews || 0);
      });
      main.querySelectorAll('[data-place-id]').forEach(function (btn) { btn.classList.toggle('selected', btn.dataset.placeId === selected); });
      var word = list.length === 1 ? (slug === 'yachts' ? 'yacht' : slug === 'cruises' ? 'cruise' : slug === 'events' ? 'event' : 'experience')
        : (slug === 'yachts' ? 'yachts' : slug === 'cruises' ? 'cruises' : slug === 'events' ? 'events' : 'experiences');
      countEl.textContent = list.length + ' ' + word;
      noteEl.textContent = feed.stale ? 'Last saved tours are shown. Prices and availability are confirmed on WhatsApp.' : 'Live supplier prices shown when available. Final price and availability are confirmed on WhatsApp.';
      if (list.length) {
        grid.innerHTML = list.slice(0, visible).map(function (t) { return KW.tourCard(t, feed.live); }).join('');
        KW.watchImages(grid);
      } else {
        grid.innerHTML = '<div class="empty" style="grid-column:1/-1"><p>' +
          (query || selected !== 'all' ? 'No experiences match your search.' : location ? 'No experiences are currently listed for this destination.' : 'No experiences are currently listed in this category.') +
          '</p><p style="margin-top:10px">' + (query || selected !== 'all' ? '<button type="button" data-clear>Clear search</button> · ' : '') +
          '<a href="' + KW.u('/activities') + '">Browse all experiences</a> or <a href="' + esc(KW.whatsapp('Hi KWIKAR, can you help me find an experience?')) + '" target="_blank" rel="noopener">ask our team on WhatsApp</a>.</p></div>';
        var clr = grid.querySelector('[data-clear]');
        if (clr) clr.addEventListener('click', function () {
          query = ''; selected = 'all'; if (destSel) destSel.value = 'all';
          if (searchForm) searchForm.querySelector('input').value = ''; render();
        });
      }
      moreBtn.classList.toggle('is-hidden', list.length <= visible);
    }
  }

  /* ---------- Tour detail ---------- */
  var tourMain = document.querySelector('[data-tour]');
  if (tourMain) tourPage(tourMain);

  function tourPage(root) {
    var m = location.pathname.match(/\/tour\/(\d{1,9})\/?$/);
    var id = m ? m[1] : (KW.params.get('id') || '');
    if (!/^[1-9]\d{0,8}$/.test(id)) { location.replace(KW.u('/activities')); return; }
    var canonical = document.querySelector('link[rel=canonical]');
    if (canonical) canonical.href = 'https://kwikar.com/tour/' + id;

    fetch(KW.u('/api/tours.php') + '?id=' + id, { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (t) { if (!t || !t.ok || !t.name) throw new Error('unavailable'); render(t); })
      .catch(function () {
        root.innerHTML = '<div class="status-page"><h1>Tour details unavailable</h1><p>We could not load this experience right now. Our team can share the details and current price on WhatsApp.</p>' +
          '<div class="btns"><a class="btn wa" target="_blank" rel="noopener" href="' + esc(KW.whatsapp('Hi KWIKAR, I need help with tour ' + id + '.')) + '">Ask on WhatsApp</a><a class="btn ghost" href="' + KW.u('/activities') + '">Browse experiences</a></div></div>';
        document.title = 'Experience | KWIKAR';
        var robots = document.createElement('meta'); robots.name = 'robots'; robots.content = 'noindex'; document.head.appendChild(robots);
      });

    function fromPrice(t) {
      var o = t.offers.filter(function (x) { return typeof x.price === 'number' && x.price > 0; }).sort(function (a, b) { return a.price - b.price; })[0];
      return o ? { amount: o.price, unit: o.unit === 'trip' ? 'per booking' : 'per person' } : null;
    }

    function render(t) {
      document.title = t.name + ' | KWIKAR';
      var plain = (t.description || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
      var md = document.querySelector('meta[name=description]');
      if (md) md.content = (plain || 'Explore this experience with KWIKAR and book on WhatsApp.').slice(0, 155);
      var ogT = document.querySelector('meta[property="og:title"]'); if (ogT) ogT.content = t.name;
      if (t.img) { var ogI = document.querySelector('meta[property="og:image"]'); if (ogI) ogI.content = t.img; }
      var fp = fromPrice(t);
      var photos = [t.img].concat(t.photos || []).filter(Boolean).slice(0, 4);
      var review = KW.reviewText(t.rating, t.reviews);
      var cancel = (t.cancellation || []).filter(Boolean);
      var hours = null;
      cancel.join(' ').replace(/(\d+)\s*(?:hours|hrs)/i, function (_, h) { hours = h; });
      var pickup = t.offers.some(function (o) { return o.pickupRequired; });
      var loc = place(t.location);
      var offersHtml = t.offers.map(function (o) {
        var bits = [];
        if (o.hours) bits.push(o.hours + (o.hours === 1 ? ' hour' : ' hours'));
        if (o.minPeople != null && o.maxPeople != null) bits.push(o.minPeople + '–' + o.maxPeople + ' guests');
        var tr = o.pickupRequired ? (o.transferKind === 'private' ? 'Private transfer' : 'Sharing transfer') + (o.transferPricingMode === 'per_booking' ? ' · priced once per booking' : ' · included in per-person price') : '';
        var price = o.price ? 'From ' + KW.money(o.price) + ' / ' + (o.unit || 'person') + (o.tripFee && o.adultBase ? ' + ' + KW.money(o.tripFee) + ' / booking' : '') : 'On request';
        return '<article class="offer"><div><h3>' + esc(o.name) + '</h3>' + (bits.length ? '<p>' + esc(bits.join(' · ')) + '</p>' : '') + (tr ? '<p>' + esc(tr) + '</p>' : '') +
          (o.desc ? '<details><summary>Details and inclusions</summary><div class="rich">' + o.desc + '</div></details>' : '') + '</div><strong>' + esc(price) + '</strong></article>';
      }).join('');

      root.innerHTML =
        '<div class="container wide tour-page">' +
        '<nav class="breadcrumb" aria-label="Breadcrumb"><a href="' + KW.u('/') + '">Home</a> / ' + (loc ? '<a href="' + KW.u('/destinations/' + loc.id) + '">' + esc(loc.name) + '</a> / ' : '<a href="' + KW.u('/activities') + '">Experiences</a> / ') + esc(t.name) + '</nav>' +
        '<h1>' + esc(t.name) + '</h1>' +
        '<p class="tour-meta">' + esc(loc ? loc.name : '') + (t.categories && t.categories.length ? ' · ' + esc(t.categories.join(' · ')) : '') + (review ? ' · <span class="rating">' + esc(review) + '</span>' : '') + '</p>' +
        (photos.length ? '<div class="gallery n' + photos.length + '">' + photos.map(function (src, i) { return '<img src="' + esc(src) + '" alt="' + esc(t.name) + ' photo ' + (i + 1) + '"' + (i ? ' loading="lazy"' : '') + '>'; }).join('') + '</div>' : '') +
        '<div class="badges">' + (hours ? '<span>Free cancellation up to ' + esc(hours) + ' hours before</span>' : '') + '<span>' + (pickup ? 'Transfer options available' : 'Meet at location') + '</span><span>Book on WhatsApp</span><span>No booking or card fees</span></div>' +
        '<div class="tour-grid"><div>' +
        (t.description ? '<section class="block"><h2>Overview</h2><div class="rich">' + t.description + '</div></section>' : '') +
        (t.offers.length ? '<section class="block"><h2>Available options</h2>' + offersHtml + '</section>' : '') +
        (t.itinerary && t.itinerary.length ? '<section class="block"><h2>Itinerary</h2>' + t.itinerary.map(function (s) { return '<div class="step"><strong>' + esc(s.name) + '</strong>' + (s.desc ? '<p>' + esc(s.desc) + '</p>' : '') + '</div>'; }).join('') + '</section>' : '') +
        (t.faq && t.faq.length ? '<section class="block"><h2>Questions</h2>' + t.faq.map(function (f) { return '<details class="faq"><summary>' + esc(f.q) + '</summary><p>' + esc(f.a) + '</p></details>'; }).join('') + '</section>' : '') +
        (cancel.length ? '<section class="block"><h2>Cancellation policy</h2>' + cancel.map(function (l) { return '<p>' + esc(l) + '</p>'; }).join('') + '</section>' : '') +
        (t.terms ? '<section class="block"><h2>Terms</h2><div class="rich">' + t.terms + '</div></section>' : '') +
        '</div><aside><div class="book-card"><span>From</span><strong>' + (fp ? KW.money(fp.amount) : 'Price on request') + '</strong><small>' + (fp ? fp.unit + ' · final price confirmed on WhatsApp' : 'Our team will confirm the price') + '</small>' +
        '<button class="btn block" type="button" data-book>Check availability</button>' +
        '<a class="call" href="tel:+' + KW.phone + '">Need help? Call +971 50 559 9243</a></div></aside></div></div>' +
        '<div class="sticky-book"><div><span>From</span><strong>' + (fp ? KW.money(fp.amount) : 'On request') + '</strong></div><button class="btn" type="button" data-book>Check availability</button></div>';
      KW.watchImages(root);
      root.querySelectorAll('[data-book]').forEach(function (b) { b.addEventListener('click', function () { openSheet(t); }); });

      var ld = { '@context': 'https://schema.org', '@type': 'Product', name: t.name, description: plain.slice(0, 300), image: photos };
      if (fp) ld.offers = { '@type': 'Offer', priceCurrency: 'AED', price: fp.amount, availability: 'https://schema.org/InStock', url: 'https://kwikar.com/tour/' + id };
      var s = document.createElement('script'); s.type = 'application/ld+json'; s.textContent = JSON.stringify(ld); document.head.appendChild(s);
    }

    /* ----- booking request sheet → WhatsApp ----- */
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
        optWrap.querySelectorAll('input').forEach(function (r) { r.addEventListener('change', renderTotal); });
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
          'Link: https://kwikar.com/tour/' + id
        ].filter(Boolean);
        KW.openWA(KW.whatsapp(lines.join('\n')));
      });
    }
  }
})();
