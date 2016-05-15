# Fetch info about the calendar from corinthians.com and convert to gcal
# format.

from bs4 import BeautifulSoup
from csv import DictWriter
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText
import pytz
import sys
from urllib import urlencode, urlopen
from urlparse import urljoin


SITE_URL = "http://www.corinthians.com.br"
CSV_FILENAME = "/tmp/corinthians-cal.csv"
ICAL_FILENAME = "/tmp/corinthians-ical.ical"

tz = pytz.timezone('America/Sao_Paulo')


def fetch_url(url, data=None):
    """Fetch the given URL and return its HTML."""
    if data:
        data = urlencode(data)
    content = urlopen(url, data=data).read()
    return content


def parse_content(year, content):
    """Parse the given HTML content and return match data."""
    contents = {}
    soup = BeautifulSoup(content, 'lxml')
    for links_tag in soup.find_all('div', class_='links'):
        item = links_tag.findParent()
        date = item.find('div', class_='data')
        info = item.find('div', class_='info')
        teams = item.find('div', class_='teams')
        match_data = dict()
        datetimestr = date.find('span').text.encode('utf8')
        dtstart = parse_date(year, datetimestr)
        match_data['dtstart'] = dtstart.replace(tzinfo=tz)
        dtend = dtstart + timedelta(hours=2)
        match_data['dtend'] = dtend.replace(tzinfo=tz)
        location = info.find(
            'span', class_='icon icon-local').findParent().text
        match_data['location'] = location.strip().encode('utf8')
        match_data['team_one'] = teams.find(
            'img', class_="img-team-one").get('alt').encode('utf8')
        match_data['team_two'] = teams.find(
            'img', class_="img-team-two").get('alt').encode('utf8')
        match_data['team_one_score'] = teams.find(
            'div', class_="team-one-score").text.strip().encode('utf8')
        match_data['team_two_score'] = teams.find(
            'div', class_="team-two-score").text.strip().encode('utf8')
        link = teams.find('a').get('href')
        contents[link] = match_data
    return contents


def parse_date(year, datetimestr):
    """Return datetime object from year (%Y) and datetimestr (%d/%m%Hh%M)."""
    dt = '/'.join((str(year), datetimestr))
    return datetime.strptime(dt, "%Y/%d/%m%Hh%M")


def get_summary(match_data):
    if match_data['team_one_score'] or match_data['team_two_score']:
        summary = "%s (%s) vs (%s) %s" % (
            match_data['team_one'], match_data['team_one_score'],
            match_data['team_two_score'], match_data['team_two'])
    else:
        summary = "%s vs %s" % (
            match_data['team_one'], match_data['team_two'])
    return summary


def convert_ical(cal_data, ical_filename=ICAL_FILENAME):
    """Convert cal_data to ical format."""
    ical = Calendar()
    for k in cal_data.keys():
        event = Event()
        event['uid'] = k
        match_data = cal_data[k]
        event.add('dtstart', match_data['dtstart'])
        event.add('dtend', match_data['dtend'])
        event.add('summary', get_summary(match_data))
        event.add('description', vText(urljoin(SITE_URL, k)))
        event.add('location', match_data['location'])
        ical.add_component(event)
    with open(ical_filename, 'wb') as f:
        f.write(ical.to_ical())
    return ical.to_ical()


def convert_csv(cal_data, csv_filename=CSV_FILENAME):
    """Convert cal_data to CSV format."""
    fields = (
        'Subject', 'Start Date', 'Start Time',
        'End Date', 'End Time', 'All Day Event',
        'Description', 'Location', 'Private'
    )
    rows = []
    for k in cal_data.keys():
        match_data = cal_data[k]
        start_date = match_data['dtstart']
        end_date = match_data['dtend']
        row = {
            'Subject': "%s" % get_summary(match_data),
            'Start Date': '%s' % start_date.strftime('%d/%m/%y'),
            'Start Time': '%s' % start_date.strftime('%H:%M'),
            'End Date': '%s' % end_date.strftime('%d/%m/%y'),
            'End Time': '%s' % end_date.strftime('%H:%M'),
            'All Day Event': 'False',
            'Description': '%s' % urljoin(SITE_URL, k),
            'Location': '%(location)s' % match_data,
            'Private':  'True'
        }
        rows.append(row)
    with open(csv_filename, "wb") as csv_file:
        writer = DictWriter(csv_file, fields)
        writer.writeheader()
        writer.writerows(rows)
    csv_content = open(csv_file.name, 'r').read()
    return csv_content


def main(argv):
    events = {}
    for year in [2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008]:
        data = {'ano': year}
        url = urljoin(SITE_URL, 'jogos/ajax_jogos')
        html_content = fetch_url(url, data=data)
        # html_content doesn't have year so we have to pass on the info to the
        # function so it'll build the data structure with the correct dates.
        parsed_content = parse_content(year, html_content)
        events.update(parsed_content)
    convert_csv(events)
    convert_ical(events)
    print "%s events converted." % len(events)


if __name__ == "__main__":
    main(sys.argv)
