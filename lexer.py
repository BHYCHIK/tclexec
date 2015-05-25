import re

class LexerException(Exception):
    pass

class TclParser(object):
    def __init__(self, data):
        self._data = data
        self._pos = 0
        self._line_n = 1
        self._line_start_pos = 0

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
        return pos + 2

    def _parse_word(self, data):
        if data.startswith('"'):
            m = re.match(r'^"(([^"]|\\.)*?)"', data)
            if m is None:
                return self._raise_error('Unterminated string')
            return ('QUOTED_WORD', m.group(0))

        if data.startswith('['):
            sub_len = self._parse_balanced_brackets(data, '[', ']')
            return ('SUBSTITUTE_WORD', data[:sub_len])

        if data.startswith('{'):
            if data.startswith('{*}'):
                return ('EXPAND_WORD', '{*}')
            fig_len = self._parse_balanced_brackets(data, '{', '}')
            return ('FIGURE_WORD', data[:fig_len])

        m = re.match(r'^([^\s;$#]+)', data)
        if m:
            return ('SIMPLE_WORD', m.group(0))

        return None

    def _parse_comment(self):
        res = []
        while len(self._data[self._pos:]):
            m = re.match(r'^((?:\\.|[^\\\n])*)(\\)?(\n|$)', self._data[self._pos:])
            assert m is not None
            res.append(m.group(1))
            self._pos += len(m.group(0))
            if m.group(3) == '\n':
                self._start_new_line()
            if m.group(2) is None: # comment doesn't continue on the next line
                break
        return ''.join(res)

    def _start_new_line(self):
        self._line_n += 1
        self._line_start_pos = self._pos
    def _raise_error(self, desc):
        raise LexerException('Line: {}, position: {}, character: "{}", error: {}'.format(
            self._line_n, self._pos - self._line_start_pos, self._data[self._pos], desc))
    def get_tokens(self):
        data_len = len(self._data)
        while self._pos < data_len:
            if self._data[self._pos] == '#':
                self._pos += 1
                comment = self._parse_comment()
                yield ('COMMENT', comment)
                continue
            if self._data[self._pos] == '$':
                yield ('EXPAND_SYMBOL', '$')
                self._pos += 1
                continue
            word = self._parse_word(self._data[self._pos:])
            if word is not None:
                self._pos += len(word[1])
                if word[0] in ('QUOTED_WORD', 'SUBSTITUTE_WORD', 'FIGURE_WORD'):
                    word = (word[0], word[1][1:-1])
                yield word
                continue
            if self._data[self._pos] in ('\n', ';'):
                if self._data[self._pos] == '\n':
                    self._start_new_line()
                yield ('END_OF_STATEMENT', self._data[self._pos])
                self._pos += 1
                continue
            if self._data[self._pos] in (' ', '\n', '\f', '\t'):
                self._pos += 1
                continue
            return self._raise_error('unknown character')
