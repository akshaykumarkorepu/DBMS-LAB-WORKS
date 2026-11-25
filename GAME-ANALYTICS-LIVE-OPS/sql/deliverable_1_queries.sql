-- DBMS LAB END-SEM — Deliverable 1 SQL
-- Student: Akshay kumar korepu | Roll No.: 24MAB0A03
-- Course: DBMS Lab | Instructor: Dr. Vikas Srivastava
-- SQL dialect: SQLite 3.25+ (window functions required)
-- Tables are loaded from the canonical CSVs in data/.

-- ============================================================================
-- 1(a) DAILY HEALTH BY DATE AND PLATFORM
-- Gross revenue includes positive IAP transactions only. Refunds are shown
-- separately in the data-quality report. Revenue is counted even when the
-- payer has no same-day activity row. Active-payer share only counts purchasers
-- who also have a player_day row on that date.
-- ============================================================================
WITH ranked_purchase AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY purchase_id ORDER BY event_ts ASC
         ) AS rn
  FROM purchase
),
purchase_dedup AS (
  SELECT * FROM ranked_purchase WHERE rn = 1
),
activity AS (
  SELECT pd.device_id,
         date(substr(CAST(pd.activity_date AS TEXT),1,4) || '-' ||
              substr(CAST(pd.activity_date AS TEXT),5,2) || '-' ||
              substr(CAST(pd.activity_date AS TEXT),7,2)) AS dt,
         pp.platform
  FROM player_day pd
  JOIN player_profile pp ON pp.device_id = pd.device_id
),
daily_active AS (
  SELECT dt, platform, COUNT(DISTINCT device_id) AS dau
  FROM activity
  GROUP BY dt, platform
),
daily_revenue AS (
  SELECT date(p.event_ts) AS dt, pp.platform,
         SUM(CASE WHEN p.usd_amount > 0 THEN p.usd_amount ELSE 0 END) AS gross_iap_usd,
         SUM(CASE WHEN p.usd_amount < 0 THEN p.usd_amount ELSE 0 END) AS refunds_usd
  FROM purchase_dedup p
  JOIN player_profile pp ON pp.device_id = p.device_id
  GROUP BY date(p.event_ts), pp.platform
),
active_payers AS (
  SELECT DISTINCT p.device_id, date(p.event_ts) AS dt, pp.platform
  FROM purchase_dedup p
  JOIN player_day pd
    ON pd.device_id = p.device_id
   AND date(substr(CAST(pd.activity_date AS TEXT),1,4) || '-' ||
            substr(CAST(pd.activity_date AS TEXT),5,2) || '-' ||
            substr(CAST(pd.activity_date AS TEXT),7,2)) = date(p.event_ts)
  JOIN player_profile pp ON pp.device_id = p.device_id
  WHERE p.usd_amount > 0
),
daily_payer_count AS (
  SELECT dt, platform, COUNT(DISTINCT device_id) AS active_payers
  FROM active_payers
  GROUP BY dt, platform
)
SELECT da.dt, da.platform, da.dau,
       ROUND(COALESCE(dr.gross_iap_usd,0),2) AS gross_iap_usd,
       ROUND(COALESCE(dr.refunds_usd,0),2) AS refunds_usd,
       ROUND((COALESCE(dr.gross_iap_usd,0)+COALESCE(dr.refunds_usd,0)),2) AS net_iap_usd,
       ROUND(COALESCE(dr.gross_iap_usd,0)/NULLIF(da.dau,0),4) AS arpdau,
       COALESCE(pc.active_payers,0) AS active_payers,
       ROUND(100.0*COALESCE(pc.active_payers,0)/NULLIF(da.dau,0),3) AS active_payer_pct
FROM daily_active da
LEFT JOIN daily_revenue dr ON dr.dt=da.dt AND dr.platform=da.platform
LEFT JOIN daily_payer_count pc ON pc.dt=da.dt AND pc.platform=da.platform
ORDER BY da.dt, da.platform;


