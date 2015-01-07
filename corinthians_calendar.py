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
CAL_URL="site/inc/ajax/jogos/getJogos.asp?mes=%d&ano=%d"
CSV_FILENAME="/tmp/corinthians-cal.csv"
ICAL_FILENAME="/tmp/corinthians-ical.ical"

tz = pytz.timezone('America/Sao_Paulo')


def fetch_url(url):
    """Fetch the given URL and return its HTML."""
    content = urlopen(url).read()
    return content


def parse_content(content):
    """Parse the given HTML content and return game data."""
    contents = {}
    soup = BeautifulSoup(content)
    for item in soup.find_all('li', class_='item'):
        if item.text == "Nenhum jogo encontrado":
            continue
        info = item.find('div', class_='info')
        teams = item.find('div', class_='teams')
        game_data = dict()
        day = info.findChildren()[0].text.split()[1].encode('utf8')
        hour = info.findChildren()[2].text.split()[1].encode('utf8')
        dtstart = parse_date(day, hour)
        game_data['dtstart'] = dtstart.replace(tzinfo=tz)
        dtend = dtstart + timedelta(hours=2)
        game_data['dtend'] = dtend.replace(tzinfo=tz)
        game_data['location'] = info.findChildren()[4].text.replace('Local:', '').strip().encode('utf8')
        game_data['team_one'] = teams.find('img', class_="team-one").get('alt').encode('utf8')
        game_data['team_two'] = teams.find('img', class_="team-two").get('alt').encode('utf8')
        game_data['team_one_score'] = teams.find(
            'div', class_="team-one-score").text.strip().encode('utf8')
        game_data['team_two_score'] = teams.find(
            'div', class_="team-two-score").text.strip().encode('utf8')
        link = item.find('a').get('href')
        contents[link] = game_data
    return contents


def parse_date(date, time):
    """For a given date and time return parsed datetime."""
    dt = ','.join((date, time))
    return datetime.strptime(dt, "%d/%m/%y,%Hh%M")


def get_summary(game_data):
    if game_data['team_one_score'] or game_data['team_two_score']:
        summary = "%s (%s) vs (%s) %s"  % (
            game_data['team_one'], game_data['team_one_score'],
            game_data['team_two_score'], game_data['team_two'])
    else:
        summary = "%s vs %s" % (
            game_data['team_one'], game_data['team_two'])
    return summary


def convert_ical(cal_data, ical_filename=ICAL_FILENAME):
    """Convert cal_data to ical format."""
    ical = Calendar()
    for k in cal_data.keys():
        event = Event()
        event['uid'] = k
        game_data = cal_data[k]
        event.add('dtstart', game_data['dtstart'])
        event.add('dtend', game_data['dtend'])
        event.add('summary', get_summary(game_data))
        event.add('description', vText(urljoin(SITE_URL, k)))
        event.add('location', game_data['location'])
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
        game_data = cal_data[k]
        start_date = game_data['dtstart']
        end_date = game_data['dtend']
        row = {
            'Subject': "%s" % get_summary(game_data),
            'Start Date': '%s' % start_date.strftime('%d/%m/%y'),
            'Start Time': '%s' % start_date.strftime('%H:%M'),
            'End Date': '%s' % end_date.strftime('%d/%m/%y'),
            'End Time': '%s' % end_date.strftime('%H:%M'),
            'All Day Event': 'False',
            'Description': '%s' % urljoin(SITE_URL, k),
            'Location': '%(location)s' % game_data,
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
    for year in [2015, 2014, 2013, 2012, 2011, 2010]:
        for month in range(1, 13):
            url = urljoin(SITE_URL, CAL_URL % (month, year))
            html_content = fetch_url(url)
            parsed_content = parse_content(html_content)
            events.update(parsed_content)
    convert_csv(events)
    convert_ical(events)
    print "%s events converted." % len(events)


if __name__ == "__main__":
    main(sys.argv)
