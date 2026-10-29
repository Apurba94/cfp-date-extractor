"""Date recognition in free text plus keyword-based classification of the surrounding line."""
import datetime as dt
import re

MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                           "september", "october", "november", "december"])}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_WD = r"(?:(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+)?"
PATTERNS = [
    ("iso", re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")),
    ("mdy", re.compile(_WD + r"\b(" + _MON + r")\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)),
    ("dmy", re.compile(_WD + r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + _MON + r"),?\s+(\d{4})\b", re.I)),
    ("md", re.compile(_WD + r"\b(" + _MON + r")\s+(\d{1,2})(?:st|nd|rd|th)?\b(?!,?\s*\d{4})", re.I)),
    ("slash", re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")),
]
CATEGORIES = [
    ("abstract", r"abstract\s+(?:submission|registration|deadline|due)|abstracts?\s+due|paper registration"),
    ("rebuttal", r"rebuttal|author response|response period"),
    ("notification", r"notification|acceptance|decisions?\b|author notification"),
    ("camera-ready", r"camera[- ]ready|final (?:version|manuscript|paper)"),
    ("registration", r"early[- ]bird|registration"),
    ("workshop", r"workshop|tutorial"),
    ("conference", r"conference dates?|conference will|main conference|event dates?|takes place|held (?:on|in)"),
    ("submission", r"submission|paper deadline|full papers?|manuscripts? due|deadline"),
]
_TIME = re.compile(r"(\d{1,2}:\d{2})\s*(AoE|UTC[+-]?\d*|GMT[+-]?\d*|anywhere on earth|[A-Z]{3,4}T?)?", re.I)


def _mon(s):
    return MONTHS[s.lower().rstrip(".")[:4] if s.lower().startswith("sept") else s.lower().rstrip(".")[:3]]


def find_dates(text, default_year=None, slash_order="mdy"):
    """Return [(date, start, end)] for all dates found; month-day dates get default_year."""
    found, used = [], []
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            if any(a < m.end() and m.start() < b for a, b in used):
                continue
            g = m.groups()
            try:
                if kind == "iso":
                    d = dt.date(int(g[0]), int(g[1]), int(g[2]))
                elif kind == "mdy":
                    d = dt.date(int(g[2]), _mon(g[0]), int(g[1]))
                elif kind == "dmy":
                    d = dt.date(int(g[2]), _mon(g[1]), int(g[0]))
                elif kind == "md":
                    if default_year is None:
                        continue
                    d = dt.date(default_year, _mon(g[0]), int(g[1]))
                else:
                    a, b, y = int(g[0]), int(g[1]), int(g[2])
                    d = dt.date(y, a, b) if slash_order == "mdy" else dt.date(y, b, a)
            except (ValueError, KeyError):
                continue
            found.append((d, m.start(), m.end()))
            used.append((m.start(), m.end()))
    return sorted(found, key=lambda x: x[1])


def classify(context):
    c = context.lower()
    for name, rx in CATEGORIES:
        if re.search(rx, c):
            return name
    return "other"


def extract_deadlines(text, default_year=None):
    """One record per date: category, date, time/zone if present, the source line."""
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for d, s, e in find_dates(line, default_year):
            context = line if classify(line) != "other" else (lines[i - 1] + " " + line if i else line)
            tm = _TIME.search(line[e:e + 40])
            out.append({"category": classify(context), "date": d, "time": tm.group(1) if tm else "",
                        "zone": (tm.group(2) or "").replace("anywhere on earth", "AoE") if tm else "",
                        "line": line.strip()})
    if re.search(r"(?i)anywhere on earth|\baoe\b", text):
        for r in out:
            r["zone"] = r["zone"] or "AoE"
    return out


def check_order(records):
    """Warn if the usual order submission <= notification <= camera-ready <= conference is violated."""
    order = ["abstract", "submission", "rebuttal", "notification", "camera-ready", "conference"]
    firsts = {}
    for r in records:
        firsts.setdefault(r["category"], r["date"])
    warn = []
    seq = [c for c in order if c in firsts]
    for a, b in zip(seq, seq[1:]):
        if firsts[a] > firsts[b]:
            warn.append("%s (%s) is after %s (%s)" % (a, firsts[a], b, firsts[b]))
    return warn


def to_ics(records, name="Conference"):
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//research-toolkit//cfp-date-extractor//EN"]
    for i, r in enumerate(records):
        if r["category"] == "other":
            continue
        out += ["BEGIN:VEVENT", "UID:%s-%d-%s@cfp" % (re.sub(r"\W", "", name), i, r["date"].strftime("%Y%m%d")),
                "DTSTAMP:%s" % dt.datetime.now().strftime("%Y%m%dT%H%M%S"),
                "DTSTART;VALUE=DATE:%s" % r["date"].strftime("%Y%m%d"),
                "SUMMARY:%s: %s%s" % (name.replace(",", "\\,"), r["category"],
                                      " %s %s" % (r["time"], r["zone"]) if r["time"] else ""),
                "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"
