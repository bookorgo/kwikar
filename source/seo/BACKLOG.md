# KWIKAR SEO backlog

Team roles are in TEAM.md. `[tech]` items are for Tech, `[edit]` items for Editor, untagged items for Writer (first open item first). Keep each item one page or one fix.

## Open

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
- [ ] Alexandra New Year's Eve Gala Dinner (tour 289): full tour-extras content before December (time-sensitive; supplier has 8 options but no prices in the feed yet, so write "our team confirms the price"). Tech set title/meta on 3 Nov
- [ ] [tech] Tour 161 (Ferrari World): the "Fast Track Ticket Add on" (offer 1348, AED 200, needs a separate general admission ticket) sets the auto "From" price in the hero, sticky bar, schema and {from}, so the page says "From AED 200" while entry costs more. Add a way to leave add-on offers out of the from-price (e.g. `from_exclude` in tour-extras, or skip offer names containing "Add on"). Writer avoided {from} on this page until then
- [ ] [tech] Auto titles for long tour names are cut mid-phrase (e.g. "…Gala Dinner New | KWIKAR"); cut at a natural break or drop words like "Theme Park" instead. Also collapse double spaces in supplier names (471 "Fly Board  Burj Al Arab", 472 "Donut Ride  Burj Al Arab")
- [ ] [tech] Add IndexNow (key file + ping from the rebuild Action for changed URLs) so Bing picks up changes faster

- [ ] [tech] KidZania (275): the feed "price" is the adult (accompanying) rate AED 90 while the child ticket is AED 195, so cards and the hero say "From AED 90" for a children's attraction. Use the child rate as the from-price for KidZania (or label it "adult"). Seen while writing the Dubai with kids guide (4 Nov)
- [ ] Guide "Dubai with kids": when official sites can be fetched, add checked child rules (free ages, height limits, hours) for KidZania, LEGOLAND, The Green Planet, IMG Worlds, Ski Dubai and Dubai Safari Park. Supplier notes disagree (e.g. Green Planet free under 2 vs under 3), so the guide currently says "send ages, our team confirms"

- [ ] [edit] Alt text for Dubai Frame (175), Dubai Aquarium (144) and Aquaventure (142) photos (earlier runs could not open the supplier images)
- [ ] [edit] Global Village (102): add season end date, free-entry age rules and transport once an official source can be fetched. 3 Nov: globalvillage.ae still blocked. Khaleej Times (15 Sep) says season runs "through May 2027", exact end date not announced; free entry "usually" under 3, 65+ and People of Determination (Gulf News: "senior citizens", no age); buses 102/103/104/106 (one source only). KT also gives Mon–Thu midnight / weekends 1am, which conflicts with our checked Sun–Wed / Thu–Sat split — keep ours until the official page can be read

## Needs approval (Irfan)

- Free data keys as GitHub secrets (Settings → Secrets → Actions): GSC_SA_JSON (Search Console service account, add its email as a user in Search Console), BING_API_KEY (Bing Webmaster → Settings → API access), PAGESPEED_API_KEY (Google Cloud, PageSpeed Insights API). Until then the seo-data branch has keyword ideas only

- Office address and trade licence number for the footer, About page and Organization schema
- GA4 measurement ID (events are already in the code)
- Real Madrid World (268) is published at /activities/spain/real-madrid-world because the supplier location is "spain"; the park is at Dubai Parks and Resorts. Moving it to /activities/dubai/... needs a URL change + 301 (Writer, 4 Nov)

## Done

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
