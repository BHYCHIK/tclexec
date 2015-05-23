import ply.lex as lex
import re

tokens = (
    'TCL_WORD',
    'TCL_OPEN_CURLY_BRACE',
    'TCL_CLOSE_CURLY_BRACE',
    'TCL_OPEN_SQUARE_BRACE',
    'TCL_CLOSE_SQUARE_BRACE',
    'TCL_COMMENT',
    'TCL_EXTENSION_OPERATOR',
    'TCL_DOLLAR',
    'TCL_DOLLAR_BRACE',
    'TCL_END_OF_STATEMENT',
    'TCL_ESCAPE_SYMBOL',
    'TCL_QUOTE',
    )

t_TCL_WORD = r'[^{}$[\]#;"\n]+'
t_TCL_OPEN_CURLY_BRACE = r'\{'
t_TCL_CLOSE_CURLY_BRACE = r'}'
t_TCL_OPEN_SQUARE_BRACE = r'\['
t_TCL_CLOSE_SQUARE_BRACE = r']'
t_TCL_COMMENT = r'\#'
t_TCL_EXTENSION_OPERATOR = r'\{\*\}'
t_TCL_DOLLAR = '\$'
t_TCL_DOLLAR_BRACE = r'\$\{'
t_TCL_END_OF_STATEMENT = r'\n|;'
t_TCL_QUOTE = r'"'

t_ignore = ' \t\r\f'

def t_error(t):
    print(t)
    print('Illegal character \'%s\'' % t.value[0])
    t.lexer.skip(1)

def get_tokens(data):
    lexer = lex.lex(reflags=re.UNICODE | re.DOTALL)
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            return
        yield tok
