# KWIKAR SEO backlog

Team roles are in TEAM.md. `[tech]` items are for Tech, `[edit]` items for Editor, untagged items for Writer (first open item first). Keep each item one page or one fix.

## Open

- [ ] Dubai Water Canal Dhow Cruise (tour 227): full tour-extras content
- [ ] Guide: "Ferrari World vs Warner Bros. World vs Yas Waterworld"
- [ ] Vintage G-Class Heritage Safari (tour 204): full tour-extras content
- [ ] Guide: "Best time to visit Dubai: month by month"
- [ ] Alexandra New Year's Eve Gala Dinner (tour 289): full tour-extras content before December (time-sensitive; supplier has 8 options but no prices in the feed yet, so write "our team confirms the price"). Tech set title/meta on 3 Nov

- [ ] Guide "Dubai with kids": when official sites can be fetched, add checked child rules (free ages, height limits, hours) for KidZania, LEGOLAND, The Green Planet, IMG Worlds, Ski Dubai and Dubai Safari Park. Supplier notes disagree (e.g. Green Planet free under 2 vs under 3), so the guide currently says "send ages, our team confirms"

- [ ] [edit] Alt text for Louvre Abu Dhabi (157), Dubai Frame (175), Dubai Aquarium (144), Aquaventure (142) and Ferrari World (161) and Dubai Miracle Garden (185: photos 3973, 1954, 1957, 3393), Ski Dubai (222: photos 1321–1326) photos, plus the Dubai with Kids guide hero (photo 2407, alt is just the H1). Image CDN still 403 from the sandbox on 4 and 5 Nov. 6 Nov: CDN still blocked (proxy rejects the host) 7 Nov Editor: CDN still blocked (ERR_TUNNEL_CONNECTION_FAILED); also add the Abu Dhabi day-trip guide hero (photo 2881, alt is just the H1). 8 Nov Writer: also Lotus Royale (28: photos 3975–3994, no alts yet). 10 Nov Editor: CDN still blocked (proxy connect_rejected).
- [ ] [edit] Global Village (102): add season end date, free-entry age rules and transport once an official source can be fetched. 3 Nov: globalvillage.ae still blocked. Khaleej Times (15 Sep) says season runs "through May 2027", exact end date not announced; free entry "usually" under 3, 65+ and People of Determination (Gulf News: "senior citizens", no age); buses 102/103/104/106 (one source only). KT also gives Mon–Thu midnight / weekends 1am, which conflicts with our checked Sun–Wed / Thu–Sat split — keep ours until the official page can be read. 5 Nov: WebFetch blocked again (permission prompt unanswered). 6 Nov: all four sources (globalvillage.ae, Arabian Business, Gulf News, Khaleej Times) blocked; feed offer notes still confirm Sun–Wed 4pm–midnight, Thu–Sat 4pm–1am, gates close 30 min before, Tuesday families/ladies/couples 7 Nov: WebFetch still blocked (permission prompt). 10 Nov Editor: globalvillage.ae blocked again (permission prompt).

- [ ] Guide: "Dubai Airport to the city: taxi, metro or private transfer?" (target: dubai airport transfer, dubai airport taxi fare) linking the /transfers route pages; use only transfer prices from transfers.json
- [ ] Guide: "Dubai to Abu Dhabi: how to get there" (target: dubai to abu dhabi taxi price) linking /transfers/dubai-to-abu-dhabi
- [ ] [edit] Transfer pages: add 1–2 checked local facts per airport page (terminals, arrivals hall layout) with sources. 6 Nov: WebFetch blocked in the Editor run, not started; 7 Nov: blocked again; 10 Nov: dubaiairports.ae and zayedinternationalairport.ae blocked (permission prompt).

## Needs approval (Irfan)

- More transfer routes (e.g. Dubai Marina to Abu Dhabi, Dubai to Hatta, Dubai to Muscat) need prices in the rate card before pages can be built

- http://www.kwikar.com still goes to https://www first (2 hops) after the approved .htaccess swap was live (6 Nov 00:00 UTC): the http→https 301 is made by Hostinger itself (hcdn / hPanel "Force HTTPS"), before our .htaccess. Irfan: in hPanel → Security → SSL, if "Force HTTPS" is on, turn it off (our .htaccess already forces HTTPS), or leave it (Google follows 2 hops; low impact). Issue #1 (Tech, 6 Nov)
- Free data keys as GitHub secrets (Settings → Secrets → Actions): GSC_SA_JSON (Search Console service account, add its email as a user in Search Console), BING_API_KEY (Bing Webmaster → Settings → API access), PAGESPEED_API_KEY (Google Cloud, PageSpeed Insights API). Until then the seo-data branch has keyword ideas only

