# Personal Opportunity Hunter

A verified, de-duplicated database of **funded** opportunities (travel grants, sponsored attendance, volunteer passes, career fairs) for meeting AI engineers, founders, investors and recruiters worldwide. It covers the period from India (now) through the move to Stuttgart (March 2027).

## Files

| File | What it is | Edit? |
|---|---|---|
| `data/opportunities.json` | **Single source of truth.** One record per opportunity, with a stable `id`. | Yes, only here |
| `tools/build.py` | Validates the DB (duplicate ids/names, score ranges, expired-but-open) and regenerates the files below | Code |
| `opportunities.md` | Full human-readable database, grouped by category | Generated |
| `opportunities.csv` | Spreadsheet version (one row per record, all fields + score breakdown) | Generated |
| `deadlines.md` | Confirmed future deadlines, opening dates, and a watch list | Generated |
| `priority-opportunities.md` | Ranking by score + top-15 detail | Generated |
| `sources.md` | Official sources and research sources | Manual |
| `application-checklist.md` | Documents to prepare + per-opportunity checklist | Manual |
| `search-log.md` | Dates, keywords, sources explored, tool limitations | Manual (append) |
| `config.md` | Your profile, preferences, scoring rules, schedule design | Manual |

## How to update

1. Edit or add a record in `data/opportunities.json`. Reuse the existing `id` when updating; that prevents duplicates.
2. Update `last_verified`, `status`, and `verification` (`OFFICIAL` / `OFFICIAL-HISTORICAL` / `UNVERIFIED`).
3. Run `python3 tools/build.py --stats`. The build refuses duplicate ids or names, and refuses records marked `OPEN NOW` whose deadline has passed.
4. Append what you searched to `search-log.md`.

## Rules the database follows

- Only official organiser pages count as verification. Aggregator-only claims are marked `UNVERIFIED`.
- Past-cycle dates are labelled historical and never shown as future deadlines.
- "Fully funded" is used only when travel **and** accommodation are covered, never for a free ticket alone.
- Programmes asking for upfront fees are flagged in the *Excluded / flagged* section.
- No applications are submitted, no organisers contacted and no money spent without the owner's explicit approval.

## Verification limitation (first run, 2026-11-23)

The research environment could search the web but could **not** open full pages, because direct page fetches were blocked. Facts were confirmed through search queries restricted to each organiser's own domain, which return the official page's indexed text. Re-open each official link before you apply.
