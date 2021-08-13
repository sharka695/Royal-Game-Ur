from typing import NamedTuple
import re

# https://docs.python.org/3/library/re.html#writing-a-tokenizer

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int
    
def tokenize(user_input):
    keywords = {
        'quit',
        'multiplayer',
        'host',
        'guest',
        'skip',
        'board',
        'help',
        'play',
        'piece',
        'space',
        'yes',
        'no'
    }
    token_specification = [
        ('NUMBER',      r'-?\d+(\.\d*)?'  ),  # int or decimal
        ('ASSIGN',      r'='            ),  # Assignment operator
        ('END',         r';'            ),  # Statement terminator
        ('ID',          r'[A-Za-z]+'    ),  # Identifiers
        ('NEWLINE',     r'\n'           ),  # Line ending
        ('SKIP',        r'[ \t]+'       ),  # Skip spaces, tabs
        ('MISMATCH',    r'.'            ),  # Anything else
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, user_input):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
        elif kind == 'ID' and value.lower() in keywords:
            kind = value.lower()
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            continue
        yield Token(kind, value, line_num, column)

def parse(arg):
    arg = tokenize(arg)
    prev = None
    for token in arg:
        if token.value == 'quit':
            return token.value
        elif token.value == 'multiplayer':
            return token.value
        elif token.value == 'host':
            return token.value
        elif token.value == 'guest':
            return token.value
        elif token.value == 'play':
            return token.value
        elif token.value == 'skip':
            return token.value
        elif token.value == 'board':
            return token.value
        elif token.value == 'help':
            return token.value
        elif token.value == 'yes':
            return True
        elif token.value == 'no':
            return False
        elif token.value == 'piece':
            prev = token
            continue
        elif token.value == 'space':
            prev = token
            continue
        elif token.type == 'NUMBER':
            return (prev, token.value)
        else:
            return token.value
    return
    
def interpret(game, arg):
    arg = self.parse(arg)
    if type(arg) is bool:
        return arg
    elif type(arg) is tuple:
        try:
            func = getattr(game, 'do_' + arg[0])
        except AttributeError:
            print("I can't do that.")
        return func(arg[1])
        