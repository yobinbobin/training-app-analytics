"""Small CSV -> validation -> SQLite -> SQL report -> figure ETL/analytics pipeline."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ALLOWED = {"course_open", "lesson_start", "lesson_complete", "quiz_pass"}
AS_OF = pd.Timestamp("2026-11-01 23:59:59")


def read_clean():
    students = pd.read_csv(DATA / "students.csv", parse_dates=["enrolled_at"])
    raw = pd.read_csv(DATA / "events.csv", parse_dates=["occurred_at"])
    duplicates = int(raw.duplicated("event_id").sum())
    events = raw.drop_duplicates("event_id").copy()
    bad_user = int((~events.student_id.isin(students.student_id)).sum())
    bad_name = int((~events.event_name.isin(ALLOWED)).sum())
    events = events.loc[events.student_id.isin(students.student_id) & events.event_name.isin(ALLOWED)].copy()
    events = events.merge(students[["student_id", "enrolled_at"]], on="student_id", validate="many_to_one")
    before_signup = int((events.occurred_at < events.enrolled_at).sum())
    events = events.loc[(events.occurred_at >= events.enrolled_at) & (events.occurred_at <= AS_OF)]
    events = events.drop(columns=["enrolled_at"])
    return students, events, {"raw_events": len(raw), "duplicate_event_ids": duplicates, "orphan_student_ids": bad_user, "unknown_event_names": bad_name, "before_signup": before_signup, "valid_events": len(events)}


def metrics():
    students, events, qc = read_clean()
    assert students.student_id.is_unique
    assert events.event_id.is_unique
    db = sqlite3.connect(":memory:")
    students.assign(enrolled_at=students.enrolled_at.dt.strftime("%Y-%m-%d %H:%M:%S")).to_sql("students", db, index=False)
    events.assign(occurred_at=events.occurred_at.dt.strftime("%Y-%m-%d %H:%M:%S")).to_sql("events", db, index=False)
    sql = (ROOT / "sql" / "metrics.sql").read_text(encoding="utf-8")
    statements = [q.strip() for q in sql.split(";") if q.strip()]
    funnel = pd.read_sql_query(statements[0], db)
    cohorts = pd.read_sql_query(statements[1], db)
    weekly = pd.read_sql_query(statements[2], db)
    assert int(funnel["enrolled"].sum()) == len(students)
    assert np.all(np.diff(funnel[["enrolled", "opened", "started", "completed", "passed"]].to_numpy(), axis=1) <= 0)

    # Independent pandas check for D7 retention among fully observed cohorts.
    new = students.assign(as_of_age=(AS_OF - students.enrolled_at).dt.total_seconds() / 86400)
    eligible = new.loc[new.as_of_age >= 14].copy()
    t = events.merge(eligible[["student_id", "enrolled_at"]], on="student_id")
    days = (t.occurred_at - t.enrolled_at).dt.total_seconds() / 86400
    d7_returners = int(t.loc[(days >= 7) & (days < 14), "student_id"].nunique())
    d7_retention = d7_returners / len(eligible)
    d7_label = round(100 * d7_retention, 2)

    summary = {"dataset": "synthetic", "as_of": str(AS_OF), "students": int(len(students)),
               "quality": qc, "funnel": funnel.to_dict(orient="records"),
               "eligible_d7": int(len(eligible)), "returners_d7": d7_returners,
               "d7_retention_pct": d7_label,
               "cohorts": cohorts.to_dict(orient="records"), "weekly": weekly.to_dict(orient="records")}
    (ROOT / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "REPORT.md").open("w", encoding="utf-8") as out:
        out.write("# StudyPulse - результаты на синтетических данных\n\n")
        out.write(f"Сгенерировано **{len(students)}** студентов; после очистки осталось **{len(events)}** событий. ")
        out.write(f"Исправлено {qc['duplicate_event_ids']} дубля, исключено {qc['orphan_student_ids']} события с неизвестным студентом и {qc['unknown_event_names']} событие с неизвестным типом.\n\n")
        out.write("## Воронка по каналам\n\n")
        out.write("| Канал | Студенты | Открыли курс | Начали урок | Завершили урок | Сдали тест | Доля завершений |\n|---|---:|---:|---:|---:|---:|---:|\n")
        for x in funnel.to_dict(orient="records"):
            out.write(f"| {x['channel']} | {x['enrolled']} | {x['opened']} | {x['started']} | {x['completed']} | {x['passed']} | {x['completion_pct']}% |\n")
        out.write(f"\n## D7 удержание\n\nВернулись в дни [7,14) после регистрации: **{d7_returners}/{len(eligible)} = {d7_label}%**. ")
        out.write("Студенты без 14 полных дней наблюдения исключены, чтобы не занижать метрику.\n\n")
        out.write("## Интерпретация\n\nСегментные различия в метриках заданы генератором данных. ")
        out.write("Их нельзя интерпретировать как реальные проблемы или причинные эффекты. ")
        out.write("Для реального продукта следующий шаг - проверить инструментирование событий, построить когорты, ")
        out.write("провести интервью с пользователями и сформулировать дизайн эксперимента.\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        stage = ["enrolled", "opened", "started", "completed", "passed"]
        fig, ax = plt.subplots(figsize=(8.6, 4.4))
        xx = np.arange(len(stage))
        for _, row in funnel.iterrows():
            vals = [100 * row[s] / row["enrolled"] for s in stage]
            ax.plot(xx, vals, marker="o", label=row["channel"])
        ax.set_xticks(xx, ["Sign-up", "Course open", "Lesson start", "Lesson finish", "Quiz pass"])
        ax.set_ylim(0, 105)
        ax.set_ylabel("% of enrolled")
        ax.set_title("StudyPulse: synthetic learning funnel")
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        (ROOT / "figures").mkdir(exist_ok=True)
        fig.savefig(ROOT / "figures" / "funnel.png", dpi=175)
        plt.close(fig)
    except ImportError:
        print("matplotlib not installed; skipped chart")
    db.close()
    print(f"Cleaned {qc['raw_events']} -> {qc['valid_events']} events; D7 = {d7_label}%")
    return summary


if __name__ == "__main__":
    metrics()
