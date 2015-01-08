import datetime
from doctest import ELLIPSIS, NORMALIZE_WHITESPACE, REPORT_NDIFF
import os.path
import pytz
from tempfile import NamedTemporaryFile

from testtools import TestCase
from testtools.matchers import DocTestMatches, Contains, StartsWith

from corinthians_calendar import (
    convert_csv,
    convert_ical,
    fetch_url,
    parse_content
    )


tz = pytz.timezone('America/Sao_Paulo')


class TestCalendarConverter(TestCase):

    def setUp(self):
        super(TestCalendarConverter, self).setUp()
        self.sample_data = open('sample.html').read()

    def test_fetch_url(self):
        fake_url = 'file://%s/sample.html' % os.path.dirname(__file__)
        expected_content = '<a href="/site/futebol/jogos/informacoes/?id=510">'
        url_content = fetch_url(fake_url)
        self.assertThat(url_content, Contains(expected_content))

    def test_parse_content(self):
        expected_content = {
            '/site/futebol/jogos/informacoes/?id=510': {
                'dtstart': datetime.datetime(2014, 11, 30, 0, 0, tzinfo=tz),
                'dtend': datetime.datetime(2014, 11, 30, 2, 0, tzinfo=tz),
                'location': u'A definir',
                'team_one': u'Fluminense',
                'team_one_score': '',
                'team_two': u'Corinthians',
                'team_two_score': ''
            }
        }
        contents = parse_content(self.sample_data)
        content_key = expected_content.keys()[0]
        self.assertEquals(contents[content_key], expected_content[content_key])

    def test_convert_ical(self):
        ical = convert_ical(parse_content(self.sample_data))
        expected_ical = ("""
            BEGIN:VCALENDAR
            ...
            BEGIN:VEVENT
            SUMMARY:Bahia vs Corinthians\r
            DTSTART;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20141116T170000\r
            DTEND;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20141116T190000\r
            UID:/site/futebol/jogos/informacoes/?id=507\r
            DESCRIPTION:http://www.corinthians.com.br/.../?\r\n id=507\r
            LOCATION:Fonte Nova\r
            END:VEVENT
            ...
            END:VCALENDAR
            """)

        flags = ELLIPSIS | NORMALIZE_WHITESPACE | REPORT_NDIFF
        self.assertThat(ical, DocTestMatches(expected_ical, flags))

    def test_convert_csv(self):
        csv_header = (
            'Subject', 'Start Date', 'Start Time',
            'End Date', 'End Time', 'All Day Event',
            'Description', 'Location', 'Private'
        )
        tmp_file = NamedTemporaryFile()
        csv = convert_csv(
            parse_content(self.sample_data), csv_filename=tmp_file.name)
        self.assertThat(csv, StartsWith(csv_header))
        expected_content = (
            "/site/futebol/jogos/informacoes/?id=506")
        self.assertThat(tmp_file.read(), Contains(expected_content))
