# -*- coding: utf-8 -*-
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
        expected = '<a href="http://www.corinthians.com.br/jogos/ver/29">'
        url_content = fetch_url(fake_url)
        self.assertThat(url_content, Contains(expected))

    def test_parse_content(self):
        expected_content = {
            'http://www.corinthians.com.br/jogos/ver/29': {
                'dtstart': datetime.datetime(2008, 07, 05, 16, 10, tzinfo=tz),
                'dtend': datetime.datetime(2008, 07, 05, 18, 10, tzinfo=tz),
                'location': 'Pacaembu',
                'team_one': 'Corinthians',
                'team_one_score': '1',
                'team_two': 'São Caetano',
                'team_two_score': '0'
            }
        }
        contents = parse_content(2008, self.sample_data)
        content_key = expected_content.keys()[0]
        self.assertEquals(contents[content_key], expected_content[content_key])

    def test_convert_ical(self):
        ical = convert_ical(parse_content(2008, self.sample_data))
        expected_ical = ("""
            BEGIN:VCALENDAR
            ...
            BEGIN:VEVENT
            SUMMARY:Corinthians (1) vs (0) São Caetano\r
            DTSTART;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20080705T161000\r
            DTEND;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20080705T181000\r
            UID:http://www.corinthians.com.br/jogos/ver/29\r
            DESCRIPTION:http://www.corinthians.com.br/jogos/ver/29\r
            LOCATION:Pacaembu\r
            END:VEVENT
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
            parse_content(2008, self.sample_data), csv_filename=tmp_file.name)
        self.assertThat(csv, StartsWith(csv_header))
        expected_content = (
            'http://www.corinthians.com.br/jogos/ver/29')
        self.assertThat(tmp_file.read(), Contains(expected_content))
