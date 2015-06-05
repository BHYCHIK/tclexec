#!/usr/bin/env python
import sys
from lexer import TclLexer, LexerException
from parser import build_ast, draw_ast
from pprint import PrettyPrinter
from interpret import TclInterpretator, RuntimeErrorException

if __name__ == '__main__':
    data = sys.stdin.read()
    lexer = TclLexer(data)
    tokens = None
    try:
        tokens = list(lexer.get_tokens())
    except LexerException as e:
        sys.exit(e)
    ast = build_ast(tokens)
    #p = PrettyPrinter(indent=2)
    #p.pprint(ast)
    draw_ast(ast)
    try:
        interp = TclInterpretator(data)
        interp.execute(ast)
    except RuntimeErrorException as ex:
        sys.stderr.write(ex.message + '\n')
