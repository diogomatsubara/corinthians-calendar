import doctest
import os.path
from tempfile import NamedTemporaryFile

from testtools import TestCase
from testtools.matchers import DocTestMatches, Contains

from corinthians_calendar import fetch_url, parse_content, convert_csv, convert_ical


class TestCalendarConverter(TestCase):

    def test_fetch_url(self):
        fake_url = 'file://%s/sample.html' % os.path.dirname(__file__)
        expected_content = '<a href="/site/futebol/jogos/informacoes/?id=510">'
        url_content = fetch_url(fake_url)
        self.assertThat(url_content, Contains(expected_content))

    def test_parse_content(self):
        expected_content = {
            '/site/futebol/jogos/informacoes/?id=510': {
                'day': u'30/11/14',
                'hour': u'0h00',
                'location': u'A definir',
                'team_one': u'Fluminense',
                'team_two': u'Corinthians'
            }
        }
        sample_data = open('sample.html').read()
        contents = parse_content(sample_data)
        content_key = expected_content.keys()[0]
        self.assertEquals(contents[content_key], expected_content[content_key])

    def test_convert_ical(self):
        sample_data = open('sample.html').read()
        ical = convert_ical(parse_content(sample_data))
        expected_ical = ("""
            BEGIN:VCALENDAR
            ...
            BEGIN:VEVENT
            SUMMARY:Bahia vs Corinthians\r
            DTSTART;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20141116T170000\r
            DTEND;TZID=America/Sao_Paulo;VALUE=DATE-TIME:20141116T190000\r
            UID:/site/futebol/jogos/informacoes/?id=507\r
            DESCRIPTION:http://www.corinthians.com.br/site/futebol/jogos/informacoes/?\r\n id=507\r
            LOCATION:Fonte Nova\r
            END:VEVENT
            ...
            END:VCALENDAR
            """
        )

        flags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF
        self.assertThat(ical, DocTestMatches(expected_ical, flags))

    def test_convert_csv(self):
        csv_header = (
            'Subject', 'Start Date', 'Start Time',
            'End Date', 'End Time', 'All Day Event',
            'Description', 'Location', 'Private'
        )
        sample_data = open('sample.html').read()
        tmp_file = NamedTemporaryFile()
        csv_writer= convert_csv(
            parse_content(sample_data), csv_filename=tmp_file.name)
        self.assertEquals(csv_writer.fieldnames, csv_header)
        expected_content = (
            "/site/futebol/jogos/informacoes/?id=506")
        self.assertThat(tmp_file.read(), Contains(expected_content))
