# Van Board — Shared Feeder Van Board for Rural Commuters

A lightweight, mobile-first public board where riders and drivers log, view,
and confirm today's shared van/auto departures between villages and market
towns — no login, no phone verification, zero paid dependencies.

**Try it:** open `index.html` directly in a browser — it works immediately
with no setup (see "Two storage modes" below). For a real multi-device
public board, see `DEPLOY.md`.

## How it works

- **Board** (`index.html` main view): today's trips, grouped by route,
  sorted by departure time. Upcoming trips appear first; departed ones are
  dimmed below a "── Departed ──" divider. Filter chips narrow to one route.
- **Next van banner**: each route shows a prominent "Next: 7:45 AM from
  Water Tank Circle (in 23 min)" banner so riders get their answer at a glance.
- **Log a van**: a bottom sheet with route, a *search-and-pick* landmark
  selector (no free text for stop names), time, and optional vehicle number.
- **Confirm toggle**: any visitor can tap "Confirm running" once per trip per
  device to bump a lightweight trust counter.
- **Report wrong info**: a subtle "⚑ Report" link per card lets riders flag
  inaccurate listings; trips with ≥3 reports are visually flagged.
- **Deep links**: share `?route=kondapur-siddipet` via WhatsApp to link
  directly to a specific route's board.

## Two storage modes (`db.js`)

The app runs on **localStorage** the instant you open it — good enough to
demo or to pilot with a single kiosk phone at a stop. Fill in `config.js`
with a free Firebase (Firestore, Spark/free tier) project and the app
automatically switches to a **shared, realtime backend** with no code
changes — see `DEPLOY.md`. Both paths are $0.

## Project structure

```
index.html      structure
style.css       mobile-first styling (route-sign inspired palette)
app.js          board rendering + form + dialogs
db.js           storage abstraction (local + Firestore) and anti-spam checks
landmarks.js    canonical stops/routes + nickname aliases — edit this to
                launch the board for a different cluster of villages
config.js       Firebase project config (empty = local mode)
DEPLOY.md       how to publish for free (GitHub Pages + Firebase)
```

## Duplicate handling & data trust (under 300 words)

**Duplicates.** A new listing is checked against today's trips on the same
route and landmark within a **±20 minute window**. If one exists, the
submitter sees the existing van's time and vehicle number and chooses "same
van" (which bumps the existing listing's confirm count instead of creating
a row) or "different van" (a genuinely separate trip, e.g. a second van
running close behind). This catches the common case — three people
independently logging the 7 AM van — without ever silently blocking a post,
since only the submitter, who has local context, can tell them apart.

**Trust without accounts.** Since there's no login, trust is built from
*volume of independent confirmations*, not identity. Three device-local
safeguards keep that signal meaningful: each browser/phone can confirm a
given trip only once (stored in `localStorage`), each device can log at most
5 new trips per hour, and each device can report a trip only once. None of
these stop a determined bad actor with two phones, but they stop the
accidental double-counting and casual spam that would otherwise dominate a
small, well-meaning user base — the realistic threat model for a
village-level board.

**Community flagging.** A "Report" button lets riders flag listings with
wrong times or fake trips. At ≥3 reports from different devices, the card is
visually flagged ("⚠ Flagged by riders") so other riders know to treat it
with caution. This provides lightweight moderation without requiring admin
accounts or identity verification.

**Trade-off accepted.** The landmark picker (fixed list, not free text)
trades a small amount of flexibility — a genuinely new stop needs a code
edit to `landmarks.js` — for eliminating the spelling/nickname chaos the
brief describes. Given the low rate of new junctions appearing versus the
daily cost of unmatched spellings, this favored consistency over flexibility.
