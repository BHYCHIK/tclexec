# -*- coding: utf-8 -*-
from lexer import TclLexer
from parser import build_ast
from copy import deepcopy

class Var(dict):
    def __init__(self, **args):
        self.__dict__.update(**args)

class RuntimeErrorException(Exception):
    pass

class TclString(object):
    def __init__(self, **args):
        self.__dict__.update(**args)

class TclInterpretator(object):
    def __init__(self, source_code, context=None):
        self._source_code = source_code
        if context is None:
            self._context = dict()
            self._context['vars'] = dict()
        else:
            self._context = context

    def _generate_runtime_error(self, token, description):
        from lexer import get_line_from_pos
        line_n, line_pos = get_line_from_pos(token.pos, self._source_code)
        text = 'Line: {}, position: {}: {}'.format(line_n, line_pos, description)
        raise RuntimeErrorException(text)

    def exec_subprogram(self, subprogram_code):
        lexer = TclLexer(subprogram_code)
        tokens = list(lexer.get_tokens())
        ast = build_ast(tokens)
        return self.execute(ast)

    def expand_simple_value(self, token):
        if token.type in ('FIGURE_WORD', 'SIMPLE_WORD'):
            return token.value
        if token.type == 'DOLLAR_WORD':
            var = self._context['vars'].get(token.value)
            if var is None:
                self._generate_runtime_error(token, 'expand variable %s doesn\'t exist' % token.value)
            return var.value
        if token.type == 'QUOTED_WORD':
            lexer = TclLexer(token.value, in_quoted_context=True)
            print('quoted pos ' + str(token.pos))
            tokens = self._fix_tokens_positions(token.pos, lexer.get_tokens())
            ret_val = []
            for t in tokens:
                ret_val.append(self.expand_value(t))
            return ''.join(ret_val)
        if token.type == 'SUBSTITUTE_WORD':
            return self.exec_subprogram(token.value)

        assert 0

    def expand_value(self, token):
        #Need more complicated expanding
        if token.type == 'MULTI_WORD':
            return ''.join(self.expand_simple_value(sub_token) for sub_token in token.subtokens)
        r = self.expand_simple_value(token)
        assert r is not None
        return r

    def execute_command(self, cmd):
        args_list = []
        for arg in cmd['children']:
            string = TclString(value=self.expand_value(arg['value']), token=arg['value'])
            args_list.append(string)
        cmd_name = self.expand_value(cmd['value'])
        self_method_name = '_command_' + cmd_name
        if not hasattr(self, self_method_name):
            self._generate_runtime_error(cmd['value'], 'command %s doesn\'t exist' % cmd_name)
        return getattr(self, self_method_name)(cmd['value'], args_list)

    def _fix_tokens_positions(self, start_pos, tokens):
        for token in tokens:
            print('fix token {} pos: {} -> {}'.format(token.value, token.pos, token.pos + start_pos))
            new_token = deepcopy(token)
            new_token.pos += start_pos
            if token.type == 'MULTI_WORD':
                for t in new_token.subtokens:
                    t.pos += start_pos
            yield new_token

    def execute(self, ast):
        return_value = None
        for cmd in ast['children']:
            #print('command: %s %s' % (cmd['value'].value, ' '.join(a['value'].value for a in cmd['children'])))
            return_value = self.execute_command(cmd)
            #print '%s: %s' % (cmd['value'].value, return_value)
            assert return_value is None or isinstance(return_value, basestring)
        return return_value

    def _command_set(self, token, args_list):
        if len(args_list) == 1:
            return self._context['vars'][args_list[0]].value
        if len(args_list) != 2:
            self._generate_runtime_error(token, 'set command needs exactly 1 or 2 arguments. %d is given' % len(args_list))
        self._context['vars'][args_list[0].value] = Var(value=args_list[1].value, token=args_list[1].token)
        return args_list[1].value

    def _command_puts(self, token, args_list):
        #TODO Добавить проверку наличия переменной
        if len(args_list) != 1:
            self._generate_runtime_error(token, 'puts command needs exactly 2 arguments. %d is given' % len(args_list))
        print(args_list[0].value)
