"""Unit and integration checks run with python -m unittest discover -s tests -v."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generate import generate, N_STUDENTS
from pipeline import read_clean, metrics


class StudyPulseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from generate import main
        main()

    def test_student_count(self):
        students, _ = generate()
        self.assertEqual(len(students), N_STUDENTS)

    def test_reproducibility(self):
        a, x = generate()
        b, y = generate()
        self.assertEqual(a, b)
        self.assertEqual(x, y)

    def test_deduplicate_events(self):
        _, events, qc = read_clean()
        self.assertEqual(qc['duplicate_event_ids'], 3)
        self.assertTrue(events.event_id.is_unique)

    def test_orphans_and_unknown(self):
        _, events, qc = read_clean()
        self.assertEqual(qc['orphan_student_ids'], 1)
        self.assertEqual(qc['unknown_event_names'], 1)
        self.assertNotIn('teleport', events.event_name.unique())

    def test_report_valid(self):
        result = metrics()
        self.assertEqual(sum(x['enrolled'] for x in result['funnel']), 3000)
        self.assertGreater(result['eligible_d7'], 1000)
        self.assertGreater(result['returners_d7'], 0)
        self.assertLess(result['d7_retention_pct'], 100)


if __name__ == '__main__':
    unittest.main()
