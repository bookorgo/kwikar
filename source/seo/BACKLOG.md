# KWIKAR SEO backlog

Team roles are in TEAM.md. `[tech]` items are for Tech, `[edit]` items for Editor, untagged items for Writer (first open item first). Keep each item one page or one fix.

## Open

- [ ] Ferrari World Abu Dhabi (tour 161): full tour-extras content. Target: "ferrari world tickets"
- [ ] Guide: "Dubai with kids: indoor and outdoor things to do by age"
- [ ] Louvre Abu Dhabi (tour 157): full tour-extras content. Target: "louvre abu dhabi tickets"
- [ ] Dubai Miracle Garden (tour 185): full tour-extras content (season dates already in extras). Target: "dubai miracle garden tickets"
- [ ] Guide: "Global Village guide: season dates, timings and tips"
- [ ] Transfers page: SEO content (quick answer, routes and starting prices from the estimator, airports, FAQs) in the existing design
- [ ] Holidays page: SEO content (what a package includes, how quotes work, FAQs) in the existing design
- [ ] Ski Dubai (tour 222): full tour-extras content
- [ ] Guide: "Abu Dhabi day trip from Dubai: what to see and how to get there"
- [ ] Lotus Royale Dinner Cruise (tour 28): full tour-extras content
- [ ] Dubai Water Canal Dhow Cruise (tour 227): full tour-extras content
- [ ] Guide: "Ferrari World vs Warner Bros. World vs Yas Waterworld"
- [ ] Vintage G-Class Heritage Safari (tour 204): full tour-extras content
- [ ] Guide: "Best time to visit Dubai: month by month"
- [ ] [tech] Tour pages: option cards show supplier "hours" as-is (Aquarium All Access shows "22 hours"); add a per-offer override or hide the hours line when it is clearly wrong
- [ ] [tech] Add IndexNow (key file + ping from the rebuild Action for changed URLs) so Bing picks up changes faster

- [ ] [tech] qa.py does not fail on long titles or short meta descriptions (Editor 3 Nov found 4 titles of 62–65 chars on hand-written pages). Make qa.py check rendered <title> ≤ 60 and meta 120–160 for pages with hand-written content
- [ ] [tech] Meta descriptions under 120 chars on template pages: /activities/ and all category hubs (72–86), /destinations/ and every country page (36–64), /contact, /about, /terms, /privacy, /refund-policy, /booking-information, /search, /holidays, /transfers; supplier-text metas 118–119 on kidzania-dubai, house-of-hype, the-palm-monorail. Write proper 120–160 char descriptions (templates or hub-intros)
- [ ] [tech] Supplier descriptions shown verbatim contain banned wording: "Book now" (hot-air-ballon-flight-in-dubai), "during checkout" (the-view-palm-jumeirah terms). Filter these phrases in build.py or override the text in tour-extras
- [ ] [edit] Alt text for Dubai Frame (175), Dubai Aquarium (144) and Aquaventure (142) photos (earlier runs could not open the supplier images)
- [ ] [edit] Global Village (102): add season end date, free-entry age rules and transport once an official source can be fetched. 3 Nov: globalvillage.ae still blocked. Khaleej Times (15 Sep) says season runs "through May 2027", exact end date not announced; free entry "usually" under 3, 65+ and People of Determination (Gulf News: "senior citizens", no age); buses 102/103/104/106 (one source only). KT also gives Mon–Thu midnight / weekends 1am, which conflicts with our checked Sun–Wed / Thu–Sat split — keep ours until the official page can be read

## Needs approval (Irfan)

- Office address and trade licence number for the footer, About page and Organization schema
- GA4 measurement ID (events are already in the code)

## Done

- [x] Aquaventure World Waterpark (tour 142) full content (30 Oct 2026). atlantis.com and visitdubai.com blocked; facts from the Dubai Pass (Dubai Tourism) page + supplier notes. Left out (sources disagree): free-entry age (under 2 vs under 3), child age bands, outside water allowance, park size, monorail/taxi details, wheelchair access, tower names. Photo alt text still to do
- [x] Guide: "3 Days in Dubai: A First-Timer's Itinerary" /blog/dubai/3-days-in-dubai-itinerary (30 Oct 2026). Only reuses facts already checked on tour pages; official sites could not be fetched this run. Dubai Fountain left out (show times not checked)
- [x] Dubai Aquarium & Underwater Zoo (tour 144) full content (30 Oct 2026). Opening hours and tunnel length left out: sources disagree (10pm vs 11pm close; 48 m vs 50 m). Photo alt text still to do
- [x] Dubai Frame (tour 175) full content (30 Oct 2026). Photo alt text not written: supplier images could not be opened from the run sandbox
- [x] Global Village (tour 102) full content; fixed wrong opening-hours row (30 Oct 2026). Still to add when the official site can be checked: season end date, free-entry age rules, location/transport

- [x] Burj Khalifa page content (30 Oct 2026)
- [x] Desert safari (Noble camp), Alexandra dhow, shared yacht, visa page content (30 Oct 2026)
- [x] Homepage SEO content and redesign of SEO sections (30 Oct 2026)
- [x] Guides: Burj Prime vs Non-Prime, best time for Burj, morning vs evening safari, dhow vs yacht (30 Oct 2026)
