# StudyPulse - Product analytics of a learning platform

Independent study project. Fictional student learning events - **no real user data or real business impact**.

## Why this product?

A campus learning platform wants to understand where learners stop progressing and whether they come back a week after registering. This is a portfolio project about **product metrics and data quality**, not advertising, marketplace ranking or Ozon logistics.

## Analytics questions

1. How many learners reach each stage of the learning funnel?
2. How do completion rates differ by acquisition channel?
3. What percentage of eligible learners returns during days 7-13 after enrollment?
4. How do cohort activation and weekly active users vary?
5. How should invalid and duplicate events be handled before building dashboards?

## Stack

Python, pandas, NumPy, SQLite, SQL (LEFT JOIN, CTE, conditional aggregation), matplotlib, unittest.

## Run locally

Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
python generate.py
python pipeline.py
python -m unittest discover -s tests -v
```

The pipeline generates `data/students.csv`, `data/events.csv`, `results.json`, `REPORT.md` and `figures/funnel.png`. It cleans deliberate duplicate IDs and invalid records and independently calculates D7 retention. Re-running with the same seed produces the same dataset.

## What this proves

- Reproducible ETL workflow from event CSV files to SQLite and analytical SQL.
- Product funnel, first-lesson activation, D7 retention and weekly activity metrics.
- Quality controls: deduplication, orphan users, unknown event types, datetime checks.
- Cohort right-censoring check: users who have not completed 14 days of observation are excluded from the D7 denominator.
- Clear separation between simulated behavior and real observations.

## Example results (synthetic)

- 3,000 fictional students, 18,135 generated raw events, 18,130 valid events after cleanup.
- 3 duplicate event IDs, one orphan user ID and one unknown event type filtered.
- Completion rates: University 64.30%, Referral 63.78%, Social 53.31%.
- D7 retention for fully observed cohorts: 1,239 / 2,775 = **44.65%**.

**These channel differences were deliberately generated. Do not interpret them as genuine findings about user behaviour.**

## Limitations

Data are fully synthetic and nothing here shows causal effect, authentic product improvement, actual users, or live A/B testing. The pipeline is a learning demonstration, not production-grade infrastructure. **No PySpark was used.** The project was prepared with AI assistance; review the code and methods before describing it as your own hands-on experience.
