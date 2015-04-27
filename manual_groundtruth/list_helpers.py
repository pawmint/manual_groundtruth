from prompt_toolkit.contrib.shortcuts import get_input
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.contrib.completers import WordCompleter

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


def read_list(name, possible_values, default):
    _numbered_list = ['%d. %s' % (i, v)
                      for i, v in enumerate(possible_values, 1)]
    validator = ListValidator(possible_values, default)
    completer = WordCompleter(_numbered_list)

    answer = get_input(
        '%s?' % name
        + (' [default %s]' % (possible_values.index(default) + 1)
           if default is not None else '')
        + '\n(%s)' % ', '.join(_numbered_list)
        + '\n>> ',
        completer=completer, validator=validator)
    parsed_answer = parse_list_answer(answer, possible_values,
                                      default)
    return parsed_answer
