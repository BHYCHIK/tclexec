#!/usr/bin/env python3
import sys
from lexer import TclLexer, LexerException

if __name__ == '__main__':
    data = sys.stdin.read()
    lexer = TclLexer(data)
    try:
        for token in lexer.get_tokens():
            print(token)
    except LexerException as e:
        sys.stderr.write('invalid source code: {}\n'.format(e))