-- ============================================================================
-- 1(b) WEEKLY INSTALL COHORT RETENTION (EXACT DAY 1, 7, 14, 30)
-- Pre-2026 installs are excluded because their milestones predate telemetry.
-- A milestone is reported only if the latest install in that cohort has had
-- the full follow-up window by 2026-04-30; otherwise the cell is NULL.
-- ============================================================================
WITH profile_2026 AS (
  SELECT device_id, date(install_date) AS install_date,
         date(install_date,
              '-' || ((CAST(strftime('%w',install_date) AS INTEGER)+6)%7) || ' days') AS install_week
  FROM player_profile
  WHERE date(install_date) >= '2026-01-01'
    AND date(install_date) <= '2026-04-30'
),
cohort_bounds AS (
  SELECT install_week, COUNT(*) AS cohort_size,
         MAX(install_date) AS latest_install
  FROM profile_2026
  GROUP BY install_week
),
player_flags AS (
  SELECT p.install_week, p.device_id, p.install_date,
         cb.cohort_size, cb.latest_install,
         a1.device_id AS d1_active,
         a7.device_id AS d7_active,
         a14.device_id AS d14_active,
         a30.device_id AS d30_active
  FROM profile_2026 p
  JOIN cohort_bounds cb ON cb.install_week=p.install_week
  LEFT JOIN player_day a1
    ON a1.device_id=p.device_id
   AND a1.activity_date=CAST(strftime('%Y%m%d',date(p.install_date,'+1 day')) AS INTEGER)
  LEFT JOIN player_day a7
    ON a7.device_id=p.device_id
   AND a7.activity_date=CAST(strftime('%Y%m%d',date(p.install_date,'+7 day')) AS INTEGER)
  LEFT JOIN player_day a14
    ON a14.device_id=p.device_id
   AND a14.activity_date=CAST(strftime('%Y%m%d',date(p.install_date,'+14 day')) AS INTEGER)
  LEFT JOIN player_day a30
    ON a30.device_id=p.device_id
   AND a30.activity_date=CAST(strftime('%Y%m%d',date(p.install_date,'+30 day')) AS INTEGER)
)
SELECT install_week, cohort_size,
  CASE WHEN date(latest_install,'+1 day') <= '2026-04-30'
       THEN ROUND(100.0*SUM(CASE WHEN d1_active IS NOT NULL THEN 1 ELSE 0 END)/cohort_size,2) END AS d1_pct,
  CASE WHEN date(latest_install,'+7 day') <= '2026-04-30'
       THEN ROUND(100.0*SUM(CASE WHEN d7_active IS NOT NULL THEN 1 ELSE 0 END)/cohort_size,2) END AS d7_pct,
  CASE WHEN date(latest_install,'+14 day') <= '2026-04-30'
       THEN ROUND(100.0*SUM(CASE WHEN d14_active IS NOT NULL THEN 1 ELSE 0 END)/cohort_size,2) END AS d14_pct,
  CASE WHEN date(latest_install,'+30 day') <= '2026-04-30'
       THEN ROUND(100.0*SUM(CASE WHEN d30_active IS NOT NULL THEN 1 ELSE 0 END)/cohort_size,2) END AS d30_pct
FROM player_flags
GROUP BY install_week, cohort_size, latest_install
ORDER BY install_week;

-- ============================================================================
-- 1(c)(i) REVENUE CONCENTRATION — PAYERS ONLY AND ALL PLAYERS
-- Top percentages use FLOOR(population * percentage) ranked players.
-- Revenue is positive gross IAP per player; refund sensitivity is documented.
-- ============================================================================
WITH ranked_purchase AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY purchase_id ORDER BY event_ts) AS rn
  FROM purchase
),
purchase_dedup AS (SELECT * FROM ranked_purchase WHERE rn=1),
player_revenue AS (
  SELECT device_id, SUM(usd_amount) AS revenue
  FROM purchase_dedup
  WHERE usd_amount > 0
  GROUP BY device_id
),
populations AS (
  SELECT 'payers_only' AS population, device_id, revenue FROM player_revenue
  UNION ALL
  SELECT 'all_players' AS population, pp.device_id, COALESCE(pr.revenue,0) AS revenue
  FROM player_profile pp LEFT JOIN player_revenue pr ON pr.device_id=pp.device_id
),
ranked AS (
  SELECT population, device_id, revenue,
         ROW_NUMBER() OVER (PARTITION BY population ORDER BY revenue DESC, device_id) AS rn,
         COUNT(*) OVER (PARTITION BY population) AS n
  FROM populations
)
SELECT population,
       ROUND(100.0*SUM(CASE WHEN rn <= CAST(n*0.01 AS INTEGER) THEN revenue ELSE 0 END)/SUM(revenue),2) AS top_1_pct_revenue_share,
       ROUND(100.0*SUM(CASE WHEN rn <= CAST(n*0.10 AS INTEGER) THEN revenue ELSE 0 END)/SUM(revenue),2) AS top_10_pct_revenue_share,
       ROUND(100.0*SUM(CASE WHEN rn <= CAST(n*0.50 AS INTEGER) THEN revenue ELSE 0 END)/SUM(revenue),2) AS top_50_pct_revenue_share
FROM ranked
GROUP BY population;


-- ============================================================================
-- 1(c)(ii) TIME TO FIRST PURCHASE — PLAYER-LEVEL ROWS FOR DISTRIBUTION
-- Negative delays are retained in this extract for audit; exclude them from
-- nonnegative delay percentiles and report them separately.
-- ============================================================================
WITH ranked_purchase AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY purchase_id ORDER BY event_ts) AS rn
  FROM purchase
),
purchase_dedup AS (SELECT * FROM ranked_purchase WHERE rn=1),
first_purchase AS (
  SELECT device_id, date(MIN(event_ts)) AS first_purchase_date
  FROM purchase_dedup
  WHERE usd_amount > 0
  GROUP BY device_id
)
SELECT pp.device_id, date(pp.install_date) AS install_date,
       fp.first_purchase_date,
       julianday(fp.first_purchase_date)-julianday(date(pp.install_date)) AS days_to_first_purchase
