#!/usr/bin/env python

from prompt_toolkit.contrib.shortcuts import get_input
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.contrib.completers import WordCompleter
import arrow
import csv
import sys
import os.path
import logging
import re
import datetime


FILENAME = 'labels.csv'

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

remarks_index = set()
situations_index = set()

default = {
    'resident': None,
    'starttime': None,
    'endtime': None,
    'type': None,
    'confidence': None
}


def init():
    global remarks_index
    global situations_index
    try:
        with open(sys.argv[1], 'r') as csvfile:
            reader = list(csv.DictReader(csvfile))
            remarks_index = set(map(lambda x: x['remarks'], reader))
            situations_index = set(map(lambda x: x['guessed_situation'],
                                   reader))

            last_line = reader[-1]
            default['resident'] = last_line['resident']
            default['type'] = last_line['type_of_observation']
            default['confidence'] = last_line['confidence']
            default['starttime'] = last_line['endtime']
    except IOError:
        logging.debug('The CSV file doesn\'t exist')


def parse_list_answer(answer, accepted_values, default):
    if default is not None and answer == '':
        return default
    try:
        return accepted_values[int(answer) - 1]
    except (ValueError, IndexError):
        answer = answer.split(". ")[-1]
        if answer not in accepted_values:
            raise ValueError
        return answer


def _parse_absolute_date(raw_date, default):
    regex_mm = re.compile('(?P<min>\d{1,2})$')
    regex_hh_mm = re.compile('(?P<hour>\d{1,2}):(?P<min>\d{1,2})$')
    regex_hh_mm_ss = re.compile('(?P<hour>\d{1,2}):(?P<min>\d{1,2}):'
                                '(?P<sec>\d{1,2})$')
    regex_dd_hh_mm_ss = re.compile('(?P<day>\d{1,2}) +(?P<hour>\d{1,2}):'
                                   '(?P<min>\d{1,2}):(?P<sec>\d{1,2})$')
    regex_mm_dd_hh_mm_ss = re.compile('(?P<month>\d{1,2})-(?P<day>\d{1,2})'
                                      ' +(?P<hour>\d{1,2}):'
                                      '(?P<min>\d{1,2}):(?P<sec>\d{1,2})$')
    regex_yyyy_mm_dd_hh_mm_ss = re.compile('(?P<year>\d{4})-'
                                           '(?P<month>\d{1,2})-'
                                           '(?P<day>\d{1,2}) +'
                                           '(?P<hour>\d{1,2}):'
                                           '(?P<min>\d{1,2}):'
                                           '(?P<sec>\d{1,2})$')

    if default is not None:
        results = (regex_mm.match(raw_date) or
                   regex_hh_mm.match(raw_date) or
                   regex_hh_mm_ss.match(raw_date) or
                   regex_dd_hh_mm_ss.match(raw_date) or
                   regex_mm_dd_hh_mm_ss.match(raw_date) or
                   regex_yyyy_mm_dd_hh_mm_ss.match(raw_date))
    else:
        results = regex_yyyy_mm_dd_hh_mm_ss.match(raw_date)
    if results is None:
        raise ValueError

    units = {}
    for unit in ['year', 'month', 'day', 'hour', 'min', 'sec']:
        try:
            units[unit] = int(results.group(unit))
        except IndexError:
            units[unit] = None

    parsed_date = arrow.get(
        units['year'] if units['year'] is not None else default.year,
        units['month'] if units['month'] is not None else default.month,
        units['day'] if units['day'] is not None else default.day,
        units['hour'] if units['hour'] is not None else default.hour,
        units['min'] if units['min'] is not None else default.minute,
        units['sec'] if units['sec'] is not None else 0,
    )
    return parsed_date


