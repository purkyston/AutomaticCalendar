#!/bin/python

from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

TESTID = 'mi584oior0veus2f79lolaht54@group.calendar.google.com'
ALGOID = 'o3alvrvraeam3vd43kqent15p4@group.calendar.google.com'
CURRENTID = ALGOID


def CodeforcesTime2ISO(str_time, str_length):
  datetime_start = datetime.strptime(str_time, '%b/%d/%Y %H:%M')
  datetime_length = datetime.strptime(str_length, '%H:%M')
  datetime_base = datetime.strptime('00:00', '%H:%M')
  timedelta_length = datetime_length - datetime_base
  datetime_end = datetime_start + timedelta_length
  return datetime_start.isoformat()+'+03:00', datetime_end.isoformat() + '+03:00'

def AtcoderTime2ISO(str_time, str_length):
    datetime_start = datetime.strptime(str_time, '%Y/%m/%d %H:%M')
    datetime_length = datetime.strptime(str_length, '%H:%M')
    datetime_base = datetime.strptime('00:00', '%H:%M')
    timedelta_length = datetime_length - datetime_base
    datetime_end = datetime_start + timedelta_length
    return datetime_start.isoformat()+'+09:00', datetime_end.isoformat() + '+09:00'


def AddCodeforcesEvents(service, calendar_event_summary_list):

  result = requests.get("http://codeforces.com/contests")
  soup = BeautifulSoup(result.text)
  first_table = soup.find('table')
  contests = first_table.find_all('tr')[1:]

  event = {
    'summary': 'None',
    'description': 'Codeforces',
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
  }

  for contest in contests:
    name, writers, start, length = [element.get_text().strip() for element in contest.find_all('td')[:4]]
    #print(name, writers, start, length)
    str_start, str_end = CodeforcesTime2ISO(start, length)
    #print(str_start, str_end)
    if name in calendar_event_summary_list:
      print(name, 'has been added')
    else:
      event['summary'] = name
      event['start']['dateTime'] = str_start
      event['end']['dateTime'] = str_end
      insert_result = service.events().insert(calendarId=CURRENTID, body=event).execute()
      print(insert_result)

def AddAtcoderEvents(service, calendar_event_summary_list):

  result = requests.get("http://atcoder.jp/contest")
  soup = BeautifulSoup(result.text)
  first_table = soup.find_all('table', class_='table')[1]
  contests = first_table.find('tbody').find_all('tr')

  event = {
    'summary': 'None',
    'description': 'AtCoder',
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
  }

  for contest in contests[::3]:
    start, name, length, limit = [element.get_text().strip() for element in contest.find_all('td')[:]][:4]
    str_start, str_end = AtcoderTime2ISO(start, length)
    if name in calendar_event_summary_list:
      print(name, 'has been added')
    else:
      event['summary'] = name
      event['start']['dateTime'] = str_start
      event['end']['dateTime'] = str_end
      insert_result = service.events().insert(calendarId=CURRENTID, body=event).execute()
      print(insert_result)


def FetchAllEvents(service):
  # Call the Calendar API
  now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
  page_token = None
  event_list = []
  while True:
    events = service.events().list(calendarId=CURRENTID, pageToken=page_token, timeMin=now,
                                   singleEvents=True, orderBy='startTime').execute()
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

  # Call the Calendar API
  now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

  calendar_event_list = FetchAllEvents(service)

  summary_list = set([event.get('summary') for event in calendar_event_list])

  AddCodeforcesEvents(service, summary_list)
  AddAtcoderEvents(service, summary_list)


if __name__ == '__main__':
  main()
