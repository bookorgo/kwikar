# KWIKAR SEO team — who does what

Four scheduled roles work on kwikar.com like a small team. Each run reads this file, its own role
section, `RUNBOOK.md` (setup, build, hard rules, how to ship) and `LEARNINGS.md`.
The RUNBOOK hard rules apply to every role. Owner: Irfan Kabir.

| Role | When (Dubai time) | Main job |
|---|---|---|
| Writer | daily 10:43 and 16:43 | One new or expanded page/guide per run |
| Editor | daily 21:37 | Check and polish what was published in the last 24 h |
| Tech | daily 03:23 | Live site health, feed changes, technical fixes |
| Strategist | Monday 11:17 | Research, reprioritise the backlog, weekly report for Irfan |

## Shared rules for the team

- **Backlog tags** in `BACKLOG.md`: items starting with `[tech]` belong to Tech, `[edit]` to Editor,
  items under "Needs approval" wait for Irfan. Every other open item belongs to Writer.
- Any role may add items to the backlog for another role (with the right tag). Write *why* in the item.
- One role per run, one shipped change set per run. Always `git pull --rebase` before you push; if the
  push conflicts, rebase again, rebuild, re-run QA, then push.
- Log every run in `LOG.md`, starting the line with the role: `- YYYY-MM-DD HH:MM UTC — [Editor] …`.
- No more than **2 new pages or guides a day** across the team (quality over volume; Google treats
  mass-produced pages as low quality). Editor and Tech never add new pages.
- If a run cannot finish, push only the notes (LOG/BACKLOG) and stop. Never push broken work.
- End every run with a 2–3 line Roman Urdu summary for Irfan.

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
