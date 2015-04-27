#!/usr/bin/env python

from prompt_toolkit.contrib.shortcuts import get_input
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.contrib.completers import WordCompleter
import csv
import sys
import os.path
import logging

from manual_groundtruth import date_helpers, list_helpers


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


class ResidentValidator(Validator):
    def __init__(self, accepted_values, accept_empty=False):
        self.accepted_values = accepted_values
        if accept_empty:
            self.accepted_values.append('')

    def validate(self, document):
        if document.text not in self.accepted_values:
            raise ValidationError(message='Unknown resident',
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
    startime = date_helpers.read_date('Start time', default['starttime'])
    default['endtime'] = startime
    return startime


def read_endtime():
    endtime = date_helpers.read_date('End time', default['endtime'],
                                     accept_pasttime=False)
    default['starttime'] = endtime
    return endtime


def read_type_of_observation():
    observations_list = [
        'Correct inference',
        'Reasoning error',
        'Sensing error',
        'System failure',
        'Other'
    ]
    observation = list_helpers.read_list('Type of observation',
                                         observations_list, default['type'])
    default['type'] = observation
    return observation


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
    confidence = list_helpers.read_list('Confidence', confidence_list,
                                        default['confidence'])
    default['confidence'] = confidence
    return confidence


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
