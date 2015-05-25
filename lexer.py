import re

class Token():
    pass

class LexerException(Exception):
    pass

def parse_word(data):
    m = re.match(r'^([a-zA-Z0-9]+)', data)
    if m:
        return ('SIMPLE_WORD', m.group(0))

    m = re.match(r'^"(.*?[^\\])"', data)
    if m:
        return ('QUOTED_WORD', m.group(0))

    if data.startswith('['):
        pos = 1
        counter = 1
        escaped = False
        while (counter != 0) and (pos < len(data)):
            if escaped:
                escaped = False
                pos += 1
                continue

            if data[pos] == '\\':
                escaped = True
                pos += 1
                continue

            if data[pos] == '[':
                counter += 1
                pos += 1
                continue

            if data[pos] == ']':
                counter -= 1
                if counter == 0:
                    break
                pos += 1
                continue

            pos += 1
        return ('SUBSTITUTE_WORD', data[:pos+1])
    
    if data.startswith('{'):
        pos = 1
        counter = 1
        escaped = False
        while (counter != 0) and (pos < len(data)):
            if escaped:
                escaped = False
                pos += 1
                continue

            if data[pos] == '\\':
                escaped = True
                pos += 1
                continue

            if data[pos] == '{':
                counter += 1
                pos += 1
                continue

            if data[pos] == '}':
                counter -= 1
                if counter == 0:
                    break
                pos += 1
                continue

            pos += 1
        return ('FIGURE_WORD', data[:pos+1])


def get_tokens(data):
    position = 0
    data_len = len(data)
    while position < data_len:
        word = parse_word(data[position:])
        if word is not None:
            position += len(word[1])
            if word[0] != 'SIMPLE_WORD':
                word = (word[0], word[1][1:-1])
            yield word
            continue
        if data[position] in ('\n', ';'):
            yield ('END_OF_STATEMENT', data[position])
            position += 1
            continue
        if data[position] in (' ', '\n', '\f', '\t'):
            position += 1
            continue
        if data[position] == '$':
            yield ('EXPAND_SYMBOL', '$')
            position += 1
            continue
        raise LexerException(data[position])

