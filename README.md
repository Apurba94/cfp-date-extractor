# cfp-date-extractor

**Paste a call for papers, get its important dates: abstract, submission, rebuttal, notification,
camera-ready and conference dates, with time zones (AoE), order checks and a calendar file.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Calls for papers arrive by e-mail and mailing lists with dates written in every possible format
("Jan 22 2027", "1st March 2027", "2027-05-24", "March 15"). Copying them into a calendar by hand for
every venue you consider is slow and error-prone. Extracting them automatically makes it easy to track
many venues, and combines well with `deadline-tracker` from this toolkit.

## Features

- Date formats: ISO, `Month D, YYYY`, `D Month YYYY` (with ordinals and weekdays), `M/D/YYYY`, and
  `Month D` without a year (year inferred from the text or `--year`)
- Line-based classification: abstract, submission, rebuttal, notification, camera-ready, registration,
  workshop, conference
- Times and zones after dates; "Anywhere on Earth" detected for the whole call
- Sanity check that dates follow the usual order; ICS export; JSON output

## Usage

```bash
pip install .
cfp-date-extractor cfp_email.txt --name "ICRA 2027 Workshop" --ics icra.ics
pbpaste | cfp-date-extractor --json
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
