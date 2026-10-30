# KWIKAR hourly SEO run — runbook

Every scheduled run follows this file. Owner: Irfan Kabir (kwikar.com). Booking is on WhatsApp only;
there is no online payment, no admin panel and no affiliate links.

## Each run: do exactly ONE task, finish it, ship it

1. **Set up**
   - Clone `bookorgo/kwikar` (attach it with the add_repo tool, access "push", if it is not in the session).
   - `pip install --break-system-packages pillow` only if a task needs images.
   - Get the latest tours feed: `gh run download -R bookorgo/kwikar -n tours-feed -D /tmp/feed`
     (artifact of the newest successful "Refresh tours" run). Build with
     `cd source && python3 build.py --feed /tmp/feed/tours-feed.json && python3 qa.py`.
2. **Pick the task**: the first unchecked item in `source/seo/BACKLOG.md` that is not marked
   `(needs Irfan)`. If the backlog has fewer than 5 open items, first add new ones (see "Self-improvement").
3. **Do it** following the rules below. Keep it small enough to finish in this run.
4. **Check**: `python3 build.py --feed /tmp/feed/tours-feed.json && python3 qa.py` must print `QA OK`.
   Look at changed pages with Playwright screenshots (desktop 1300px and mobile 390px) when the
   change is visible; the design must match the existing kw-* sections (seo_head, facts, info_cards,
   faq_cards). Fix anything that looks off.
5. **Ship**: tick the item in BACKLOG.md, add one line to `source/seo/LOG.md`
   (`- YYYY-MM-DD HH:MM UTC — what changed — files`), commit (message ends with the attribution lines
   from the session), `git pull --rebase`, push to `main`, then trigger the rebuild so live prices are
   fresh: `gh api -X POST repos/bookorgo/kwikar/actions/workflows/rebuild.yml/dispatches -f ref=main`.
6. If nothing could be finished, do not push half-done work; write the blocker in LOG.md and BACKLOG.md.

## Hard rules

- **Prices and tour data only from the TravelDesk API.** In hand-written text use `{from}` (tour pages)
  or `{price:ID}` / `{link:ID}` (guides). Never type a tour price.
- **Facts must be checked**: open the source page (WebFetch) for every opening time, rule, date or
  requirement, add it to `sources` and `last_checked`. If sources disagree, leave the fact out.
- Original text only. No copied paragraphs, no "best price"/"cheapest"/"guaranteed" claims, no fake
  reviews or ratings, no aggregateRating, no doorway pages, no keyword stuffing. British English.
- Wording must fit the WhatsApp flow: "send your request", "our team confirms the final price before
  you pay". Never "checkout", "pay online", "instant confirmation".
- **Never without Irfan's approval** (write it in BACKLOG.md under "Needs approval" instead):
  changing robots.txt rules, canonical rules, existing URLs/slugs or redirect rules, deleting pages,
  changing the design system, changing contact details, adding tracking/ads, anything legal.
- Don't touch `public_html/api/`, the API key file or GitHub settings. Never commit secrets.
- One H1 per page, title ≤ 60 chars, meta description 120–160 chars, descriptive alt text.

## Where things live

- Tour page content: `source/data/tour-extras.json` (keys: slug, title, description, h1, subtitle,
  quick_answer, at_a_glance, glance_hide, badges, overview, best_for, choose, included, not_included,
  visitor_info, steps_title, steps, faqs, faqs_replace, faq_note, terms, related_heading,
  related_links, cta_heading, cta_text, alts, tip, last_checked, sources). Adding `slug` renames the URL
  and creates a 301 — only for tours that don't have a hand-written slug yet.
- Guides: `source/data/blog/*.json` (slug, city, title, description, h1, summary, published, updated,
  tour_id, glance, body HTML, faqs, related tour ids, sources).
- Hub intros: `source/data/hub-intros.json`. Site templates: `source/build.py`. Styles:
  `source/styles/additions.css`.

## Self-improvement (when the backlog runs low, and every Monday run)

- Read `source/seo/LOG.md` and open GitHub issues from the weekly SEO check; fix real problems first.
- Run PageSpeed (https://pagespeed.web.dev, mobile) on the homepage and one tour page; add concrete
  fixes to the backlog.
- Research 3–5 search topics travellers ask about Dubai/UAE experiences that Kwikar sells
  (WebSearch), check what the top results cover and what they miss, and add the best gaps as backlog
  items (one page or guide each, with the target query).
- Write what you learned (what kinds of pages/sections worked, mistakes to avoid) under
  "Learnings" in `source/seo/LEARNINGS.md`, so later runs improve. Keep it short and factual.
