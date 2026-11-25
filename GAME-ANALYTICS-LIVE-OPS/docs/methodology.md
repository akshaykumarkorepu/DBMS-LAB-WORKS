# Methodology and analytical decisions

## Deliverable 1

### Daily health
Daily activity is calculated from distinct `player_day.device_id` values grouped by date and platform. Purchases are deduplicated by `purchase_id` using the earliest timestamp. Gross IAP includes positive USD transactions only; negative transactions are retained separately as refunds. Revenue is assigned to the purchasing player's platform. Active payer share uses only purchasers with a same-day activity record, because the assignment asks for the share of active players who purchased that day. Positive payer-days without activity are retained in revenue but excluded from this numerator.

### Retention
Only 2026 installs are included. Pre-2026 installs have D1/D7/D14/D30 dates before the telemetry window and cannot be measured. Retention is exact-day activity, not “any activity within a window.” For a weekly cohort, a milestone is shown only when the latest install date in that cohort plus the milestone day is on or before 2026-04-30. This avoids partial-cohort denominators.

### Spender behaviour
Revenue concentration is shown for both payers only and all installed players, ranking positive gross IAP per player. The top p% population count is `floor(N × p)`. First-purchase delay percentiles exclude negative delays but report their count. Repeat-purchase gaps use `LAG()` over deduplicated positive purchases ordered by timestamp.

### Rewarded ads
Completed ads are the primary measure of rewarded-ad engagement because started and abandoned events do not grant the reward. May 1 is excluded from the Jan 1–Apr 30 window. The cap analysis checks `ad_daily_count >= ad_daily_cap` at the event level and then aggregates by player-day and cap value. A player-day can have multiple cap values; those exposures are reported transparently. Unique player-days hitting any cap are also reported without double counting.

## Deliverable 2(a): ARPDAU decomposition

The first 30 days are Jan 1–30, 2026; the last 30 days are Apr 1–30, 2026. For tier i and period t, tier ARPDAU is positive deduplicated IAP revenue divided by player-days. Overall ARPDAU is the weighted average of tier ARPDAU using each tier's share of player-days.

The symmetric interpretation used here is the Kitagawa decomposition with period-2 weights for the within-tier effect and period-1 rates for the mix effect:

- Within effect = Σ s(i,2) × [r(i,2) − r(i,1)]
- Mix effect = Σ [s(i,2) − s(i,1)] × r(i,1)

The two effects sum to the observed blended ARPDAU change. The decomposition is descriptive; it does not establish why the country-tier mix changed.

## Deliverable 3: acquisition channels

The install cohort is Jan 1–Mar 31, 2026. Every included install has a complete 30-day observation window ending by Apr 30. Outcomes are active days and positive IAP revenue during install day through day 29. OLS models use HC3 heteroskedasticity-robust standard errors. Adjusted models include country tier, platform and install week. Organic is the reference channel.

These are observational comparisons, not causal estimates. No marketing spend/CPI or ad-revenue data is supplied, so channel ROI and an optimal budget allocation cannot be calculated.

## Deliverable 4: churn model

The training snapshot is Mar 31, 2026; the test snapshot is Apr 15, 2026. Eligible players must have installed at least one day before the snapshot and have at least one active day in the preceding seven days. Churn=1 if there is no `player_day` record in the next 14 days. Features use only information available on or before the snapshot: 14-day activity, sessions, playtime, level, recency, change in sessions, prior positive purchase history, completed ads and currency-spend event count. A standardised logistic-regression pipeline is evaluated on the later snapshot using ROC-AUC, average precision, and threshold-specific precision/recall/F1.

Thresholds are operational choices. Without offer cost, save lift and retained-player value, no single threshold can be claimed economically optimal.
