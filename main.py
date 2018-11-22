#!/bin/python

from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from bs4 import BeautifulSoup
from datetime import datetime
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

TESTID = 'mi584oior0veus2f79lolaht54@group.calendar.google.com'
ALGOID = 'o3alvrvraeam3vd43kqent15p4@group.calendar.google.com'
CURRENTID = ALGOID


def codeforces_time2iso(str_time, str_length):
    datetime_start = datetime.strptime(str_time, '%b/%d/%Y %H:%M')
    datetime_length = datetime.strptime(str_length, '%H:%M')
    datetime_base = datetime.strptime('00:00', '%H:%M')
    timedelta_length = datetime_length - datetime_base
    datetime_end = datetime_start + timedelta_length
    return datetime_start.isoformat() + '+03:00', \
        datetime_end.isoformat() + '+03:00'


def atcoder_time2iso(str_time, str_length):
    datetime_start = datetime.strptime(str_time, '%Y/%m/%d %H:%M')
    datetime_length = datetime.strptime(str_length, '%H:%M')
    datetime_base = datetime.strptime('00:00', '%H:%M')
    timedelta_length = datetime_length - datetime_base
    datetime_end = datetime_start + timedelta_length
    return datetime_start.isoformat() + '+09:00', \
        datetime_end.isoformat() + '+09:00'


def hackerrank_time2iso(str_start, str_end):
    return str_start, str_end


def codechef_time2iso(str_start, str_end):
    return str_start, str_end


def parse_codeforces_events(text):
    soup = BeautifulSoup(text, 'lxml')
    first_table = soup.find('table')
    contests = first_table.find_all('tr')[1:]

    contest_list = []
    for contest in contests:
        name, writers, start, length = [
            element.get_text().strip()
            for element in contest.find_all('td')[:4]]
        contest_list.append((name, start, length))
    return contest_list


def parse_atcoder_events(text):
    soup = BeautifulSoup(text, 'lxml')
    first_table = soup.find_all('table', class_='table')[1]
    contests = first_table.find('tbody').find_all('tr')

    contest_list = []
    for contest in contests[::3]:
        start, name, length, limit = [
            element.get_text().strip()
            for element in contest.find_all('td')[:]][:4]
        contest_list.append((name, start, length))
    return contest_list


def parse_hackerrank_events(text):
    soup = BeautifulSoup(text, 'lxml')
    contests = soup.find(class_="contests-active").find_all(class_="contest-tab-expander")

    contest_list = []
    for contest in contests:
        name = contest.find(class_="contest-name").get_text()
        start_element = contest.find(class_="fnt-sz-small txt-navy")
        if start_element.span is not None:
            meta_dict = {}
            for meta in start_element.span.span.find_all():
                meta_dict[meta['itemprop']] = meta['content']
            contest_list.append((name, meta_dict['startDate'], meta_dict['endDate']))
    return contest_list


def parse_codechef_events(text):
    soup = BeautifulSoup(text, 'lxml')
    contests = soup.find_all(class_="dataTable")[1]

    contest_list = []
    for contest in contests.tbody.find_all("tr"):
        elements = contest.find_all("td")
        name = elements[1].get_text()
        str_start = elements[2]['data-starttime']
        str_end = elements[3]['data-endtime']
        contest_list.append((name, str_start, str_end))
    return contest_list


class AddEvents(object):

    def __init__(self, url, website, parse_event, time2iso, event_list):
        self.url = url
        self.website = website
        self.time2iso = time2iso
        self.parse_event = parse_event
        self.event_set = event_list

    def add_events(self, service, calendar_id):
        event = {
            'summary': 'None',
            'description': self.website,
            'start': {
                'dateTime': 'None',
            },
            'end': {
                'dateTime': 'None',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
            'source': {
                'title': self.website,
                'url': self.url,
            },
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:55.0) Gecko/20100101 Firefox/55.0",
        }
        html_result = requests.get(self.url, headers=headers)
        contest_list = self.parse_event(html_result.text)

        for contest in contest_list:
            name, start, length = contest
            str_start, str_end = self.time2iso(start, length)
            if name in self.event_set:
                print(name, 'has been added')
            else:
                event['summary'] = name
                event['start']['dateTime'] = str_start
                event['end']['dateTime'] = str_end
                insert_result = service.events().insert(
                    calendarId=calendar_id, body=event).execute()
                print(insert_result)


def fetch_all_events(service, calendar_id):
    """Fetching all events of the calenderId

    :return: list [event0, event1, ..., ]
    """
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    page_token = None
    event_list = []
    while True:
        events = service.events().list(calendarId=calendar_id,
                                       pageToken=page_token,
                                       timeMin=now,
                                       singleEvents=True,
                                       orderBy='startTime').execute()
        event_list.extend(events.get('items', []))
        page_token = events.get('nextPageToken')
        if not page_token:
            break
    return event_list


def main():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    calendar_event_list = fetch_all_events(service, CURRENTID)

    summary_list = set([event.get('summary') for event in calendar_event_list])

    AddEvents(url="http://codeforces.com/contests",
              website="Codeforces",
              parse_event=parse_codeforces_events,
              time2iso=codeforces_time2iso,
              event_list=summary_list).add_events(service, CURRENTID)
    AddEvents(url="http://atcoder.jp/contest",
              website="AtCoder",
              parse_event=parse_atcoder_events,
              time2iso=atcoder_time2iso,
              event_list=summary_list).add_events(service, CURRENTID)
    AddEvents(url="https://www.hackerrank.com/contests",
              website="Hackerrank",
              parse_event=parse_hackerrank_events,
              time2iso=hackerrank_time2iso,
              event_list=summary_list).add_events(service, CURRENTID)
    AddEvents(url="https://www.codechef.com/contests",
              website="Codechef",
              parse_event=parse_codechef_events,
              time2iso=codechef_time2iso,
              event_list=summary_list).add_events(service, CURRENTID)


if __name__ == '__main__':
    main()
