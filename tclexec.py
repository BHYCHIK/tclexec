#!/usr/bin/env python3
import sys
import lexer 

if __name__ == '__main__':
    data = sys.stdin.read()
    parser = lexer.TclParser(data)
    try:
        for token in parser.get_tokens():
            print(token)
    except lexer.LexerException as e:
        sys.stderr.write('invalid source code: {}\n'.format(e))
