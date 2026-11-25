# Submission manifest

**Student:** Akshay kumar korepu  
**Roll No.:** 24MAB0A03  
**Course:** DBMS Lab  
**Instructor:** Dr. Vikas Srivastava

## Main deliverable

- `presentation/DBMS_Lab_EndSem_Akshay_24MAB0A03.pptx`
  - Slides 1–8: Product Director executive readout (within the eight-slide limit).
  - Slides 9–14: Technical appendix for data quality, SQL outputs, spender/ad analysis, ARPDAU, acquisition and churn.

## Working files

- `sql/00_schema.sql` and `sql/deliverable_1_queries.sql`
- `src/run_analysis.py` and `src/build_presentation.py`
- Five canonical CSVs in `data/`
- Generated result tables and charts in `outputs/`
- README, requirements and methodology/limitations documentation

## Reproduction

```bash
pip install -r requirements.txt
python src/run_analysis.py
python src/build_presentation.py
```

The SQLite database is regenerated at `outputs/dbms_lab.sqlite` when the analysis pipeline runs. It is omitted from this ZIP because it is a generated cache; the five CSV inputs and scripts are included.

## GitHub privacy note

The `.gitignore` excludes the supplied CSV data by default. Do not publish the anonymised course datasets in a public repository unless the instructor explicitly permits redistribution. The submission ZIP contains the canonical datasets so the project can be reproduced locally.
