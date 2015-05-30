#!/usr/bin/env python
import sys
from lexer import TclLexer, LexerException
from parser import build_ast, draw_ast
from pprint import PrettyPrinter
from interpret import execute

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
    #p = PrettyPrinter(indent=2)
    #p.pprint(ast)
    #draw_ast(ast)
    execute(ast)
