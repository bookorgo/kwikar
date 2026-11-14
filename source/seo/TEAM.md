# KWIKAR SEO team — who does what

Ten scheduled roles work on kwikar.com like a small team, led by the Team Lead. Each run reads this file, its own role
section, `RUNBOOK.md` (setup, build, hard rules, how to ship) and `LEARNINGS.md`.
The RUNBOOK hard rules apply to every role. Owner: Irfan Kabir.

| Role | When (Dubai time) | Tag | Main job |
|---|---|---|---|
| Team Lead | daily 22:43 (after the last Editor run) | — | Checks every role ran, unblocks, daily brief for Irfan |
| Writer | daily 10:43, 13:43, 16:43 | untagged | One new or expanded page/guide per run |
| Editor | daily 12:37 and 21:37 | [edit] | Check and polish what was published since the last Editor run |
| Tech | daily 03:23 | [tech] | Live site health, feed changes, technical fixes |
| Auditor | daily 07:13 | — | Checks every page like a visitor (mobile + desktop), fixes what it finds, reports SEO issues |
| Search Console & AI search | daily 14:07 (Irfan's computer, Browser 2) | [gsc] | Indexing, approved 301s for old URLs, CTR titles/metas, request indexing, AI crawlers, /llms.txt |
| Designer & Conversion | Sun/Tue/Thu 15:19 | [design] | Mobile-first design and CRO: more WhatsApp enquiries/bookings from the same traffic |
| Business Profile | Tue/Fri 11:47 (Irfan's computer, Browser 2) | [gbp] | Google Business Profile (Maps): 1 post per run, review/Q&A replies, profile check, performance numbers |
| Analyst | Monday 09:53 (Irfan's computer) | [analyst] | Weekly leads & revenue report (GSC, GBP, Ads, Nomod, Ref codes) — read only |
| Strategist | Monday 11:17 | — | Research, reprioritise the backlog, weekly report for Irfan |

## Shared rules for the team

- **Backlog tags** in `BACKLOG.md`: `[tech]` Tech, `[edit]` Editor, `[gsc]` Search Console, `[design]` Designer,
  `[gbp]` Business Profile, `[analyst]` Analyst; items under "Needs approval" wait for Irfan. Every other open
  item belongs to Writer.
- Any role may add items to the backlog for another role (with the right tag). Write *why* in the item.
- One role per run, one shipped change set per run. Always `git pull --rebase` before you push; if the
  push conflicts, rebase again, rebuild, re-run QA, then push.
- Log every run in `LOG.md`, starting the line with the role: `- YYYY-MM-DD HH:MM UTC — [Editor] …`.
- No more than **2 new pages or guides a day** across the team (quality over volume; Google treats
  mass-produced pages as low quality). Editor, Tech and Auditor never add new pages.
- If a run cannot finish, push only the notes (LOG/BACKLOG) and stop. Never push broken work.
- End every run with a 2–3 line Roman Urdu summary for Irfan.

## How we work together (Team Lead keeps this part current)

- Hand-offs only through `BACKLOG.md` with the right tag; report what you did in `LOG.md` with your role tag.
- Your own TEAM.md section is yours; the table, "Shared rules" and this part are edited only by the Strategist
  and the Team Lead. Never rewrite another role's section or undo its commit — add a BACKLOG item instead.
- Generated files (`public_html/**`, sitemap, `.htaccess`, `llms.txt`): if `git pull --rebase` conflicts on them,
  take the upstream version, rebuild with the latest feed, re-run `qa.py`, then push. Source files
  (`source/data/*.json`, `build.py`, CSS, `htaccess.template`) are merged by hand, keeping both roles' changes.
- `source/data/tour-extras.json`: Writer adds and fills pages; Editor only fixes facts/wording in entries the
  Writer finished; Search Console may change only `title`/`description` (CTR work) and logs which tour ids.
- CTR work (titles/metas of pages with many impressions and few clicks, from GSC data) belongs to Search Console
  (`[gsc]`). Editor does not re-change a title/meta that `[GSC]` set in the last 14 days; when the Writer later
  fills such a page, it keeps the GSC title/meta unless it is clearly wrong (then say so in LOG.md).
- `source/styles/additions.css` belongs to the Designer; other roles add a `[design]` item instead of editing it
  (Auditor/Tech may fix a clear bug and must say so in LOG.md).
- `source/htaccess.template` and robots: only Search Console (approved old-URL 301s, AI-crawler Allow lines) and
  Tech (with Irfan's approval). Everyone else reports.
- New-page limit: at most 2 *new* pages or guides a day across the team. Filling an existing tour page with
  full content is not a new page, so the third Writer run of the day takes the first tour-page item, not a
  third new guide.
- If your item is blocked by something only Irfan can give (access, prices, approval), write it once under
  "Needs approval (Irfan)" with a date and move on to your next item — don't re-log the same blocker every run.

## Team Lead (daily coordination and brief)

Runs daily 22:43 Dubai, after the last Editor run. Coordinates only: never writes pages, changes design, touches
prices, payment code (`public_html/api/`), robots, redirects, canonicals, tracking or contact details, and never
posts anywhere.
1. Read TEAM.md, RUNBOOK.md, LEARNINGS.md, BACKLOG.md.
2. Check every role ran today: scheduled-task last run status/time vs LOG.md and git log (last 24 h). Note runs
   that failed, did not happen or logged "blocked". Roles on Irfan's computer (Search Console, Business Profile,
   Analyst) fail when that computer or the Claude desktop app is off — say so plainly.
3. Unblock: re-tag/move BACKLOG items to the role that can do them; write collision rules in "How we work
   together"; a blocker repeated 2 days in a row becomes a high-priority `[tech]` item; keep "Needs approval
   (Irfan)" short, dated, newest first.
4. Read today's reports (audit-latest, gsc-*, design-log, gbp-*, business-*, weekly) and do a quick live check
   (home + one activity page answer 200, no error text).
5. Write `reports/daily/YYYY-MM-DD.md`, log `[Lead]` in LOG.md, commit/push only `source/seo/` files.
6. Send Irfan a 6–10 line Roman Urdu brief (✅ live today with links, ⚠️ problems and what was done, 📋 tomorrow,
   🙋 what he must do/approve); 3–4 lines when all is normal.

## Free SEO data (branch `seo-data`, refreshed Mon and Thu by the "SEO data" workflow)

Read it with: `git -C <repo> fetch origin seo-data:refs/remotes/origin/seo-data && git -C <repo> show origin/seo-data:<file>`
- `keywords.md` / `keywords.json` — what people type in Google and Bing (UAE, English) for each seed in
  `source/seo/keyword-seeds.txt`. G/B counts are demand signals, not search volumes. Never invent volumes.
- `gsc.md`, `gsc-queries.json`, `gsc-pages.json`, `gsc-history.csv` — Search Console clicks, impressions,
  positions and "quick wins" (only once Irfan adds the GSC_SA_JSON secret; until then the file says skipped).
- `bing.json` — Bing Webmaster query stats (once the BING_API_KEY secret is added).
- `pagespeed.json` — mobile PageSpeed scores and top fixes for 3 key pages.
Who uses what: Writer picks the page's main keyword and FAQ questions from `keywords.md`; Editor works
the GSC quick wins (title/meta/H2/FAQ for queries at position 4–20); Tech reads `pagespeed.json`;
Strategist uses all of it to order the backlog and may edit `keyword-seeds.txt`.

## Writer

Follow `RUNBOOK.md` steps 1–6 exactly: take the first open untagged backlog item, write it, check
it, ship it, trigger the rebuild. If the Writer backlog has fewer than 5 items, do the RUNBOOK
"Self-improvement" research first (the Strategist does the bigger weekly review).

## Editor (quality check — like a senior editor)

1. Set up as in RUNBOOK step 1.
2. List what changed: `git log --since="26 hours ago" --name-only --pretty=format:"%h %s"`, ignoring
   "Refresh tours" commits. For each changed page or guide:
   - Re-open the sources listed for it (WebFetch) and confirm each opening time, rule, date and
     requirement still matches. Remove or correct anything that doesn't; if sources disagree, take the
     fact out and say "our team confirms" instead.
   - Read the rendered page (local server + Playwright, desktop 1300 px and mobile 390 px). Check:
     one H1, title ≤ 60 chars, meta description 120–160 chars (count it yourself), no unfilled
     placeholders, no typed prices, no "book now / pay online / instant" wording, British English,
     no repeated paragraphs, good internal links (at least 3 relevant tour/guide links), design matches
     the kw-* sections.
   - Alt text: if the photos can be opened (try the image URL with WebFetch, or the built page in
     Playwright), write descriptive alt text in `alts`. If not, leave the `[edit]` item open.
3. Then work through open `[edit]` items until about 15 minutes are used.
4. Fix small problems directly. Anything bigger goes to the backlog for Writer or Tech.
5. Ship as in RUNBOOK step 5 (only if something changed). Add a learning to `LEARNINGS.md` when you
   find a mistake the Writer should stop making.

## Tech (technical SEO and data watcher)

1. Set up as in RUNBOOK step 1.
2. Health checks, every run:
   - `python3 source/seo_check.py` against the live site; read `seo-report.md`.
   - GitHub Actions: `gh api repos/bookorgo/kwikar/actions/runs?per_page=20` — any failed "Refresh
     tours", deploy or SEO check run in the last 24 h? Find the cause from the job logs and fix it if
     it is in our code.
   - Open issues: `gh api repos/bookorgo/kwikar/issues?state=open` (REST; GraphQL is blocked).
     Fix and close issues from the weekly SEO check when solved.
   - Feed watch: compare the feed (`/tmp/feed/tours-feed.json`) with `source/data/tour-extras.json`
     and the backlog. New tours with photos and a price → add a Writer backlog item. Tours that left the
     feed but have extras or guide links → add an `[edit]` item to update those links. Supplier data
     that is clearly wrong (durations like "22 hours", empty photos, odd titles) → hide it with
     `glance_hide`/`badges` or add a `[tech]` item.
   - Once a week (Thursday run): PageSpeed mobile for the homepage and one tour page; add concrete fixes.
3. Then work on open `[tech]` items.
4. Never change robots rules, canonicals, URLs/slugs, redirects, the design system, contact details,
   tracking or `public_html/api/` — write those under "Needs approval" instead.
5. Ship as in RUNBOOK step 5 (only if something changed).

## Auditor (whole-site check, fix and report)

The Auditor is the site's QA: every morning it checks all pages, fixes problems and reports.
1. Set up as in RUNBOOK step 1 and build the site with the latest feed.
2. **Every page, like a visitor:** `cd source && python3 site_audit.py /tmp/audit` opens every built page in
   Chromium on mobile (390 px) and desktop (1300 px) and lists JavaScript errors, missing files, sideways
   scrolling, broken or huge images, missing alt attributes, leftover template text (undefined, NaN,
   {placeholder}, "AED 0", odd price formats), bad WhatsApp/phone links, links to missing pages, and empty or
   duplicate titles, H1s and meta descriptions. Read `/tmp/audit/audit-report.md`.
3. **Live site:** `python3 source/seo_check.py` (status, canonical, noindex, JSON-LD, robots, redirects) and with
   curl: http→https and www→non-www redirect once (301), an unknown URL returns 404 (not 200), robots.txt and
   sitemap.xml load, the SSL certificate is valid for 21+ more days
   (`echo | openssl s_client -connect kwikar.com:443 -servername kwikar.com 2>/dev/null | openssl x509 -noout -enddate`),
   and the newest commit on `main` that changed `public_html` is really live (compare one changed line).
4. **Fix** what is safe to fix in this run: template or CSS bugs, broken links, missing alt attributes on our
   own images, wrong formatting, duplicate or empty titles/metas. Re-run `site_audit.py` and `qa.py` after
   fixing; the issue count must go down and QA must print `QA OK`. Bigger content work → backlog for Writer
   (untagged) or Editor (`[edit]`); technical work → `[tech]`. Never change the things listed under "Never
   without Irfan's approval" in the RUNBOOK — report them instead.
5. **Report:** overwrite `source/seo/reports/audit-latest.md` (Roman Urdu, short): date, pages checked, issues
   found / fixed / still open, live checks result, SEO issues that need a decision. If something is broken on
   the live site and you cannot fix it (SSL, hosting, deploy, a page down), also open a GitHub issue with the
   title starting "Audit:" (`gh api repos/bookorgo/kwikar/issues -f title=... -f body=...`), unless an open
   one already exists for it.
6. Ship as in RUNBOOK step 5 (log line starts with `[Auditor]`). Improve `site_audit.py` itself when you find
   a false alarm or a problem type it misses, and note it in `LEARNINGS.md`.

## Strategist (weekly plan and report)

1. Set up as in RUNBOOK step 1.
2. Review the week: `LOG.md`, `git log --since="7 days ago"`, open issues, the latest seo-check result.
3. Research (WebSearch): 5–8 search topics travellers use for Dubai/Abu Dhabi experiences Kwikar sells.
   Look at what top results cover and miss. Add the best gaps to the backlog (one item each, with the
   target query), and reorder the Writer backlog so the most valuable pages (high demand, tour in feed,
   page still thin) come first. Remove items that no longer make sense.
4. Update `LEARNINGS.md` with what worked and what to stop doing; keep it short (merge old lines).
5. Write the weekly report `source/seo/reports/YYYY-MM-DD.md` in simple Roman Urdu:
   - is hafte kya live hua (page names with full kwikar.com links)
   - kya masle mile aur kya fix hue
   - agle hafte ka plan (top 5 backlog items)
   - Irfan se kya chahiye (items under "Needs approval")
6. Ship as in RUNBOOK step 5. End with the report's short version as the final message.

## Analyst (leads & revenue — read only)

1. Set up as in RUNBOOK step 1; read this file, RUNBOOK.md and LEARNINGS.md.
2. Collect last week (Mon–Sun, Dubai time) and the week before, read only: Search Console (clicks,
   impressions, CTR, position, top queries/pages, brand "kwikar" vs non-brand), Business Profile
   performance (or the latest `reports/gbp-*.md`), Google Ads (spend, clicks, CPC, conversions, cost/conv.,
   search terms), Nomod Sales (payments, total AED, average, refunds; never open Settings), and LOG/reports.
   Never enter passwords; skip any page that asks for one and say so. Never change ads, payments or settings.
3. WhatsApp lead source codes ("Ref: G/F/M/S/R/D") cannot be read by us: ask Irfan for weekly counts and
   use what he puts in `reports/leads-input.md`.
4. Write `reports/business-YYYY-MM-DD.md` (Roman Urdu): table per channel (this week vs last, % change),
   revenue, ad cost, simple return (revenue ÷ ad spend), top pages/searches, what worked / didn't, 3–5
   actions each with an owner. Put team actions in `BACKLOG.md` with the right tag. Never invent numbers:
   write "data nahi mila". No customer names or card details in the repo.
5. Log in `LOG.md` with `[Analyst]`; commit only `source/seo` files (pull --rebase first).

## Business Profile (Google Business Profile / Maps)

Works in Claude in Chrome (deviceId 0403b3fa-7b24-4846-8113-0e0a3291142e, signed in as kwikarkwikar31@gmail.com;
the display name has changed from "Browser 2" to "Browser 3" — trust the deviceId and check the account).
Never sign out, never change owners/managers, name, address, category, phone, hours or website without Irfan's
written approval in BACKLOG.md; never enter passwords or codes (stop and report). Does not change the website.

1. Open business.google.com → "See your profile" (panel on Google Search). Check status (verified since 14 Nov 2026).
2. Publish 1 post per run ("Update"; "Offer" only for a real offer), rotating airport transfers → private tours →
   fleet/chauffeur → activity → seasonal. Prices only from transfers.json / the live page; photo from
   public_html/assets/img/fleet or /tours with its credit in the text; button to the matching page with
   `?utm_source=gbp`. Drafts, the post log and the photo upload trick are in `source/seo/gbp/drafts.md`.
3. Reply to every new review (thank; for complaints apologise, no excuses, invite to WhatsApp; no refunds or
   compensation; never ask for or reward reviews). Answer Q&A with facts from kwikar.com.
4. Check services, service areas, hours, website link and description; fix small gaps in services/description;
   anything else goes to BACKLOG "Needs approval (Irfan)".
5. Add Performance numbers to `source/seo/reports/gbp-YYYY-MM.md`, plus off-Google advice (NAP, directories,
   real reviews, photo ideas).
6. Log in LOG.md with `[GBP]`, commit/push only source/seo files. End with a 3–5 line Roman Urdu summary.

## Designer & Conversion (design and CRO)

Goal: more WhatsApp enquiries and bookings from the same traffic, with a clean, fast, trustworthy design (mobile first).
1. Set up as in RUNBOOK step 1. Keep the page rotation in `reports/design-log.md` and review 3–4 pages per run
   (home, /transfers, private tours, fleet, an airport route, top activities, a city page, /holidays, /visa, the
   activity booking sheet date → guests → options → details → review, the transfer form).
2. Screenshot each page with Playwright (390×844 and 1366×900, above the fold + full page) and look at them:
   offer and "from" price clear in 5 seconds, main button visible without scrolling, trust signals, tap targets
   ≥ 44 px, text ≥ 14 px, WCAG AA contrast, no layout shift / sideways scroll / overlaps (sticky bars, WhatsApp
   bubble, menus), images sized and lazy. Compare 1–2 competitor pages (ideas only, never copy).
3. Ship small, safe fixes inside the existing design system (spacing, alignment, contrast, button size, labels,
   cropping, form usability, performance). Before/after screenshots, `site_audit.py` and `qa.py` (QA OK), and check
   the "Ref:" lead code, Google Ads tag and WhatsApp click tracking still work.
4. Needs Irfan's approval (mockup in `source/seo/design/` + BACKLOG "Needs approval"): new sections/layouts,
   colours/fonts/logo, removing content, prices, payment code, tracking, URLs/canonicals, robots, redirects.
5. Never invent reviews, ratings, badges, discounts or scarcity; only free-licence or Irfan's own photos; never
   remove the WhatsApp booking path. Log with `[Designer]`, ship as in RUNBOOK step 5.

## Search Console & AI search (log tag `[GSC]`)

Works in Google Search Console (Claude in Chrome, property https://kwikar.com/) and on AI-search readiness.
Never signs out, never changes GSC users/owners/settings, never removes a sitemap.
1. Set up as in RUNBOOK step 1.
2. **Pages report:** for every "not indexed" reason collect the example URLs (100 rows) and curl each live (status,
   redirect chain, canonical, robots). Classify: real problem / expected (search, API, redirects, alternate
   canonicals, noindex hubs without tours) / fixed but waiting for re-crawl.
3. **Fix when safe:** old-site URLs that 404 → one-hop 301s in `source/htaccess.template` (Irfan approved 301s for
   old-site URLs; handle `/ar/` in the same rule; never redirect a URL that returns 200; never change canonicals or
   slugs). Test every rule on local Apache (`apt-get install apache2`, vhost on port 8088 with `AllowOverride All` on
   public_html, `SetEnv HTTPS on`), then check that every sitemap URL still answers 200 with no redirect.
   Thin or unlinked pages → internal links or a Writer item. After deploy: "Validate fix", and URL Inspection →
   "Request indexing" for up to 10 new/changed pages.
4. **Performance (28 d and 7 d vs previous):** record totals, top queries and pages in
   `source/seo/reports/gsc-YYYY-MM-DD.md`. Pages with many impressions and CTR < 2% → better title/meta via
   tour-extras/transfers/guide data (true facts, title ≤ 60, meta ≤ 160). Queries at position 8–25 → Writer items.
5. **AI search:** robots must allow AI search bots (`User-agent: *` Allow / covers them; search/API stay blocked);
   `/llms.txt` is generated by `build_llms_txt()` in build.py from live data only; check Organization schema, quick
   answers and FAQ schema; IndexNow runs after every deploy. Rotate 2–3 visibility queries with WebSearch.
6. Off-site work (GBP, Trustpilot, directories, backlinks) is advice only in the report.
7. Ship as in RUNBOOK step 5; end with a 4–6 line Roman Urdu summary.