def _parse_relative_date(raw_date, relative_to):
    if relative_to is None:
        raise ValueError
    regex_seconds = re.compile('(?P<sec>\d+) *s(?:ec(?:onds?)?)?')
    regex_minutes = re.compile('(?P<min>\d+) *m(?:in(?:utes?)?)?')
    regex_hours = re.compile('(?P<hour>\d+) *h(?:ours?)?')
    regex_days = re.compile('(?P<day>\d+) *d(?:ays?)?')
    days = regex_days.search(raw_date)
    if days is not None:
        days = int(days.group('day'))
    hours = regex_hours.search(raw_date)
    if hours is not None:
        hours = int(hours.group('hour'))
    minutes = regex_minutes.search(raw_date)
    if minutes is not None:
        minutes = int(minutes.group('min'))
    seconds = regex_seconds.search(raw_date)
    if seconds is not None:
        seconds = int(seconds.group('sec'))
    delta = datetime.timedelta(
        days=days or False,
        hours=hours or False,
        minutes=minutes or False,
        seconds=seconds or False
    )

    if delta.total_seconds == 0:
        raise ValueError

    if raw_date[0] == '+':
        parsed_date = relative_to + delta
    else:  # if date[0] == '-'
        parsed_date = relative_to - delta
    return parsed_date


def parse_date(raw_date, default_str, accept_pasttime=True):
    regex_full = re.compile('(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) '
                            '(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})')
    if (default_str is not None and regex_full.match(default_str) is not None):
        default_date = arrow.get(default_str)
    else:
        default_date = None

    if raw_date == '':
        return default_date.format()

    try:
        if raw_date[0] not in ['+', '-']:
            parsed_date = _parse_absolute_date(raw_date, default_date)
        else:
            parsed_date = _parse_relative_date(raw_date, default_date)
    except (ValueError, IndexError):
        raise ValueError

    if default_date is not None and (parsed_date < default_date
                                     and not accept_pasttime):
        raise ValueError

    return parsed_date.format()


def _print_date_format_helper(default):
    regex_full = re.compile('(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) '
                            '(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})')
    if default is not None and regex_full.match(default) is not None:
        _default = arrow.get(default)
    else:
        _default = None
    print("Accepted values: ")
    if _default is not None:
        print("mm")
        print("hh:mm")
        print("hh:mm:ss")
        print("dd hh:mm:ss")
        print("mm-dd hh:mm:ss")
        print("yyyy-mm-dd hh:mm:ss")
        print("+Xmin(utes) Xsec(onds) Xh(ours) Xd(ays) "
              "(each of these are optional)")
        print("-Xmin(utes) Xsec(onds) Xh(ours) Xd(ays) "
              "(each of these are optional)")
    else:
        print("yyyy-mm-dd hh:mm:ss")


class ListValidator(Validator):
    def __init__(self, accepted_values, default):
        self.accepted_values = accepted_values
        self.default = default

    def validate(self, document):
        try:
            parse_list_answer(document.text, self.accepted_values,
                              self.default)
        except ValueError:
            raise ValidationError(message='Not a valid answer',
                                  index=len(document.text))


class ResidentValidator(Validator):
    def __init__(self, accepted_values, accept_empty=False):
        self.accepted_values = accepted_values
        if accept_empty:
            self.accepted_values.append('')

    def validate(self, document):
        if document.text not in self.accepted_values:
            raise ValidationError(message='Unknown resident',
                                  index=len(document.text))


class DateValidator(Validator):
    def __init__(self, default, accept_pasttime=True):
        self.default = default
        self.accept_pasttime = accept_pasttime

    def validate(self, document):
        if document.text == '?':
            return
        try:
            parse_date(document.text, self.default,
                       accept_pasttime=self.accept_pasttime)
        except ValueError:
            raise ValidationError(message='Failed to parse datetime',
                                  index=len(document.text))


def read_resident():
    validator = ResidentValidator(
        ['3', '4', '5', '6', '7', '8'],
        accept_empty=(default['resident'] is not None))
    resident = get_input('Resident? ' + ('[default %s] ' % default['resident']
                                         if default['resident'] is not None
                                         else ''),
                         validator=validator)
    if resident == '':
        resident = default['resident']
    default['resident'] = resident
    return resident


def read_starttime():
    starttime = get_input('Start time? (? for help) '
                          + ('[default "%s"] ' % default['starttime'][:19]
                             if default['starttime'] is not None
                             else '') +
                          '>> ',
                          validator=DateValidator(default['starttime']))
    if starttime == '?':
        print("---")
        _print_date_format_helper(default['starttime'])
        print("---")
        return read_starttime()
    else:
        start = parse_date(starttime, default['starttime'])
        default['endtime'] = start
        return start


