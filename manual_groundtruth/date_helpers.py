import arrow
from prompt_toolkit.contrib.shortcuts import get_input
from prompt_toolkit.validation import Validator, ValidationError
import re
import datetime


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


def read_date(name, default, accept_pasttime=True):
    date = get_input('%s? (? for help) ' % name
                     + ('[default "%s"] ' % default[:19]
                        if default is not None else '')
                     + '>> ',
                     validator=DateValidator(default, accept_pasttime))
    if date == '?':
        print("---")
        _print_date_format_helper(default)
        print("---")
        return read_date(name, default, accept_pasttime)
    else:
        parsed_date = parse_date(date, default, accept_pasttime)
        return parsed_date
