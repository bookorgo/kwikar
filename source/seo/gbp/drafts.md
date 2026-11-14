# Google Business Profile — post drafts and post log

Rules: true facts only, prices only from the live site / `source/data/transfers.json`, no invented offers,
no "best/cheapest", no phone number in post text (Google often rejects it), button link with `?utm_source=gbp`.
Photos: fleet photos are CC BY-SA → put the credit line in the post text.
How to add a photo (the post dialog is a cross-origin frame, file inputs are not reachable): open the photo
on kwikar.com in a tab, draw it with a canvas overlay that fills the viewport (photo left, dark text panel right),
hover the mouse to the bottom-right corner, screenshot, then `upload_image` drag-and-drop onto
"Drag images and videos here".

## Posted

- 2026-11-14 — Update, airport transfers (DXB from AED 120 / Downtown from AED 150, Business Sedan),
  photo BMW 5 Series (Alexander-93, CC BY-SA 4.0) with text panel, button Learn more →
  https://kwikar.com/transfers?utm_source=gbp. Status: submitted, pending Google review.

## Next drafts (rotate: tours → fleet/chauffeur → activity → seasonal)

### 1. Private Dubai City Tour (next run)
Photo: public_html/assets/img/tours/dubai.webp (check its credit in the credits file first)
Button: Learn more → https://kwikar.com/transfers/private-tours/dubai-city-tour?utm_source=gbp

> See old and new Dubai in one private tour. Your chauffeur picks you up at your hotel or home in Dubai,
> drives you between the sights and waits while you explore: Al Fahidi, Dubai Creek and the souks,
> Jumeirah Mosque, the Burj Al Arab view, Palm Jumeirah, Dubai Marina and Downtown.
>
> Half day, up to 5 hours, from AED 650 per car in a Business Sedan (up to 3 guests). Family SUVs and
> 7-seat vans are available for bigger groups. Your chauffeur drives; he is not a tour guide.
>
> Send your request on WhatsApp with your date and hotel. Our team confirms the final price before you pay.

(Re-check stops, "not a guide" wording and AED 650 on the live page before posting.)

### 2. Chauffeur by the hour
Photo: public_html/assets/img/fleet/bmw-7-series.webp (First Class) — credit from fleet-credits.json
Button: Learn more → https://kwikar.com/transfers/chauffeur-service-dubai?utm_source=gbp

> Need a car and driver for meetings, shopping or a day out in Dubai? Hire a private chauffeur by the hour
> with KWIKAR: from AED 150 per hour in a Business Sedan, minimum 3 hours. First Class (Mercedes S-Class,
> BMW 7 Series), 7-seat Mercedes V-Class and Cadillac Escalade / GMC Yukon XL are also available.
>
> Fuel, tolls and parking are included. Send your request on WhatsApp with the date, start time and
> stops. Our team confirms the final price before you pay.
>
> Photo credit: <artist>, <licence>, via Wikimedia Commons.

### Later ideas
- Activity: a popular dhow cruise or desert safari, "from AED X" only as shown on the live tour page that day.
- Seasonal: New Year's Eve cruises / Sky Views (no prices in the feed yet → "our team confirms the price"),
  Abu Dhabi F1 weekend 3–6 Dec (airport and Abu Dhabi transfers, no event prices).