def read_endtime():
    endtime = get_input('End time? (? for help) '
                        + ('[default "%s"] ' % default['endtime'][:19]
                           if default['endtime'] is not None
                           else '') +
                        '>> ',
                        validator=DateValidator(default['endtime'],
                                                accept_pasttime=False))
    if endtime == '?':
        print("---")
        _print_date_format_helper(default['endtime'])
        print("---")
        return read_endtime()
    else:
        end = parse_date(endtime, default['endtime'], accept_pasttime=False)
        default['starttime'] = end
        return end


def read_type_of_observation():
    observations_list = [
        'Correct inference',
        'Reasoning error',
        'Sensing error',
        'System failure',
        'Other'
    ]

    _observations_list = ['%d. %s' % (i, observation)
                          for i, observation
                          in enumerate(observations_list, 1)]
    validator = ListValidator(observations_list, default['type'])
    observations_completer = WordCompleter(_observations_list)

    type_of_observation = get_input(
        'Type of observation?'
        + (' [default %d]' % (observations_list.index(default['type']) + 1)
           if default['type'] is not None else '')
        + '\n(%s)' % ', '.join(_observations_list)
        + '\n>> ',
        completer=observations_completer,
        validator=validator)
    _type_of_observation = parse_list_answer(type_of_observation,
                                             observations_list,
                                             default['type'])
    default['type'] = _type_of_observation
    return _type_of_observation


def read_guessed_situation():
    guessed_situation_completer = WordCompleter(situations_index)

    guessed_situation = get_input('Guessed situation? >> ',
                                  completer=guessed_situation_completer)
    if guessed_situation == '?':
        print('--')
        print('\n'.join(situations_index))
        print('--')
        return read_guessed_situation()
    else:
        situations_index.add(guessed_situation)
        return guessed_situation


def read_remarks():
    remarks_completer = WordCompleter(remarks_index)

    remarks = get_input('Remarks? >> ', completer=remarks_completer)
    if remarks == '?':
        print('--')
        print('\n'.join(remarks_index))
        print('--')
        return read_remarks()
    else:
        remarks_index.add(remarks)
        return remarks


def read_confidence():
    confidence_list = [
        'Just a doubt',
        'Perhaps',
        'Probably',
        'Very likely',
        'Sure'
    ]
    _confidence_list = ['%d. %s' % (i, confidence)
                        for i, confidence in enumerate(confidence_list, 1)]
    validator = ListValidator(confidence_list, default['confidence'])
    confidence_completer = WordCompleter(_confidence_list)

    confidence = get_input(
        'Confidence?'
        + (' [default %s]' % (confidence_list.index(default['confidence']) + 1)
           if default['confidence'] is not None else '')
        + '\n(%s)' % ', '.join(_confidence_list)
        + '\n>> ',
        completer=confidence_completer,
        validator=validator)
    _confidence = parse_list_answer(confidence, confidence_list,
                                    default['confidence'])
    default['confidence'] = _confidence
    return _confidence


def ask_for_labels():
    while True:
        resident = read_resident()

        starttime = read_starttime()
        endtime = read_endtime()

        type_of_observation = read_type_of_observation()
        guessed_situation = read_guessed_situation()
        remarks = read_remarks()
        confidence = read_confidence()

        print('----------------------')

        yield {
            'resident': resident,
            'starttime': starttime,
            'endtime': endtime,
            'remarks': remarks,
            'confidence': confidence,
            'type_of_observation': type_of_observation,
            'guessed_situation': guessed_situation
        }


def save(label):
    flag_new_file = not os.path.isfile(sys.argv[1])
    with open(sys.argv[1], 'a') as csvfile:
        fieldnames = ['resident', 'starttime', 'endtime',
                      'type_of_observation', 'guessed_situation',
                      'remarks', 'confidence']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if flag_new_file:
            logging.debug('Creating the CSV file')
            writer.writeheader()
        writer.writerow(label)


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <csv-file>' % sys.argv[0])
    init()
    for label in ask_for_labels():
        save(label)


if __name__ == '__main__':
    main()
