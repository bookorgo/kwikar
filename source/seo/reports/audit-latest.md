# Audit report — 14 Nov 2026 (09:45 UTC)

**Pages check hue:** 231 (har page mobile 390 px + desktop 1300 px), latest feed ke saath build (232 HTML, 107 tour pages — tour 203 Shindhaga Museum feed se nikal gaya). Live sitemap: 200 URLs.

## Masle
- **Mile:** 0 (site_audit: koi JS error, missing file, sideways scroll, toota image, missing alt, placeholder, ajeeb price, galat WhatsApp/phone link, toota link ya duplicate title/H1/meta nahi).
- **Fix hue:** 0 (zaroorat nahi thi). QA OK.
- **Abhi khule:** 0.
- Extra check (khud script se): 201 indexable pages par title ≤ 60, meta 120–160, ek H1, meta poore jumle par khatam ✔ (naya Alexandra NYE page bhi shamil).

## Live checks
- seo_check: 200/200 OK (status, canonical, noindex, JSON-LD, robots, purane redirects).
- http → https: 301 ✔ · Unknown URL: 404 ✔ · robots.txt (repo jaisa) aur sitemap.xml: 200 ✔.
- Shindhaga Museum (tour 203) ab live par 410 Gone deta hai ✔ — tour feed se hata, build ne khud kiya; koi andar ka link us par nahi.
- Latest deploy live ✔ (Refresh tours 14 Nov 01:27 — "last checked 14 Nov 2026"; Writer ka naya Alexandra New Year's Eve page bhi live).
- GitHub Actions pichhle 24 ghante: sab green.
- SSL: sandbox se check nahi hota (proxy apna certificate dikhata hai). Let's Encrypt ~18 Dec tak valid, khud renew hota hai.
- www → non-www: sandbox se block. Issues #1 aur #3 abhi bhi khule (wahi 2-hop masla).

## Irfan ka faisla chahiye
- **www redirect (issue #1, #3 duplicate):** hPanel → Security → SSL → "Force HTTPS" off kar dein (.htaccess pehle se HTTPS force karti hai), ya chhor dein — asar kam hai. #3 ko #1 ka duplicate kar ke band kar sakte hain.
- **URL typo:** /activities/abu-dhabi/abu-dhabi-city-tour-form-abu-dhabi-russian-speaking-guide ("form" → "from"). Page noindex hai; slug badalne ke liye 301 aur aapki approval chahiye.
