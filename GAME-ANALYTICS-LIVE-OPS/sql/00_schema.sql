-- SQLite schema for DBMS Lab End-Sem
CREATE TABLE IF NOT EXISTS player_profile (
  device_id TEXT PRIMARY KEY,
  original_device_id TEXT,
  install_date TEXT NOT NULL,
  platform TEXT,
  country TEXT,
  country_tier INTEGER,
  acquisition_channel TEXT,
  first_purchase_date TEXT
);
CREATE TABLE IF NOT EXISTS player_day (
  device_id TEXT NOT NULL,
  activity_date INTEGER NOT NULL,
  player_level INTEGER,
  session_count INTEGER,
  playtime_minutes REAL,
  app_version TEXT
);
CREATE TABLE IF NOT EXISTS purchase (
  purchase_id TEXT NOT NULL,
  device_id TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  pack_name TEXT,
  usd_amount REAL,
  currency_granted INTEGER,
  sale_flag INTEGER
);
CREATE TABLE IF NOT EXISTS currency_spend (
  device_id TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  spend_type TEXT,
  currency_type TEXT,
  currency_value INTEGER,
  spend_category TEXT,
  player_level INTEGER,
  premium_balance INTEGER,
  social_balance INTEGER,
  grind_balance INTEGER
);
CREATE TABLE IF NOT EXISTS ad_view (
  device_id TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  status TEXT,
  placement TEXT,
  reward_type TEXT,
  reward_amount INTEGER,
  ad_daily_count INTEGER,
  ad_daily_cap INTEGER
);
CREATE INDEX IF NOT EXISTS idx_player_day_date_device ON player_day(activity_date, device_id);
CREATE INDEX IF NOT EXISTS idx_purchase_ts_device ON purchase(event_ts, device_id);
CREATE INDEX IF NOT EXISTS idx_currency_ts_device ON currency_spend(event_ts, device_id);
CREATE INDEX IF NOT EXISTS idx_ad_ts_device ON ad_view(event_ts, device_id);

CREATE INDEX IF NOT EXISTS idx_player_day_device_date ON player_day(device_id, activity_date);
