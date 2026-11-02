"""Generate privacy-safe fictitious student learning events, not real usage logs."""
from __future__ import annotations
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
RNG_SEED = 2077
N_STUDENTS = 3000
START = datetime(2026, 7, 20, 9)
END = datetime(2026, 11, 1, 23, 59)
COURSES = ("Python basics", "SQL basics", "Statistics", "UX design")
CHANNELS = ("University", "Referral", "Social")
ACTIVITY = ("course_open", "lesson_start", "lesson_complete", "quiz_pass")


def generate() -> tuple[list[tuple], list[tuple]]:
    r = random.Random(RNG_SEED)
    students, events = [], []
    eid = 0

    def add_event(student_id: str, event_name: str, when: datetime) -> None:
        nonlocal eid
        if when <= END:
            eid += 1
            events.append((f"E{eid:07}", student_id, event_name, when.isoformat(timespec="seconds")))

    for i in range(N_STUDENTS):
        student = f"U{i + 1:05d}"
        cohort = r.randrange(14)
        enrolled = START + timedelta(weeks=cohort, days=r.randrange(7), hours=r.randrange(10))
        course = r.choices(COURSES, weights=(0.35, 0.30, 0.20, 0.15))[0]
        channel = r.choices(CHANNELS, weights=(0.50, 0.30, 0.20))[0]
        students.append((student, course, channel, enrolled.isoformat(timespec="seconds")))

        # An intentionally approximate funnel with varying engagement by course/channel.
        if r.random() >= 0.96:
            continue
        t0 = enrolled + timedelta(minutes=r.randint(4, 90))
        add_event(student, "course_open", t0)
        started = r.random() < (0.79 if course != "UX design" else 0.72)
        completed = started and r.random() < (0.64 if channel != "Social" else 0.52)
        passed = completed and r.random() < 0.74
        if started:
            add_event(student, "lesson_start", t0 + timedelta(minutes=10))
        if completed:
            add_event(student, "lesson_complete", t0 + timedelta(minutes=50))
        if passed:
            add_event(student, "quiz_pass", t0 + timedelta(minutes=64))
        if not started:
            continue
        for week in range(1, 8):
            ret_prob = min(0.93, 0.58 * (0.83 ** (week - 1)) * (1.27 if completed else 0.82))
            if channel == "Social":
                ret_prob *= 0.77
            if r.random() >= ret_prob:
                continue
            when = enrolled + timedelta(weeks=week, days=r.randint(0, 5), hours=r.randint(1, 8))
            add_event(student, "course_open", when)
            if r.random() < 0.75:
                add_event(student, "lesson_start", when + timedelta(minutes=10))
                if r.random() < 0.68:
                    add_event(student, "lesson_complete", when + timedelta(minutes=45))

    # Inject typical instrumentation defects to exercise the cleanup pipeline.
    events.extend([events[0], events[5], events[10]])
    events.append(("E9999991", "U99999", "course_open", START.isoformat(timespec="seconds")))
    events.append(("E9999992", "U00001", "teleport", START.isoformat(timespec="seconds")))
    return students, events


def write_csv(path: Path, cols: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(cols)
        writer.writerows(rows)


def main() -> None:
    students, events = generate()
    write_csv(BASE / "data" / "students.csv", ["student_id", "course", "channel", "enrolled_at"], students)
    write_csv(BASE / "data" / "events.csv", ["event_id", "student_id", "event_name", "occurred_at"], events)
    print(f"Generated {len(students)} fictitious students and {len(events)} raw events with seed {RNG_SEED}")


if __name__ == "__main__":
    main()