- Office address and trade licence number for the footer, About page and Organization schema
- GA4 measurement ID (events are already in the code)
- Xclusive Super Yacht Cruise (tour 68, /activities/uae/xclusive-super-yacht-cruise): the supplier gives no photos, no description, no categories and location "other", so the page is thin (only 2 option cards). Ask TravelDesk for details/photos, or approve noindex until they arrive (Tech, 5 Nov)
- Real Madrid World (268) is published at /activities/spain/real-madrid-world because the supplier location is "spain"; the park is at Dubai Parks and Resorts. Moving it to /activities/dubai/... needs a URL change + 301 (Writer, 4 Nov)

- Slug typo: /activities/abu-dhabi/abu-dhabi-city-tour-form-abu-dhabi-russian-speaking-guide ("form" should be "from"; title/H1 already fixed, page is noindex). Renaming needs a `slug` in tour-extras + 301 (Auditor, 5 Nov)

## Done

- [x] Lotus Royale Dinner Cruise (tour 28) full content (8 Nov 2026). Boarding 6:45pm, departure 7:30pm, 3 hours, Pier 7 by Dubai Marina Mall, smart casual, under-3 free, photo ID, route and Royale package contents from supplier notes cross-checked with experiences.visitdubai.com/productDetail/92695 and Platinumlist. Left out (one source or sources disagree): yacht length (220 ft, supplier only), days (supplier Wed/Fri/Sat vs Platinumlist daily; auto row from our offers kept), upper child age (supplier 10+ adult vs Platinumlist 11+), outside-food rule, wheelchair access, alcohol age. Supplier FAQ said boarding 19:00, its own terms and both sources say 6:45pm. Photo alt text still to do
- [x] Guide: "Abu Dhabi Day Trip from Dubai: What to See and How to Get There" /blog/abu-dhabi/abu-dhabi-day-trip-from-dubai (7 Nov 2026). Grand Mosque opening 9am, Friday midday closure/2:30pm reopening, online access pass, dress code, food/photo/children rules and free guided tours from szgmc.gov.ae (closing time left out: official pages say 8:30pm and 9pm; entry fees left out). Louvre Monday closing reused from our checked tour page. Qasr Al Watan hours left out (official hours page blocked; supplier says 11am–6pm). Tour itinerary from supplier offer 1774; drive time from transfers.json. Linked from the Louvre page
- [x] Ski Dubai (tour 222) full content (7 Nov 2026). Hours, last ticket, under-2/under-14/helmet rules, slope level 2 + waiver, -4°C and food rule from skidxb.com (snow-park-adnoc, slope pass, passes page) cross-checked with experiences.visitdubai.com; pass contents from supplier notes. Left out: ID/AED 25 card deposit, Mountain Thriller specs, ticket validity, hats (sources disagree or old). Supplier durations (1 h / 4 h) hidden. Photo alt text still to do
- [x] [tech] Homepage slider dots are now 24×24 px tap targets (dot drawn by ::before, same look); local Lighthouse mobile accessibility 91 → 100, target-size passes. IndexNow verified live: "IndexNow: HTTP 200 for 188 URLs" in the Update deploy branch run of 6 Nov 17:42 UTC (6 Nov 2026)
- [x] Holidays page /holidays: SEO content below the package listings (intro + facts, what a package can include, 4-step quote process, which package suits your trip, 7 FAQs with FAQPage schema); title "Dubai Holiday Packages and Trips Abroad" (48), meta 145. No outside facts used: only the catalog and our own booking/refund terms, so no sources needed (6 Nov 2026)
- [x] Guide: "Global Village Dubai Guide: Season 31 Timings and Tips" /blog/dubai/global-village-dubai-guide (6 Nov 2026). globalvillage.ae blocked again; hours/last entry/Tuesday rule from supplier notes + Arabian Business + Gulf News; Gardens of the World, Dragon Kingdom, Little Wonderers from Gulf News + Khaleej Times. Left out (one source only or not confirmed): end date, bus route numbers, parking prices, banned items, ticket prices. Free entry stated as "past seasons", our team confirms. Linked from the Global Village tour page
- [x] Transfers: 34 new pages (23 routes, 4 airports, 5 vehicle classes, hourly chauffeur) + new /transfers hub from the approved rate card (6 Nov 2026)

