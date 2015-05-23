import sys
import lexer 

if __name__ == '__main__':
    data = sys.stdin.read()
    tokens = list(lexer.get_tokens(data))
    for token in tokens:
        print(token)
