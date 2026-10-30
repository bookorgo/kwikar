# SEO learnings

Short, factual notes that later runs should follow.

- SEO text must sit inside the site's own section design (eyebrow + heading + rule, fact rows, cards, FAQ cards). Plain long articles and duplicate tables looked "odd" to the owner (30 Oct 2026).
- Put long hub text below the listings, not above; visitors come for the tours first.
- Don't repeat the same list twice on a page (e.g. options table + option cards).
- Supplier data can be wrong (e.g. a private car option listed as "1 hour"); hide such automatic glance rows with glance_hide and state the checked fact instead.
- Photos come from the supplier API in a fixed order; check the actual images before writing alt text.
- Browsers may show a cached page after a deploy; HTML is now served with Cache-Control: no-cache.
- In unattended runs WebFetch to globalvillage.ae, visitdubai.com and mediaoffice.ae was blocked (permission prompt unanswered); arabianbusiness.com worked. Cross-check news facts with the supplier offer notes in the feed (`details.<id>.offers[].desc`) and leave out anything only one unofficial source states.
- Earlier hand-written glance rows can be wrong (Global Village hours said Mon–Thu/weekends; real split is Sun–Wed / Thu–Sat). Re-check old rows when you fill a page.
- dubaiframe.ae/en/plan-your-visit and emirates.com (Dubai Experience pages) could be fetched in unattended runs; the TravelDesk image CDN is blocked from the sandbox, so alt text needs a run that can view the photos. Supplier FAQs can contradict supplier offer notes (Dubai Frame 9am vs 8am): use the official page.
- qa.py passed a 171-char meta description; check the rendered length yourself.
- Run of 30 Oct 16:30 UTC: thedubaiaquarium.com could not be fetched (permission prompt unanswered); uae.emaar.com and emirates.com/bh/... Dubai Experience pages worked. When sources disagree on hours (Aquarium 10pm vs 11pm), say "open every day, our team confirms the time" instead of a time.
- Screenshot via a local server (`python3 -m http.server` in public_html); file:// loses the CSS because asset paths are absolute.
- Run of 30 Oct 17:10 UTC: every WebFetch (dubaiframe.ae, uae.emaar.com, atthetop.ae) was blocked by an unanswered permission prompt. Itinerary-style guides can still ship by reusing only facts already checked and sourced in tour-extras.json; leave out anything new (e.g. Dubai Fountain times).
