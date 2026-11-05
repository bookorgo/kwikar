# Audit report — 5 Nov 2026 (03:35 UTC)

**Pages check hue:** 170 (har page mobile 390 px + desktop 1300 px). Live sitemap: 136 URLs.

## Masle
- **Mile:** 4 (site_audit ke naye check ke saath) + 9 kamzor category titles
  - 2 category pages ke title mein lafz double tha: "Luxury experiences Experiences", "Cultural experiences Experiences"
  - Russian-guide Abu Dhabi city tour ke title aur H1 mein supplier ki typo: "City Tour **form** Abu Dhabi"
  - Baqi 9 category titles bhi ajeeb the ("Cruises Experiences", "Events Experiences" waghera)
- **Fix hue:** sab. Ab 11 category pages ka title "<Category> in Dubai & the UAE | KWIKAR" hai, aur supplier names mein "tour form" → "tour from" (URL nahi badla).
- **Abhi khule:** 0 (site_audit 4 → 0, QA OK).
- site_audit.py ab title/H1 mein double lafz aur "tour form" typo bhi pakarta hai.

## Live checks
- seo_check: 136/136 OK (status, canonical, noindex, JSON-LD, robots, purane redirects).
- http → https: 301 ✔ · Unknown URL: 404 ✔ · robots.txt aur sitemap.xml: 200 ✔ (sitemap index, 3 sitemaps).
- Latest deploy live ✔ (Refresh tours 01:16 UTC — page par "last checked 5 Nov 2026").
- **SSL expiry aur www → non-www:** is run mein check nahi ho sake — sandbox ka proxy apna certificate dikhata hai aur www.kwikar.com ko block karta hai. Live site par koi kharabi nazar nahi aayi. [tech] item add kiya: ye do checks GitHub Action se chalein.

## Irfan ka faisla chahiye
- URL mein typo: /activities/abu-dhabi/abu-dhabi-city-tour-form-abu-dhabi-russian-speaking-guide ("form" → "from"). Page noindex hai, is liye asar kam hai; slug badalne ke liye 301 aur aapki approval chahiye.
