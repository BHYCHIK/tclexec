import re

class Token(object):
    def __init__(self, pos, type, value):
        self.pos = pos
        self.type = type
        self.value = value
    def __repr__(self):
        return 'Token(type={}, value={})'.format(self.type, self.value)

class MultiToken(Token):
    def __init__(self, pos, type, subtokens):
        self.pos = pos
        self.type = type
        self.subtokens = subtokens
    def __repr__(self):
        return 'MultiToken(type={}, subtokens={})'.format(self.type, self.subtokens)

class LexerException(Exception):
    pass

class TclParser(object):
    def __init__(self, data):
        self._data = data
        self._pos = 0

    def _parse_balanced_brackets(self, data, open_bracket, close_bracket):
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

            if data[pos] == open_bracket:
                counter += 1
                pos += 1
                continue

            if data[pos] == close_bracket:
                counter -= 1
                if counter == 0:
                    break
                pos += 1
                continue

            pos += 1
        if counter != 0:
            return self._raise_error('Unbalanced brackets found')
        return pos + 1

    def _parse_one_word(self):
        data = self._data[self._pos:]
        if data.startswith('$'):
            if len(data) == len('$'):
                return self._raise_error('unexpected end of input')
            if data[1] == '$':
                return self._raise_error('$$ is disallowed')
            self._pos += 1
            word = self._parse_one_word()
            if word is None:
                return self._raise_error('expected word after $')
            word.type = 'DOLLAR_WORD'
            return word

        if data.startswith('"'):
            m = re.match(r'^"(([^"\\]|\\.)*?)"', data)
            if m is None:
                return self._raise_error('Unterminated string')
            self._pos += len(m.group(0))
            return Token(pos=self._pos, type='QUOTED_WORD', value=m.group(1))

        if data.startswith('['):
            sub_len = self._parse_balanced_brackets(data, '[', ']')
            self._pos += sub_len
            return Token(pos=self._pos, type='SUBSTITUTE_WORD', value=data[1:sub_len-1])

        if data.startswith('{'):
            if data.startswith('{*}'):
                self._pos += len('{*}')
                return Token(pos=self._pos, type='EXPAND_WORD', value='{*}')
            fig_len = self._parse_balanced_brackets(data, '{', '}')
            self._pos += fig_len
            return Token(pos=self._pos, type='FIGURE_WORD', value=data[1:fig_len-1])

        m = re.match(r'^([^\s;$#]+)', data)
        if m:
            self._pos += len(m.group(0))
            return Token(pos=self._pos, type='SIMPLE_WORD', value=m.group(0))

        return None

    def _parse_multiword(self):
        words = []
        first_pos = self._pos
        while True:
            w = self._parse_one_word()
            if w is None:
                break
            words.append(w)
        if not words:
            return None
        if len(words) == 1:
            return words[0]
        return MultiToken(pos=first_pos, type='MULTI_WORD', subtokens=tuple(words))

    def _parse_comment(self):
        t = Token(pos=self._pos, type='COMMENT', value=None)
        res = []
        while len(self._data[self._pos:]):
            m = re.match(r'^((?:\\.|[^\\\n])*)(\\)?(\n|$)', self._data[self._pos:])
            assert m is not None
            res.append(m.group(1))
            self._pos += len(m.group(0))
            if m.group(2) is None: # comment doesn't continue on the next line
                break
        t.value = ''.join(res)
        return t

    def _raise_error(self, desc):
        data_lfs = tuple(m.start() for m in re.finditer('\n', self._data))
        line_n = line_pos = None
        for i, lf_pos in enumerate(data_lfs):
            assert self._pos != lf_pos # can't be error on LF
            if self._pos > lf_pos:
                line_n = i + 2
                line_pos = self._pos - lf_pos
                continue
            break
        if line_n is None:
            line_n = 1
            line_pos = lf_pos + 1

        raise LexerException('Line: {}, position: {}, character: "{}", error: {}'.format(
            line_n, line_pos, self._data[self._pos], desc))
    def get_tokens(self):
        data_len = len(self._data)
        while self._pos < data_len:
            if self._data[self._pos] == '#':
                self._pos += 1
                yield self._parse_comment()
                continue
            word = self._parse_multiword()
            if word is not None:
                yield word
                continue
            if self._data[self._pos] in ('\n', ';'):
                yield Token(pos=self._pos, type='END_OF_STATEMENT', value=self._data[self._pos])
                self._pos += 1
                continue
            if self._data[self._pos] in (' ', '\f', '\t'):
                self._pos += 1
                continue
            return self._raise_error('unknown character')
