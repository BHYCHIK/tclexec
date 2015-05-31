import re

class Token(object):
    def __init__(self, pos, type, value):
        self.pos = pos
        self.type = type
        self.value = value
    def __str__(self):
        return 'val: {}, type: {}'.format(self.value, self.type)
    def __repr__(self):
        return 'Token(type={}, value={}, pos={})'.format(self.type, self.value, self.pos)
    def get_id(self):
        return '{}:{}'.format(self.value, self.pos)

class MultiToken(Token):
    def __init__(self, pos, type, subtokens):
        self.pos = pos
        self.type = type
        self.subtokens = subtokens
        self.value = 'MultiToken'
    def __repr__(self):
        return 'MultiToken(type={}, subtokens={})'.format(self.type, self.subtokens)

def format_tcl_error(pos, source_code, err_desc):
    line_n, line_pos, line = get_line_from_pos(pos, source_code)
    err_text = 'Line: {}, position: {}: {}'.format(line_n, line_pos, err_desc)
    marked_line = (' ' * (line_pos - 1) if line_pos else '') + '^'
    return '\n'.join((err_text, line, marked_line))

class LexerException(Exception):
    pass

def get_line_from_pos(pos, source_code):
    """
    >>> get_line_from_pos(0, "a\\nb\\nc")
    (1, 1, 'a')
    >>> get_line_from_pos(1, "abc")
    (1, 2, 'abc')
    >>> get_line_from_pos(2, "a\\nbc")
    (2, 1, 'bc')
    >>> get_line_from_pos(4, "ab\\ncde\\nfg")
    (2, 2, 'cde')
    """
    data_lfs = tuple(m.start() for m in re.finditer('\n', source_code))
    line_n = 1
    line_pos = pos + 1
    lf_pos = 0
    for i, lf_pos in enumerate(data_lfs):
        assert pos != lf_pos, (pos, lf_pos) # can't be error on LF
        if pos > lf_pos:
            line_n = i + 2
            line_pos = pos - lf_pos
            continue
        line = source_code[data_lfs[i-1]+1:data_lfs[i]] if i != 0 else source_code[:data_lfs[i]]
        return line_n, line_pos, line
    # error after last LF
    line = source_code[data_lfs[line_n-2]+1:] if data_lfs else source_code
    return line_n, line_pos, line

class TclLexer(object):
    def __init__(self, data, in_quoted_context=False):
        self._data = data
        self._pos = 0
        self._in_quoted_context = in_quoted_context

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
            t = Token(pos=self._pos+len('"'), type='QUOTED_WORD', value=m.group(1))
            self._pos += len(m.group(0))
            return t

        if data.startswith('['):
            sub_len = self._parse_balanced_brackets(data, '[', ']')
            t = Token(pos=self._pos+len('['), type='SUBSTITUTE_WORD', value=data[1:sub_len-1])
            self._pos += sub_len
            return t

        if data.startswith('{') and not self._in_quoted_context:
            if data.startswith('{*}'):
                t = Token(pos=self._pos, type='EXPAND_WORD', value='{*}')
                self._pos += len('{*}')
                return t
            fig_len = self._parse_balanced_brackets(data, '{', '}')
            t = Token(pos=self._pos+len('{'), type='FIGURE_WORD', value=data[1:fig_len-1])
            self._pos += fig_len
            return t

        m = None
        simple_word_separators = r'^\s;$#\['
        if not self._in_quoted_context:
            simple_word_separators += r'\{'
        m = re.match(r'^([' + simple_word_separators + r']+)', data)
        if m:
            t = Token(pos=self._pos, type='SIMPLE_WORD', value=m.group(0))
            self._pos += len(m.group(0))
            return t

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
        raise LexerException(format_tcl_error(self._pos, self._data, desc))
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
                if self._in_quoted_context:
                    yield Token(pos=self._pos, type='SIMPLE_WORD', value=self._data[self._pos])
                else:
                    yield Token(pos=self._pos, type='END_OF_STATEMENT', value=self._data[self._pos])
                self._pos += 1
                continue
            if self._data[self._pos] in (' ', '\f', '\t'):
                if self._in_quoted_context:
                    m = re.match(r'^\s+', self._data[self._pos:])
                    assert m
                    yield Token(pos=self._pos, type='SIMPLE_WORD', value=m.group(0))
                    self._pos += len(m.group(0))
                    continue
                self._pos += 1
                continue

            raise self._raise_error('unknown character')

if __name__ == '__main__':
    import doctest
    doctest.testmod()
