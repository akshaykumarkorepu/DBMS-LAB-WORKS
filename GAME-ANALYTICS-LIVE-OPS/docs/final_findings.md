# Final analytical findings

## Executive conclusion

The blended ARPDAU decline is explained by a substantial shift in active player-days toward lower-ARPDAU country Tier 4, not by deterioration within any individual tier. Acquisition-channel differences in 30-day IAP LTV become small and statistically unresolved after adjustment for observed player mix. A logistic-regression model identifies elevated 14-day churn risk, but the deployment threshold must be tested against offer economics and incremental save lift.

## Deliverable 1

- DAU rises from 1,789 on Jan 1 to 11,097 on Apr 30 (6.20×). Jan 1 is a partial day in ad telemetry; DAU itself is available from player_day.
- Mean daily ARPDAU: Android $0.2567; iOS $0.4998. Mean daily active-payer share: Android 1.47%; iOS 2.85%.
- Weekly cohort retention averages across mature cohort cells: D1 47.61% (17 cohorts), D7 25.50% (16), D14 19.55% (15), D30 13.92% (13). Cohort cells are omitted until the entire cohort has full milestone follow-up.
- 86.23% of profiles have no positive IAP purchase. Among payers, top 1%, 10%, and 50% account for 9.16%, 47.62%, and 89.94% of positive gross IAP revenue. For all profiles, the corresponding shares are 39.94%, 96.66%, and 100.00%.
- Median time to first purchase is 22 days across all valid payer delays and 13 days for 2026 installs. 110 negative delays (1–4 days before install) are disclosed and excluded from delay percentiles.
- Repeat-purchase gap: 2,476 repeat payers, 4,024 consecutive-purchase gaps; median 15.26 days, mean 22.71 days.
- Completed rewarded-ad player-days: 396,825. Event-level cap hit rate is 0.789% across unique player-days; cap-5 exposure hit rate 1.036%, cap-8 exposure hit rate 0.013%. Cap can vary within a player-day, so cap-specific exposure counts can overlap.

## Deliverable 2(a): ARPDAU

- First 30 days ARPDAU: $0.3543; last 30 days: $0.2958; change: −16.51%.
- Tier 1: $0.5186 → $0.5557 (+7.1%).
- Tier 2: $0.3735 → $0.4031 (+7.9%).
- Tier 3: $0.2336 → $0.2607 (+11.6%).
- Tier 4: $0.1543 → $0.1577 (+2.2%).
- Tier 4 share of active player-days: 17.65% → 45.99% (+28.33 percentage points).
- Kitagawa decomposition: within-tier effect +$0.0186; mix effect −$0.0771; net −$0.0585.

**Recommendation:** do not treat the blended decline as evidence that monetisation weakened within tiers. Investigate why the active mix shifted toward Tier 4 and evaluate tier-aware onboarding/monetisation strategies. The telemetry does not reveal whether the mix shift was caused by campaign targeting, market expansion, or another factor.

## Deliverable 3: acquisition channels

30-day cohort: 37,489 installs from Jan 1 to Mar 31, 2026. Mean 30-day active days / gross IAP LTV:

- Organic: 7.07 days / $2.46; payer share 13.31%.
- Paid social: 6.86 days / $2.22; payer share 13.15%.
- Paid video: 6.82 days / $1.54; payer share 8.86%.

HC3-robust OLS adjusted for country tier, platform and install week:

- Paid social vs organic 30-day LTV: −$0.248; 95% CI [−$0.523, +$0.027]; p=0.077.
- Paid video vs organic 30-day LTV: −$0.141; 95% CI [−$0.446, +$0.164]; p=0.366.
- Paid social vs organic active days: −0.212; 95% CI [−0.286, −0.137]; p<0.001.
- Paid video vs organic active days: −0.295; 95% CI [−0.378, −0.213]; p<0.001.

**Recommendation:** do not reallocate budget on the basis of these telemetry-only LTV comparisons. The paid-video LTV gap largely disappears after observed-mix adjustment; active-day differences are statistically detectable but small. CPI, ad revenue and campaign costs are absent, and channel assignment is observational.

## Deliverable 4: churn prediction

- Training snapshot Mar 31: 29,921 eligible players; churn prevalence 19.88%.
- Test snapshot Apr 15: 37,455 eligible players; churn prevalence 19.15%.
- Test ROC-AUC 0.757; average precision / PR-AUC 0.420 versus 0.191 prevalence baseline.
- Threshold 0.35: 6,443 targeted; precision 44.2%; recall 39.7%.
- Threshold 0.45: 2,653 targeted; precision 53.1%; recall 19.7%.
- Threshold 0.55: 742 targeted; precision 62.9%; recall 6.5%.
- At threshold 0.50, the model targets no players in the 1–7 or 8–30 day tenure groups. Test churn prevalence rises from 4.8% in days 1–7 to 36.7% at 90+ days.

**Recommendation:** treat 0.35 and 0.55 as candidate operating points for low-cost and high-cost interventions respectively, not proven optimal thresholds. Calibrate by tenure and use randomized holdouts to estimate incremental save lift. The same player can appear in both chronological snapshots; this reflects repeated scoring but is not an independent-player holdout.
