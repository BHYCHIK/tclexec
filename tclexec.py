#!/usr/bin/env python3
import sys
import lexer 

if __name__ == '__main__':
    data = sys.stdin.read()
    parser = lexer.TclParser(data)
    for token in parser.get_tokens():
        print(token)
