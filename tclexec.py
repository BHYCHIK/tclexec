#!/usr/bin/env python3
import sys
from lexer import TclLexer, LexerException
from parser import build_ast, draw_ast

if __name__ == '__main__':
    data = sys.stdin.read()
    lexer = TclLexer(data)
    tokens = None
    try:
        tokens = list(lexer.get_tokens())
        for token in tokens:
            print(token)
    except LexerException as e:
        sys.stderr.write('invalid source code: {}\n'.format(e))
    ast = build_ast(tokens)
    print(ast)
    draw_ast(ast)
