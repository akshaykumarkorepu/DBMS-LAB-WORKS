# Source file reconstruction notes

## Why reconstruction was required

The supplied `player_profile.csv` and `purchase.csv` did not parse as ordinary comma-separated files: each imported as a single text column. Their accompanying PDFs contained the tabular source data, but the PDF text layer represented some columns on separate pages.

## Player profile

- Source: `player_profile.pdf` (3,492 pages).
- The PDF uses paired pages: the first page in a pair contains `device_id`, `original_device_id`, `install_date`, `platform`, `country`, and `country_tier`; the following page contains `acquisition_channel` and `first_purchase_date` for the same rows.
- The two pages were aligned by row position and PDF text coordinates.
- Reconstructed output: 80,295 rows, 8 columns, 80,295 distinct `device_id` values.

## Purchase

- Source: `purchase.pdf` (672 pages).
- The PDF uses paired pages: a transaction-detail page followed by a `sale_flag` page. Transaction detail includes `purchase_id`, `device_id`, timestamp, pack, USD amount, and currency grant.
- `sale_flag` values were aligned to transactions in page order.
- Reconstructed raw output: 15,426 rows and 15,304 distinct transaction IDs.

## Validation

- All player-day, purchase, currency-spend and ad-view `device_id` values resolve to `player_profile`.
- The reconstructed profile's `first_purchase_date` matches the calendar date of the earliest positive purchase for every payer. There are 110 players whose first-purchase date is 1–4 days before their install date; this is treated as a source-level date anomaly, not corrected silently.
- Duplicate transaction IDs agree on player, pack, USD amount, currency grant and sale flag. They differ in event timestamp. The analytical deduplication rule is earliest timestamp per `purchase_id`.

The original PDF sources are not required to run the pipeline after the canonical CSVs have been created.
