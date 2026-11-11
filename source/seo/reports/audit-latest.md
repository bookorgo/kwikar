# Audit report — 11 Nov 2026 (03:25 UTC)

**Pages check hue:** 219 (har page mobile 390 px + desktop 1300 px), latest feed ke saath build (220 HTML, 107 tour pages). Live sitemap: 189 URLs.

## Masle
- **Mile:** 0 (site_audit: koi JS error, missing file, sideways scroll, toota image, missing alt, placeholder, ajeeb price, galat WhatsApp/phone link, toota link ya duplicate title/H1/meta nahi).
- **Fix hue:** 0 (zaroorat nahi thi). QA OK.
- **Abhi khule:** 0.
- Extra check (khud script se): 189 indexed pages par title ≤ 60, meta 120–160, ek H1, meta adhoore lafz par khatam nahi ✔.

## Live checks
- seo_check: 189/189 OK (status, canonical, noindex, JSON-LD, robots, purane redirects).
- http → https: 301 ✔ · Unknown URL: 404 ✔ · robots.txt aur sitemap.xml: 200 ✔ (live robots.txt repo jaisa hi).
- Latest deploy live ✔ (Refresh tours 11 Nov 01:15 UTC — live tour page par "11 Nov 2026").
- GitHub Actions pichhle 24 ghante: sab green (Refresh tours, Deep crawl).
- SSL: sandbox se check nahi hota (proxy apna certificate dikhata hai). Pichhli SEO check ke mutabiq Let's Encrypt ~17 Dec tak valid (aaj ~36 din baqi); 26 Nov ke baad 21 din se kam — Let's Encrypt khud renew karta hai, weekly SEO check Action dekhe.
- www → non-www: sandbox se block. Issues #1 aur #3 khule hain (wahi 2-hop masla).

## Irfan ka faisla chahiye
- **www redirect (issue #1, #3 duplicate):** hPanel → Security → SSL → "Force HTTPS" off kar dein (hamari .htaccess pehle se HTTPS force karti hai), ya aise hi chhor dein — asar kam hai. #3 ko #1 ka duplicate kar ke band kar sakte hain.
- **URL typo:** /activities/abu-dhabi/abu-dhabi-city-tour-form-abu-dhabi-russian-speaking-guide ("form" → "from"). Page noindex hai; slug badalne ke liye 301 aur aapki approval chahiye.
