This script parses the match dates from the official Corinthians website and
convert them to ical calendar events suitable to be imported into a calendar
application (e.g. Google Calendar).

To use the script:
```
python corinthians_calendar.py
```
You can find the ical file at /tmp/corinthians-ical.ical which is suitable to
be imported into a calendar application.

To run tests:
```
nosetests test_calendar.py
```
