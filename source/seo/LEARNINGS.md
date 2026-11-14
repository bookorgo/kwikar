# SEO learnings

Short, factual notes that later runs should follow. Merged and shortened by the Strategist on 13 Nov 2026.

## Design and page structure
- SEO text must sit inside the site's own section design (eyebrow + heading + rule, fact rows, cards, FAQ cards). Plain long articles and duplicate tables looked "odd" to the owner (30 Oct 2026). Long hub text goes below the listings.
- Don't repeat a list on a page (options table + option cards; a glance list that repeats the body's age table). Give the glance different facts.
- `choose` must be a list of [label, text] pairs (string crashes the build). `choose` and `faqs` text is HTML-escaped on tour pages: put links only in overview, visitor_info, terms or related_links.
- Ordered lists in guide bodies render without numbers; use bold lead-ins. Keep long text out of the last column of tour-page option tables (it does not wrap).
- Screenshot via a local server (`python3 -m http.server` in public_html); file:// loses the CSS.
- Trustpilot: only the Review Collector widget (footer) until real reviews exist; no star widgets or aggregateRating without Irfan's approval (5 Nov).
- Fleet photos are real black photos from Wikimedia Commons (free licences, credits in source/data/fleet-credits.json, shown only on /photo-credits), natural backgrounds, plates hidden. Never use photos without a free licence, with watermarks or plates (6 Nov).

## Titles, metas, wording
- Count the title including " | KWIKAR" (9 chars); meta 120–160 counted on the rendered page, and read its end (fit() once cut "tolls and."). qa.py once passed a 171-char meta.
- Avoid "cheapest" even in comparisons ("costs the least"). Never promise instant tickets (build.py rewrites supplier "you will instantly receive tickets").
- Template words: "First Class class" → build.py cls_word(); fleet alts via car_alt() (no "with chauffeur" when none is in the photo).
- Don't answer "Is it open now?" with "Yes"; state dates. Don't state ticket validity unless the supplier notes say it.

## Supplier data traps
- Supplier data can be wrong (private car "1 hour", Aquarium "22 hours", Ski Dubai 1 h/4 h): hide auto rows with glance_hide/offer_hours. The auto "Runs on: Every day" row is wrong for attractions with a closing day (Louvre: Mondays).
- The listing `price` is the cheapest offer, which can be a fast-track add-on (Yas parks) or an adult escort rate (KidZania). build.py skips add-ons and supports `from_price: "child"` / `from_exclude`; check offers before writing {from}.
- Supplier FAQs (`details.<id>.faq`) often give exact child bands for our product (G-Class 4–11, under 4 free): use those. But FAQs can contradict the supplier's own terms (Dubai Frame 9am vs 8am, Lotus Royale 19:00 vs 6:45pm): use the time the terms and outside sources agree on.
- Supplier terms can list items the option doesn't include (Ski Dubai equipment): write `included` from the offer notes.
- Other sites may sell a same-named tour from another operator (G-Class: different dinner and child band) or other days (Platinumlist "daily"): cross-check only shared facts, keep product details and day rows from our own offers.
- Old hand-written glance rows can be wrong (Global Village hours): re-check when filling a page.
- Big rides close for months (Formula Rossa since May 2026; Yas Waterworld rides in Nov): check ride-status pages before naming rides.

