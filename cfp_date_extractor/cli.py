"""Command-line interface for cfp-date-extractor."""
import argparse
import datetime as dt
import json
import re
import sys

from .core import check_order, extract_deadlines, to_ics


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cfp-date-extractor", description="Extract important dates from a call for papers.")
    ap.add_argument("file", nargs="?", help="CFP text (stdin if omitted)")
    ap.add_argument("--year", type=int, help="year for dates written without one (default: most common year found)")
    ap.add_argument("--name", default="Conference")
    ap.add_argument("--ics")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()
    year = args.year
    if year is None:
        years = re.findall(r"\b(20\d{2})\b", text)
        year = max(set(years), key=years.count) if years else dt.date.today().year
        year = int(year)
    recs = extract_deadlines(text, year)
    if args.json:
        print(json.dumps(recs, indent=2, default=str))
    else:
        for r in recs:
            print("%-13s %s %s %s" % (r["category"], r["date"], r["time"], r["zone"]))
        for w in check_order(recs):
            print("warning: " + w)
    if args.ics:
        with open(args.ics, "w", encoding="utf-8", newline="") as fh:
            fh.write(to_ics(recs, args.name))
    return 0
