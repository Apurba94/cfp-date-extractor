import datetime as dt
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from cfp_date_extractor.cli import main
from cfp_date_extractor.core import check_order, classify, extract_deadlines, find_dates, to_ics

CFP = """Call for Papers - ICRA 2027 Workshop on Field Robotics

Important Dates (all deadlines are 23:59 Anywhere on Earth)
- Abstract registration: January 15, 2027
- Full paper submission: Jan 22 2027
- Author notification: 1st March 2027
- Camera-ready due: March 15
- Conference dates: 2027-05-24 to 2027-05-28
"""


class DateTests(unittest.TestCase):
    def test_formats(self):
        got = [d for d, _, _ in find_dates("Sept 3, 2026; 4th October 2026; 2026-11-05; 12/31/2026", 2026)]
        self.assertEqual(got, [dt.date(2026, 9, 3), dt.date(2026, 10, 4), dt.date(2026, 11, 5), dt.date(2026, 12, 31)])
        self.assertEqual(find_dates("March 15"), [])
        self.assertEqual(find_dates("March 15", 2027)[0][0], dt.date(2027, 3, 15))
        self.assertEqual(find_dates("Friday, May 1, 2026")[0][0], dt.date(2026, 5, 1))
        self.assertEqual(find_dates("Feb 30, 2026"), [])

    def test_classify(self):
        self.assertEqual(classify("Paper submission deadline"), "submission")
        self.assertEqual(classify("Notification of acceptance"), "notification")
        self.assertEqual(classify("Camera-ready papers due"), "camera-ready")
        self.assertEqual(classify("Abstract registration"), "abstract")


class ExtractTests(unittest.TestCase):
    def test_cfp(self):
        recs = extract_deadlines(CFP, 2027)
        cats = [(r["category"], r["date"].isoformat()) for r in recs]
        self.assertEqual(cats[:4], [("abstract", "2027-01-15"), ("submission", "2027-01-22"),
                                    ("notification", "2027-03-01"), ("camera-ready", "2027-03-15")])
        self.assertEqual(cats[4], ("conference", "2027-05-24"))
        self.assertTrue(all(r["zone"] == "AoE" for r in recs))
        self.assertEqual(check_order(recs), [])

    def test_order_warning_and_ics(self):
        recs = extract_deadlines("Submission: 2026-06-01\nNotification: 2026-05-01", 2026)
        self.assertEqual(len(check_order(recs)), 1)
        ics = to_ics(recs, "Test Conf")
        self.assertIn("DTSTART;VALUE=DATE:20260601", ics)

    def test_cli_infers_year(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "cfp.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(CFP)
            with redirect_stdout(io.StringIO()) as buf:
                main([p, "--ics", os.path.join(d, "c.ics")])
            self.assertIn("camera-ready  2027-03-15", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
