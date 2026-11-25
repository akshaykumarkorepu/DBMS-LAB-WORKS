# DBMS Lab End-Sem — Initial Data Audit

**Student:** Akshay kumar korepu  
**Roll No.:** 24MAB0A03  
**Institution:** National Institute of Technology Warangal  
**Course:** DBMS Lab  
**Instructor:** Dr. Vikas Srivastava

## 1. Dataset inventory

| Dataset | Rows | Unique players / IDs |
|---|---:|---:|
| player_profile | 80,295 | 80,295 |
| player_day | 667,435 | 79,181 |
| purchase (raw) | 15,426 | 11,054 |
| currency_spend | 489,892 | 73,216 |
| ad_view | 647,623 | 74,042 |

Total source rows: **1,900,671**.

## 2. Source reconstruction

The uploaded `player_profile.csv` and `purchase.csv` were not conventional comma-separated tables. The profile export had fixed-width text and omitted fields in the flattened representation. The purchase export split transaction records over two lines and placed `sale_flag` in separate page blocks.

To avoid misaligned columns, the canonical `data/player_profile.csv` and `data/purchase.csv` were reconstructed from the accompanying source PDFs using page coordinates and row alignment. The reconstructed counts are 80,295 profiles and 15,426 purchase rows before deduplication. The profile page-pair extraction recovered all eight fields in the assignment data dictionary; purchase page-pair extraction recovered all seven purchase fields including sale flags.

The other three datasets were read from their comma-separated CSV exports. The canonical files in `data/` are the inputs for the analysis scripts.

## 3. Key quality checks

### Player profile
- 80,295 rows and 80,295 unique `device_id` values.
- 3,211 populated `original_device_id` links; all linked IDs resolve to a profile record.
- One self-reference exists in the linked-device field and should be documented rather than silently merged.
- Install dates range from 2025-05-27 to 2026-04-30.
- 64,295 players installed during the 2026 telemetry window.
- Acquisition channels: organic 24,554; paid_social 21,705; paid_video 34,036.
- 110 players have a recorded first-purchase date 1–4 days before installation. The profile first-purchase date agrees with the earliest purchase event, so this is a source-level date inconsistency.

### Player-day
- 667,435 rows; 79,181 unique players.
- Activity dates range from 2026-01-01 to 2026-04-30.
- No duplicate `(device_id, activity_date)` pairs were found.
- 45 rows have zero playtime; no negative playtime or session counts were found.
- No activity record predates the player's installation date.
- Total DAU rises from 1,789 on Jan 1 to 11,097 on Apr 30 (6.20x).

### Purchase
- 15,426 raw rows and 15,304 distinct transaction IDs.
- 122 duplicate transaction rows; duplicated IDs agree on device, pack, amount, currency grant and sale flag. Their timestamps differ. The canonical rule is to retain the earliest timestamp per `purchase_id`.
- Deduplicated gross positive purchase revenue: **$217,593.22**.
- Deduplicated negative transactions: **$-3,249.74** across 226 rows.
- Deduplicated net purchase revenue: **$214,343.48**.
- The raw negative total is $-3,274.72; two negative duplicate rows account for the difference from the deduplicated refund total.
- 2,429 positive payer-days have no matching player-day activity row. Revenue remains in revenue totals; these rows are excluded from the numerator for the metric “share of active players who purchased that day”.

### Currency spend
- 489,892 rows; 73,216 unique players.
- 110 repeated `(device_id, event_ts)` pairs. These are not deleted without evidence that they are duplicate events.
- 228 `currency_value` observations exceed 100,000; the maximum is 75,809,670, while the median is 155. These values are suspicious and should be flagged for sensitivity analysis, not silently clipped or removed.
- No negative currency values were found.

### Rewarded ads
- 647,623 raw rows; 74,042 unique players.
- Statuses: completed 531,074; abandoned 84,420; started 32,129.
- 7,732 rows fall on May 1, outside the Jan 1–Apr 30 analysis window.
- No rows exist on March 6; this is a likely logging/mediation outage and must be shown as missing telemetry, not zero demand.
- Jan 1 is partial: first observed event is 14:00:20.
- For completed-ad player-days within Jan 1–Apr 30, there are 396,825 player-days. A first-pass event-level cap check finds 3,131 unique player-days with at least one completed event where `ad_daily_count >= ad_daily_cap`. Cap values change within 6,160 player-days, so the final cap table will explicitly state how those days are classified.

## 4. Initial analytical checks

### Daily health
- Mean daily DAU: Android 3,821.5; iOS 1,740.5.
- Mean daily gross revenue: Android $942.57; iOS $870.71.
- Mean daily ARPDAU: Android $0.2567; iOS $0.4998.
- The active-payer numerator must be matched to `player_day` on `(device_id, date)`. Counting all purchasers on a date overstates the requested active-payer share because of the 2,429 off-session payer-days.

### Retention
- Retention is calculated for installs in 2026 only because pre-2026 Day-1/7/14/30 milestones precede the available activity telemetry.
- A weekly cohort milestone is shown only when the latest installation date in that cohort has had the full milestone follow-up by 2026-04-30. Otherwise the cell is NULL, rather than a partial-cohort estimate or zero.

### ARPDAU deep dive
Using positive deduplicated IAP revenue and player-days as the denominator:
- First 30 days blended ARPDAU: $0.3543.
- Last 30 days blended ARPDAU: $0.2958.
- Change: -16.51%.
- Within-tier effect: $+0.0186; tier-mix effect: $-0.0771.
- Tier 4 active-player-day share changes from 17.7% to 46.0%.

## 5. Decisions still requiring validation in the full analysis

1. Confirm the operational meaning of linked-device IDs before merging player histories.
2. Keep gross positive IAP, refunds and net IAP separately labelled.
3. Distinguish all purchasers from active purchasers in daily payer share.
4. Define rewarded-ad cap saturation at the event level and disclose days with changing cap values.
5. Treat extreme currency values as suspicious; do not let them silently drive spending summaries.
6. Acquisition-channel comparisons are observational; no CPI or ad-revenue data is supplied, so channel ROI cannot be calculated.
7. Churn modelling uses a chronological snapshot split and a 14-day no-activity label; offer economics require assumptions not present in the telemetry.