FROM player_profile pp
LEFT JOIN first_purchase fp ON fp.device_id=pp.device_id;


-- ============================================================================
-- 1(c)(iii) REPEAT PURCHASE GAP — WINDOW FUNCTION (LAG)
-- One row per consecutive positive purchase pair, in days.
-- ============================================================================
WITH ranked_purchase AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY purchase_id ORDER BY event_ts) AS rn
  FROM purchase
),
purchase_dedup AS (SELECT * FROM ranked_purchase WHERE rn=1),
ordered AS (
  SELECT device_id, purchase_id, event_ts,
         LAG(event_ts) OVER (PARTITION BY device_id ORDER BY event_ts, purchase_id) AS previous_purchase_ts
  FROM purchase_dedup
  WHERE usd_amount > 0
)
SELECT device_id, purchase_id, previous_purchase_ts, event_ts,
       (julianday(event_ts)-julianday(previous_purchase_ts)) AS gap_days
FROM ordered
WHERE previous_purchase_ts IS NOT NULL
ORDER BY device_id, event_ts;


-- ============================================================================
-- 1(d)(i) REWARDED AD CAP — EVENT-LEVEL HIT, COMPLETED EVENTS ONLY
-- Player-days can have more than one cap value. This query reports each
-- (player, date, cap) exposure separately and avoids assigning a changed-cap
-- day solely to MAX(cap). Some player-days can therefore appear under two caps.
-- ============================================================================
WITH completed AS (
  SELECT device_id, date(event_ts) AS ad_date, ad_daily_cap, ad_daily_count
  FROM ad_view
  WHERE status='completed'
    AND date(event_ts) BETWEEN '2026-01-01' AND '2026-04-30'
),
player_day_cap AS (
  SELECT device_id, ad_date, ad_daily_cap,
         MAX(ad_daily_count) AS max_count,
         MAX(CASE WHEN ad_daily_count >= ad_daily_cap THEN 1 ELSE 0 END) AS hit_cap
  FROM completed
  GROUP BY device_id, ad_date, ad_daily_cap
)
SELECT ad_daily_cap,
       COUNT(*) AS player_days_exposed_to_cap,
       SUM(hit_cap) AS player_days_hitting_cap,
       ROUND(100.0*SUM(hit_cap)/COUNT(*),3) AS cap_hit_pct
FROM player_day_cap
GROUP BY ad_daily_cap
ORDER BY ad_daily_cap;


-- Unique completed-ad player-days hitting any cap (not double-counted).
WITH completed AS (
  SELECT device_id, date(event_ts) AS ad_date, ad_daily_cap, ad_daily_count
  FROM ad_view
  WHERE status='completed'
    AND date(event_ts) BETWEEN '2026-01-01' AND '2026-04-30'
),
player_day AS (
  SELECT device_id, ad_date,
         MAX(CASE WHEN ad_daily_count >= ad_daily_cap THEN 1 ELSE 0 END) AS hit_cap
  FROM completed
  GROUP BY device_id, ad_date
)
SELECT COUNT(*) AS completed_ad_player_days,
       SUM(hit_cap) AS unique_player_days_hitting_any_cap,
       ROUND(100.0*SUM(hit_cap)/COUNT(*),3) AS any_cap_hit_pct
FROM player_day;


-- ============================================================================
-- 1(d)(ii) DAILY AD EVENT VOLUME — ZERO-FILL MISSING DATES
-- March 6 appears as 0 rows, not as a zero-demand observation.
-- ============================================================================
WITH RECURSIVE calendar(dt) AS (
  SELECT date('2026-01-01')
  UNION ALL
  SELECT date(dt,'+1 day') FROM calendar WHERE dt<'2026-04-30'
),
daily AS (
  SELECT date(event_ts) AS dt,
         COUNT(*) AS total_ad_events,
         SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_ads,
         SUM(CASE WHEN status='started' THEN 1 ELSE 0 END) AS started_ads,
         SUM(CASE WHEN status='abandoned' THEN 1 ELSE 0 END) AS abandoned_ads
  FROM ad_view
  WHERE date(event_ts) BETWEEN '2026-01-01' AND '2026-04-30'
  GROUP BY date(event_ts)
)
SELECT c.dt,
       COALESCE(d.total_ad_events,0) AS total_ad_events,
       COALESCE(d.completed_ads,0) AS completed_ads,
       COALESCE(d.started_ads,0) AS started_ads,
       COALESCE(d.abandoned_ads,0) AS abandoned_ads
FROM calendar c
LEFT JOIN daily d ON d.dt=c.dt
ORDER BY c.dt;
