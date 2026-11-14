# Designer & Conversion — page rotation and run log

Rotation (3–4 per run, continue where the last run stopped):
1. Home  2. /transfers  3. Airport route page (rotate: DXB→Marina, AUH→Dubai, DXB→Downtown, SHJ→Dubai)
4. Lotus Royale + booking sheet (date → guests → options → details → review)  5. /transfers/private-tours
6. /transfers/fleet  7. Alexandra dhow  8. Desert safaris (Noble camp, Red Sands, morning)  9. Burj Khalifa
10. City page (/destinations/dubai, then Abu Dhabi)  11. /holidays  12. /visa  13. Transfer form (any route)

Next run starts at: 5 (/transfers/private-tours), 6, 7, 8.

## 2026-11-14 (run 1)
Checked: home, /transfers, /transfers/dubai-airport-to-dubai-marina (+ transfer form), Lotus Royale + full booking sheet; mobile 390×844 and desktop 1366×900. No sideways scroll on any page; desktop had no tap/text issues.
Fixed (source/styles/additions.css):
- Sticky "Request" / "Choose" links jumped to #transfer-enquiry with the heading hidden under the sticky header + service bar → `section[id]{scroll-margin-top}` (160 px mobile, 165 px desktop).
- Form fields were 14 px (iPhone zooms in on tap) → 16 px on mobile in the transfer/visa/contact forms and the booking sheet.
- Booking sheet details: country code + mobile now on one row (96 px + rest); transfer form: passengers + suitcases side by side (date/time stay stacked — the native date field is too wide for half width).
- Transfer form card padding 30 → 20/18 px on mobile (inputs 248 → 274 px wide).
- Header call / WhatsApp icons were 20×45 px tap targets → 44×44.
- "Choose ↗" links on transfer price rows 61×21 → 44 px tall.
- Sticky price bar "From" label #778291 (3.9:1) → #5f6b7a (5.1:1, the grey approved 6 Nov).
Checked OK: booking sheet all 5 steps, Ref: G added to wa.me links with ?gclid, generate_lead/whatsapp_click code unchanged.
Still small (next runs): category bar labels 10.5 px (icons carry the meaning); breadcrumb links 15 px tall; "View experience →" card links 21 px tall (whole card is a link?); homepage slider arrows 29 px.
Competitors: GetYourGuide and Klook block fetches; chauffeurr.ae homepage — trust row under the H1, booking widget on the first screen with live estimate and WhatsApp as a second option.
Mockups for Irfan: design/trust-strip-tour-pages.html, design/transfer-quick-request.html.
