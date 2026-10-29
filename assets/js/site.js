/* =========================================================
   KWIKAR — shared site behaviour (every page)
   Menu, dropdowns, hero slider, carousels, WhatsApp forms.
   ========================================================= */
(function () {
  'use strict';

  var KW = window.KW = window.KW || {};
  KW.phone = '971505599243';
  KW.whatsapp = function (message) {
    return 'https://wa.me/' + KW.phone + '?text=' + encodeURIComponent(message);
  };
  KW.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  KW.money = function (n) {
    return 'AED ' + Number(n).toLocaleString('en-AE', { maximumFractionDigits: 2 });
  };
  KW.params = new URLSearchParams(location.search);
  /* Internal link helper (a preview copy maps clean URLs to files) */
  KW.u = window.KW_LINK || function (path) { return path; };
  /* Open WhatsApp in a new tab; if pop-ups are blocked, go there directly */
  KW.openWA = function (url) {
    var w = null;
    try { w = window.open(url, '_blank'); } catch (err) { w = null; }
    if (w) { try { w.opener = null; } catch (err) { /* ignore */ } }
    else location.href = url;
  };

  /* ---------- Images that fail to load: show the gradient behind them ---------- */
  KW.watchImages = function (root) {
    (root || document).querySelectorAll('img').forEach(function (img) {
      if (img.dataset.watched) return;
      img.dataset.watched = '1';
      var hide = function () { img.classList.add('img-missing'); };
      if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) hide();
      img.addEventListener('error', hide);
    });
  };
  KW.watchImages();

  /* ---------- Mobile menu ---------- */
  var body = document.body;
  var toggle = document.querySelector('.menu-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = body.classList.toggle('menu-open');
      toggle.setAttribute('aria-expanded', open);
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
  }

  /* ---------- Dropdown (mega) menus ---------- */
  var items = document.querySelectorAll('.nav-item');
  function closeAll(except) {
    items.forEach(function (i) {
      if (i === except) return;
      i.classList.remove('open');
      var b = i.querySelector('.nav-toggle');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  items.forEach(function (item) {
    var btn = item.querySelector('.nav-toggle');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = !item.classList.contains('open');
      closeAll(item);
      item.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav-item')) closeAll();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeAll();
      body.classList.remove('menu-open');
    }
  });

  /* ---------- Home hero slider (left = previous, centre = active, right = next) ---------- */
  var hero = document.querySelector('[data-hero]');
  if (hero) {
    var slides = Array.prototype.slice.call(hero.querySelectorAll('.hero-slide'));
    var dotsWrap = hero.querySelector('.hero-dots');
    var n = slides.length, current = 1, timer = null;
    slides.forEach(function (_, i) {
      var d = document.createElement('button');
      d.type = 'button';
      d.setAttribute('aria-label', 'Show slide ' + (i + 1));
      d.addEventListener('click', function () { go(i); restart(); });
      dotsWrap.appendChild(d);
    });
    var dots = dotsWrap.querySelectorAll('button');
    function go(i) {
      current = (i + n) % n;
      slides.forEach(function (s, idx) {
        s.classList.remove('is-prev', 'is-active', 'is-next');
        var c = s.querySelector('.hero-content');
        c.style.animation = 'none'; void c.offsetWidth; c.style.animation = '';
        if (idx === current) s.classList.add('is-active');
        else if (idx === (current - 1 + n) % n) s.classList.add('is-prev');
        else s.classList.add('is-next');
        var heading = s.querySelector('.hero-title');
        s.querySelectorAll('a').forEach(function (a) { a.tabIndex = idx === current ? 0 : -1; });
        if (heading) heading.setAttribute('aria-hidden', idx === current ? 'false' : 'true');
      });
      dots.forEach(function (d, idx) { d.classList.toggle('on', idx === current); });
    }
    slides.forEach(function (s, idx) {
      s.addEventListener('click', function (e) {
        if (!s.classList.contains('is-active')) { e.preventDefault(); go(idx); restart(); }
      });
    });
    function restart() {
      clearInterval(timer);
      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        timer = setInterval(function () { if (!document.hidden) go(current + 1); }, 6000);
      }
    }
    hero.addEventListener('mouseenter', function () { clearInterval(timer); });
    hero.addEventListener('mouseleave', restart);
    var startX = null;
    hero.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    hero.addEventListener('touchend', function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) { go(current + (dx < 0 ? 1 : -1)); restart(); }
      startX = null;
    });
    go(current);
    restart();
  }

  /* ---------- Horizontal carousels (‹ › buttons) ---------- */
  KW.initCarousels = function () {
    document.querySelectorAll('[data-carousel]').forEach(function (sec) {
      var track = sec.querySelector('.track');
      var arrows = sec.querySelectorAll('.arrow');
      if (!track || !arrows.length) return;
      function update() {
        var max = track.scrollWidth - track.clientWidth - 2;
        arrows.forEach(function (a) {
          var dir = Number(a.dataset.dir);
          a.disabled = max <= 0 || (dir < 0 ? track.scrollLeft <= 2 : track.scrollLeft >= max);
        });
      }
      if (!sec.dataset.ready) {
        sec.dataset.ready = '1';
        arrows.forEach(function (a) {
          a.addEventListener('click', function () {
            var card = track.querySelector(':scope > :not(.is-hidden)');
            var step = card ? card.getBoundingClientRect().width + 16 : track.clientWidth;
            track.scrollBy({ left: step * Number(a.dataset.dir), behavior: 'smooth' });
          });
        });
        track.addEventListener('scroll', update, { passive: true });
        window.addEventListener('resize', update);
      }
      update();
    });
  };
  KW.initCarousels();

  /* ---------- Filter chips (holidays, transfers) ---------- */
  document.querySelectorAll('[data-filter-group]').forEach(function (group) {
    var name = group.dataset.filterGroup;
    var buttons = document.querySelectorAll('[data-filter="' + name + '"]');
    var targets = document.querySelectorAll('[data-' + name + ']');
    function apply(value) {
      buttons.forEach(function (b) {
        var on = b.dataset.value === value;
        b.classList.toggle('selected', on);
        b.setAttribute('aria-pressed', on);
      });
      targets.forEach(function (t) {
        t.classList.toggle('is-hidden', value !== 'All' && t.getAttribute('data-' + name) !== value);
      });
    }
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        var value = b.classList.contains('selected') && b.dataset.value !== 'All' ? 'All' : b.dataset.value;
        apply(value);
      });
    });
    var initial = KW.params.get(group.dataset.param || name);
    var valid = Array.prototype.some.call(buttons, function (b) { return b.dataset.value === initial; });
    apply(valid ? initial : 'All');
  });

  /* ---------- Prefill selects from links (?type=…, ?service=…) ---------- */
  document.querySelectorAll('[data-prefill]').forEach(function (el) {
    var v = KW.params.get(el.dataset.prefill);
    if (v && Array.prototype.some.call(el.options, function (o) { return o.value === v; })) el.value = v;
  });
  document.querySelectorAll('[data-pick]').forEach(function (a) {
    a.addEventListener('click', function () {
      var target = document.getElementById(a.dataset.pickTarget);
      if (target) target.value = a.dataset.pick;
    });
  });

  /* ---------- WhatsApp enquiry forms ---------- */
  document.querySelectorAll('form[data-wa]').forEach(function (form) {
    function message() {
      var lines = [form.dataset.wa];
      form.querySelectorAll('[data-label]').forEach(function (f) {
        var v = (f.value || '').trim();
        if (v) lines.push(f.dataset.label + ': ' + v);
      });
      return lines.join('\n');
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      KW.openWA(KW.whatsapp(message()));
    });
    var mail = form.querySelector('[data-mail]');
    if (mail) {
      mail.addEventListener('click', function (e) {
        e.preventDefault();
        location.href = 'mailto:info@kwikar.com?subject=' + encodeURIComponent(form.dataset.wa) + '&body=' + encodeURIComponent(message());
      });
    }
  });

  /* ---------- Transfer estimator ---------- */
  var est = document.querySelector('[data-estimator]');
  if (est) {
    var R = JSON.parse(est.dataset.estimator);
    var state = { service: 'airport', route: 0 };
    var tabs = est.querySelectorAll('[data-service]');
    var routeSel = est.querySelector('[name=route]'), hoursIn = est.querySelector('[name=hours]'), vehSel = est.querySelector('[name=vehicle]');
    var routeWrap = est.querySelector('.route-field'), hoursWrap = est.querySelector('.hours-field');
    var out = est.querySelector('[data-out]'), sel = est.querySelector('[data-sel]'), req = est.querySelector('[data-request]');
    function routes() { return state.service === 'airport' ? R.airport : R.intercity; }
    function fillRoutes() {
      routeSel.innerHTML = routes().map(function (r, i) { return '<option value="' + i + '">' + KW.esc(r.name) + '</option>'; }).join('');
    }
    function render() {
      tabs.forEach(function (t) { var on = t.dataset.service === state.service; t.classList.toggle('selected', on); t.setAttribute('aria-pressed', on); });
      routeWrap.hidden = state.service === 'hourly';
      hoursWrap.hidden = state.service !== 'hourly';
      var v = vehSel.value, price, label;
      if (state.service === 'hourly') {
        var h = Math.min(12, Math.max(3, Number(hoursIn.value) || 3));
        price = R.hourly[v] * h; label = h + ' hours · ' + v;
      } else {
        var r = routes()[Number(routeSel.value) || 0];
        price = r.rates[v]; label = r.name + ' · ' + v;
      }
      out.textContent = price != null ? KW.money(price) : 'Request a quote';
      sel.textContent = label;
    }
    tabs.forEach(function (t) { t.addEventListener('click', function () { state.service = t.dataset.service; fillRoutes(); render(); }); });
    [routeSel, hoursIn, vehSel].forEach(function (el) { el.addEventListener('input', render); el.addEventListener('change', render); });
    req.addEventListener('click', function () {
      var form = document.getElementById('transfer-form');
      if (!form) return;
      var service = form.querySelector('[name=service]'), car = form.querySelector('[name=vehicle]');
      var from = form.querySelector('[name=pickup]'), to = form.querySelector('[name=dropoff]');
      service.value = state.service === 'airport' ? 'Airport transfer' : state.service === 'hourly' ? 'Hourly chauffeur' : 'Point to point';
      if (Array.prototype.some.call(car.options, function (o) { return o.value === vehSel.value; })) car.value = vehSel.value;
      if (state.service !== 'hourly') {
        var r = routes()[Number(routeSel.value) || 0];
        from.value = r.from; to.value = r.to;
      }
    });
    fillRoutes();
    render();
  }

  /* ---------- Footer year ---------- */
  document.querySelectorAll('[data-year]').forEach(function (y) { y.textContent = new Date().getFullYear(); });
})();
