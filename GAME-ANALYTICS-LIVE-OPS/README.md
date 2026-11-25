# DBMS Lab End-Sem — Player Telemetry Analytics

**Student:** Akshay kumar korepu  
**Roll No.:** 24MAB0A03  
**Institution:** National Institute of Technology Warangal  
**Course:** DBMS Lab  
**Instructor:** Dr. Vikas Srivastava

## Project objective

Analyse anonymised mobile-game telemetry for daily product health, retention, payer behaviour, rewarded-ad engagement, the apparent ARPDAU decline, acquisition-channel quality, and 14-day churn risk.

## Deliverables covered

1. **Deliverable 1 — SQL data exploration:** daily health by platform; exact-day weekly retention; revenue concentration; time to first purchase; repeat-purchase gaps using `LAG()`; rewarded-ad cap saturation and daily volume; data-quality notes.
2. **Deliverable 2(a) — ARPDAU deep dive:** first-30-day versus last-30-day comparison, country-tier decomposition, and business recommendation.
3. **Deliverable 3 — Acquisition channels:** 30-day active days and gross IAP LTV, unadjusted and adjusted HC3-robust OLS estimates, 95% confidence intervals, and limitations.
4. **Deliverable 4 — Churn prediction:** chronological logistic-regression model predicting no activity in the following 14 days among currently active players.
5. **Readout:** eight executive slides followed by a technical appendix.

Optional Deliverable 4(b) is not attempted because the brief explicitly prioritises a well-validated churn model over a rushed second model.

## Repository layout

```text
DBMS_Lab_EndSem_Akshay/
├── data/                  # Five canonical, normalised CSVs
├── sql/
│   ├── 00_schema.sql
│   └── deliverable_1_queries.sql
├── src/
│   └── run_analysis.py
├── outputs/
│   ├── tables/            # Query results and model outputs
│   ├── charts/            # Generated charts
│   └── analysis_summary.json
├── docs/
│   ├── initial_data_audit.md
│   ├── methodology.md
│   ├── limitations.md
│   └── source_reconstruction.md
├── presentation/
│   └── DBMS_Lab_EndSem_Akshay_24MAB0A03.pptx
├── requirements.txt
└── README.md
```

## How to run

Use Python 3.10 or later. From the project root:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python src/run_analysis.py
python src/build_presentation.py
```

The analysis script loads the five CSVs, builds a SQLite database at `outputs/dbms_lab.sqlite`, executes the Deliverable 1 SQL, runs the Python analyses for Deliverables 2–4, and regenerates the tables and charts in `outputs/`. The presentation script builds the eight-slide executive readout followed by appendices in `presentation/`.

The SQL file is SQLite 3.25+ compatible. It can be run in DB Browser for SQLite against `outputs/dbms_lab.sqlite` after the Python pipeline has loaded the tables.

## Important metric definitions

- **DAU:** distinct players with a `player_day` record on the date.
- **Gross IAP revenue:** sum of positive deduplicated `usd_amount` values. Refunds are reported separately; net IAP is gross plus negative transactions.
- **ARPDAU:** gross IAP revenue divided by player-days/DAU for the same reporting period.
- **Active payer share:** distinct positive purchasers who also have a same-day `player_day` record, divided by DAU. Purchases without same-day activity remain in revenue but not in the active-payer numerator.
- **Retention:** activity on exactly Day 1, Day 7, Day 14, or Day 30 after installation. Pre-2026 installs are excluded because their milestones predate the telemetry window. A cohort milestone is NULL unless the latest install in that cohort has a complete follow-up window by 2026-04-30.
- **30-day acquisition outcomes:** active days and positive IAP revenue during install day through install day + 29. The analysed install cohort is 2026-01-01 through 2026-03-31 so every player has a full 30-day observation window.
- **Churn label:** among players active at least once in the seven days through a snapshot date and installed at least one day before the snapshot, churn=1 if no `player_day` row exists in the subsequent 14 days.

## Data handling

The canonical profile and purchase CSVs were reconstructed from the accompanying PDF table exports because the uploaded text exports did not preserve normal CSV rows. Details and validation counts are documented in `docs/source_reconstruction.md` and `docs/initial_data_audit.md`.

The supplied data is anonymised telemetry. Do not publish the data files in a public GitHub repository unless the instructor explicitly permits redistribution. The `.gitignore` excludes the data files by default; the submission ZIP can contain them if permitted by the course instructions.