## Fact checking and sources
- If sources disagree, leave the fact out or say "our team confirms" (Aquarium 10pm vs 11pm; Grand Mosque 8:30pm vs 9pm; Miracle Garden child 3–12 vs 3–11). Pre-season news: use a fact only when two sources agree, phrase old rules as "in past seasons".
- WebFetch works best through the web-fetch agent. Usually fetchable: dubaiframe.ae, emirates.com Dubai Experience pages, uae.emaar.com, dubaipass.visitdubai.com, experiences.visitdubai.com/productDetail/<id> (some pages from 2021, use only to confirm), louvreabudhabi.ae/en/visit/plan-your-visit (no www), dubaimiraclegarden.com (FAQ answers collapsed; use "Know before you go"), skidxb.com offer pages, szgmc.gov.ae, ferrariworldabudhabi.com/en/faq, wbworldabudhabi.com/en/faq, yaswaterworld.com/en, arabianbusiness.com, gulfnews.com, khaleejtimes.com, bemyguest.ae, dubai.platinumlist.net, Wikipedia, guide.michelin.com, attractions.dnatatravel.com, ticketfairy.com.
- Often blocked: globalvillage.ae, visitdubai.com, mediaoffice.ae, atlantis.com, thedubaiaquarium.com, kidzania.ae, legoland.com, imgworlds.com, dubaisafari.ae, thegreenplanetdubai.com, dubaiairports.ae, zayedinternationalairport.ae. Find host/mirror variants with WebSearch before giving up. Unattended Editor runs are often blocked for every host: rely on the feed then.
- Official hours for Yas parks are not stated on their sites: say "our team confirms the hours". All three: under 3 free, 1.1 m price tier.

## Technical
- The TravelDesk image CDN is blocked from the sandbox (since 4 Nov), so alt text needs a run that can view photos; the alt-text [edit] item keeps growing (11+ tours).
- The sandbox proxy re-signs TLS and blocks www.kwikar.com and crt.sh: SSL expiry and the www redirect can only be checked by the Actions SEO check.
- kwikar.com answers 403 to headless Chrome from GitHub runners; pagespeed.json falls back to a local copy. Sandbox Lighthouse (CHROME_PATH = Playwright Chromium) works on the live site: home 98/100/96/100, Burj tour 99/92/96/100 (12 Nov).
- HTML is served with Cache-Control: no-cache (browsers showed cached pages after deploys).
- Search Console (7 Nov): property in kwikarkwikar31@gmail.com; old-site URLs now 301; "Alternative page with proper canonical" and noindex /search are expected.
- Event pages (F1 613, 13 Nov): offers often have no current price until the event dates (pricingPeriods start on day 1), so the auto From price and "Runs on: Every day" rows are misleading; hide Price/Runs on/Options and don't use {from}. abudhabigp.com/en/faq, gulfnews.com, formula1.com and dubicars.com were fetchable via the web-fetch agent; the official FAQ had wrong concert dates (4/7 Dec), so cross-check line-ups.
- Writer 13 Nov: Wikipedia (en.wikipedia.org) was blocked and wam.ae returns an empty JavaScript shell, but dubai-online.com/essential/weather, weatherspark.com, emirates247.com, tradearabia.com and khaleejtimes.com could be fetched via the web-fetch agent. For climate numbers give rounded ranges where two sources differ by 1–2°C; phrase Ramadan/Eid dates as astronomers' forecasts.

- Writer 14 Nov (NYE cruises): operator pages can contradict themselves (Alexandra NYE: landmark in Al Jaddaf, map pin in Dubai Marina; itinerary boarding 8:30pm vs offer notes 9pm/9:30pm). Use the offer notes for times, leave the berth to "our team sends the exact berth", and never promise a Burj Khalifa fireworks view from a Marina-based boat unless two independent sources say so.

## Strategy (Strategist, 13 Nov)
- Full tour pages with checked facts shipped steadily (8 tours + 4 guides in 2 weeks) and the audit stays at 0 issues: keep one page per Writer run, quality over volume.
- Time-sensitive event pages (F1 3–6 Dec, New Year) must be live 2–3 weeks before the date to have a chance to rank; plan them first.
- keywords.md is the only demand data until Irfan adds the GSC/Bing secrets; items with G and B counts both ≥1 (e.g. "img worlds of adventure price" G5/B6) go first among evergreen pages.
- Top results for most targets are OTA listings or long generic lists; our gap is clear option comparison, checked rules and the WhatsApp "send your request" flow.
