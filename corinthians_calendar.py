# Fetch info about the calendar from corinthians.com and convert to gcal
# format.

from bs4 import BeautifulSoup
from csv import DictWriter
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText
import pytz
import sys
from urllib import urlopen
from urlparse import urljoin


SITE_URL="http://www.corinthians.com.br"
CAL_URL="site/inc/ajax/jogos/getJogos.asp?mes=%d&ano=2014"
CSV_FILENAME="/tmp/corinthians-cal.csv"


def fetch_url(url):
    """Fetch the given URL and return its HTML."""
    content = urlopen(url).read()
    return content


def parse_content(content):
    """Parse the given HTML content and return game data."""
    contents = {}
    soup = BeautifulSoup(content)
    for item in soup.find_all('li', class_='item'):
        info = item.find('div', class_='info')
        teams = item.find('div', class_='teams')
        game_data = dict()
        game_data['day'] = info.findChildren()[0].text.split()[1].encode('utf8')
        game_data['hour'] = info.findChildren()[2].text.split()[1].encode('utf8')
        game_data['location'] = info.findChildren()[4].text.replace('Local:', '').strip().encode('utf8')
        game_data['team_one'] = teams.find_all('img')[0].get('alt').encode('utf8')
        game_data['team_two'] = teams.find_all('img')[1].get('alt').encode('utf8')
        link = item.find('a').get('href')
        contents[link] = game_data
    return contents


def convert_ical(cal_data):
    """Convert cal_data to ical format."""
    # TODO:
    # - need to fix up TZ information for ical
    ical = Calendar()
    tz = pytz.timezone('America/Sao_Paulo')
    for k in cal_data.keys():
        event = Event()
        event['uid'] = k
        game_data = cal_data[k]
        start_date = parse_date(game_data['day'], game_data['hour'])
        end_date = start_date + timedelta(hours=2)
        event.add('dtstart', start_date.replace(tzinfo=tz))
        event.add('dtend', end_date.replace(tzinfo=tz))
        event.add('summary', "%s vs %s" % (
            game_data['team_one'], game_data['team_two']))
        event.add('description', vText(urljoin(SITE_URL, k)))
        event.add('location', game_data['location'])
        ical.add_component(event)
    return ical.to_ical()


def parse_date(date, time):
    """For a given date and time return parsed datetime."""
    dt = ','.join((date, time))
    return datetime.strptime(dt, "%d/%m/%y,%Hh%M")


def convert_csv(cal_data, csv_filename=CSV_FILENAME):
    """Convert cal_data to CSV format."""
    fields = (
        'Subject', 'Start Date', 'Start Time',
        'End Date', 'End Time', 'All Day Event',
        'Description', 'Location', 'Private'
    )
    csv_file = open(csv_filename, "wb")
    writer = DictWriter(csv_file, fields)
    writer.writeheader()
    for k in cal_data.keys():
        game_data = cal_data[k]
        start_date = parse_date(game_data['day'], game_data['hour'])
        end_date = start_date + timedelta(hours=2)
        row = {
            'Subject': "%(team_one)s vs %(team_two)s" % game_data,
            'Start Date': '%s' % start_date.strftime('%d/%m/%y'),
            'Start Time': '%s' % start_date.strftime('%H:%M'),
            'End Date': '%s' % end_date.strftime('%d/%m/%y'),
            'End Time': '%s' % end_date.strftime('%H:%M'),
            'All Day Event': 'False',
            'Description': '%s' % urljoin(SITE_URL, k),
            'Location': '%(location)s' % game_data,
            'Private':  'True'
        }
        writer.writerow(row)
    csv_file.close()
    return writer


def main(argv):
    full_year = {}
    for month in range(1, 13):
        url = urljoin(SITE_URL, CAL_URL % month)
        html_content = fetch_url(url)
        parsed_content = parse_content(html_content)
        full_year.update(parsed_content)
    convert_csv(full_year)
    f = open('/tmp/ical.ical', 'wb')
    f.write(convert_ical(full_year))
    f.close()


if __name__ == "__main__":
    main(sys.argv)
