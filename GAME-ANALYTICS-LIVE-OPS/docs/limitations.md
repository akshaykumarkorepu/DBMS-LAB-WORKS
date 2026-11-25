# Limitations and next steps

1. **No marketing cost or ad revenue:** the data cannot establish channel ROI, cost per install, total game revenue including ads, or profitability.
2. **Observational channel assignment:** adjustment for tier, platform and install week does not remove unobserved selection bias. A randomized acquisition or incrementality design would be stronger.
3. **Linked devices:** 3,211 profiles have an `original_device_id`; linked IDs all resolve, but the business meaning of these links is not defined. We do not merge histories without that definition. One self-link is present.
4. **Currency-value anomalies:** 228 events exceed 100,000, with a maximum of 75,809,670. These values are flagged rather than silently clipped. The churn model uses currency event counts, not the anomalous amount values.
5. **Ad telemetry:** Jan 1 is partial, Mar 6 has no rows, and 7,732 events fall on May 1. Missing data is not interpreted as zero demand. The ad network's financial revenue is absent.
6. **Changing ad caps:** 6,160 completed-ad player-days contain more than one cap value. The cap table uses event-level comparisons and reports cap exposure; a production data contract should define how cap changes are versioned.
7. **First-purchase date anomalies:** 110 players have first-purchase dates 1–4 days before install. They are excluded from nonnegative time-to-first-purchase percentiles but reported separately.
8. **Churn economics:** precision/recall quantify targeting quality, not incremental retention caused by an offer. A randomized holdout is required to estimate save lift. Segment-specific thresholds may be preferable because churn prevalence varies sharply with tenure.
9. **Temporal holdout overlap:** some players occur in both snapshot populations. This reflects repeated operational scoring at later dates, but the evaluation is not an independent-player holdout. A second robustness evaluation on previously unseen players is recommended if time permits.