- [x] [tech] Approved by Irfan (6 Nov): www → kwikar.com rule now runs before the HTTPS rule, so http://www.kwikar.com reaches https://kwikar.com in one 301 (issue #1); card location label grey #697888 → #5f6b7a (contrast 4.2 → 5.1:1) (6 Nov 2026)
- [x] [tech] SEO check Action now also checks SSL expiry (problem under 21 days) and http→https / www→non-www 301s; outside GitHub Actions (sandbox proxy) these show as notes, not failures (5 Nov 2026)
- [x] [tech] IndexNow: public key file in public_html, source/indexnow.py pings changed sitemap URLs after each deploy (Update deploy branch + Refresh tours Actions); never fails a run (5 Nov 2026)
- [x] [tech] SEO data: when the PageSpeed API refuses (429, no key) the Action runs Lighthouse mobile on the runner instead; checks canonical URLs (no redirect) and lists only failing audits (5 Nov 2026)
- [x] Dubai Miracle Garden (tour 185) full content (5 Nov 2026). dubaimiraclegarden.com (home, FAQ, A380, floral clock, Butterfly pages) could be fetched: Season 15 dates 8 Oct 2026–31 May 2027, 9am–9pm, last entry 8:30pm, Gate 1, rules, Metro + bus 105. Upper child age left out (official 3–12 vs supplier 3–11); parking, wheelchair/pram access and People of Determination rules left out (FAQ answers collapsed). Photo alt text still to do
- [x] Louvre Abu Dhabi (tour 157) full content (5 Nov 2026). Hours, Monday closing, bag/food/photo/pram rules from the official plan-your-visit page and visitor regulations PDF. Sunday gallery closing left out (sources disagree: 6:30pm vs 8:30pm); free under-18 entry attributed to the supplier (official page not found). Photo alt text still to do
- [x] [Auditor] Category hub titles "Cruises Experiences" / "Luxury experiences Experiences" → "<Category> in Dubai & the UAE"; supplier typo "tour form" → "tour from" in names (no URL change); site_audit.py checks repeated words and this typo in titles/H1s (5 Nov 2026)

- [x] [tech] From-price fixes (5 Nov 2026): fast-track add-ons (name contains "add on"/"addon", or ids in `from_exclude`) no longer set the From price — Ferrari World 200→345, Sea World 250→375, Warner Bros. World 250→345, Yas Waterworld 150→295 in titles, hero, sticky bar, cards, schema, {from} and {price:ID}. KidZania (275) uses the child rate via `from_price: "child"` (From AED 195 per child). Writer may now use {from} on Ferrari World
- [x] [tech] Auto titles for long tour names cut at a natural break (longest of " – ", ":", ",", " (", " with ", " in ", " from "…, no open bracket, no trailing "and/of/with"); double spaces collapsed in tour and option names (no URL change) (5 Nov 2026)
- [x] Guide: "Dubai with Kids: Indoor and Outdoor Things to Do by Age" /blog/dubai/dubai-with-kids (4 Nov 2026). All official sites (kidzania.ae, legoland.com, thegreenplanetdubai.com, dubaisafari.ae, imgworlds.com, skidxb.com) blocked; only facts already checked on our tour pages are used, other places are described without ages/hours

- [x] Ferrari World Abu Dhabi (tour 161) full content (4 Nov 2026). Official ride page says Formula Rossa closed for maintenance (no date) and Roof Walk unavailable; page says so. ferrariworldabudhabi.com hours page did not render, visitabudhabi.ae / yasisland.com blocked: opening hours, ride list, food rules and Yas Express left out. Price row hidden and {from} not used (add-on sets the from-price, see [tech] item)
- [x] [tech] Option hours override (`offer_hours` in tour-extras; Aquarium Platinum "22 hours" hidden), qa.py now fails on title > 60, meta outside 120–160 (indexable pages) and "book now/checkout/pay online/instant confirmation" in visible text, 120–160 char metas for all hubs/service/info pages and short auto tour metas, supplier "Book now"/"during checkout" wording filtered in build.py (3 Nov 2026)
- [x] Aquaventure World Waterpark (tour 142) full content (30 Oct 2026). atlantis.com and visitdubai.com blocked; facts from the Dubai Pass (Dubai Tourism) page + supplier notes. Left out (sources disagree): free-entry age (under 2 vs under 3), child age bands, outside water allowance, park size, monorail/taxi details, wheelchair access, tower names. Photo alt text still to do
- [x] Guide: "3 Days in Dubai: A First-Timer's Itinerary" /blog/dubai/3-days-in-dubai-itinerary (30 Oct 2026). Only reuses facts already checked on tour pages; official sites could not be fetched this run. Dubai Fountain left out (show times not checked)
- [x] Dubai Aquarium & Underwater Zoo (tour 144) full content (30 Oct 2026). Opening hours and tunnel length left out: sources disagree (10pm vs 11pm close; 48 m vs 50 m). Photo alt text still to do
- [x] Dubai Frame (tour 175) full content (30 Oct 2026). Photo alt text not written: supplier images could not be opened from the run sandbox
- [x] Global Village (tour 102) full content; fixed wrong opening-hours row (30 Oct 2026). Still to add when the official site can be checked: season end date, free-entry age rules, location/transport

- [x] Burj Khalifa page content (30 Oct 2026)
- [x] Desert safari (Noble camp), Alexandra dhow, shared yacht, visa page content (30 Oct 2026)
- [x] Homepage SEO content and redesign of SEO sections (30 Oct 2026)
- [x] Guides: Burj Prime vs Non-Prime, best time for Burj, morning vs evening safari, dhow vs yacht (30 Oct 2026)
