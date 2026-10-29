"""Extract submission, notification and camera-ready dates from call-for-papers text."""
from .core import find_dates, classify, extract_deadlines, to_ics

__version__ = "0.1.0"
__all__ = ["find_dates", "classify", "extract_deadlines", "to_ics"]
