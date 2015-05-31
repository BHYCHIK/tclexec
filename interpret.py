# -*- coding: utf-8 -*-
from lexer import TclLexer, MultiToken
from parser import build_ast
from copy import deepcopy
from math import *

class Var(dict):
    def __init__(self, **args):
        self.__dict__.update(**args)

class RuntimeErrorException(Exception):
    pass

class TclString(object):
    def __init__(self, **args):
        self.__dict__.update(**args)
    def __repr__(self):
        return self.__dict__.__repr__()

class TclInterpretator(object):
    def __init__(self, source_code, context=None):
        self._source_code = source_code
        if context is None:
            self._context = dict()
            self._context['vars'] = dict()
        else:
            self._context = context

    def _generate_runtime_error(self, token, description):
        from lexer import format_tcl_error
        raise RuntimeErrorException(format_tcl_error(token.pos, self._source_code, description))

    def exec_subprogram(self, cur_token, subprogram_code):
        lexer = TclLexer(subprogram_code)
        tokens = list(self._fix_tokens_positions(cur_token.pos, lexer.get_tokens()))
        ast = build_ast(tokens)
        interp = TclInterpretator(source_code=self._source_code, context=deepcopy(self._context))
        ret = interp.execute(ast)
        self._context = interp._context # TODO: merge context for 'procs'
        return ret

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
            tokens = self._fix_tokens_positions(token.pos, lexer.get_tokens())
            ret_val = []
            for t in tokens:
                ret_val.append(self.expand_value(t))
            return ''.join(ret_val)
        if token.type == 'SUBSTITUTE_WORD':
            return self.exec_subprogram(token, token.value)

        assert 0, token

    def expand_value(self, token):
        if token.type == 'MULTI_WORD':
            assert token.subtokens
            return ''.join(self.expand_simple_value(sub_token) for sub_token in token.subtokens)
        r = self.expand_simple_value(token)
        assert r is not None
        return r

    def execute_command(self, cmd):
        args_list = []
        for arg in cmd['children']:
            arg_token = arg['value']
            if isinstance(arg_token, MultiToken) and arg_token.subtokens[0].type == 'EXPAND_WORD': # {*}
                if len(arg_token.subtokens) != 2:
                    self._generate_runtime_error(arg_token, 'invalid usage of {*}')
                words_token = arg_token.subtokens[1]
                lexer = TclLexer(self.expand_value(words_token))
                tokens = self._fix_tokens_positions(words_token.pos, lexer.get_tokens())
                new_strings = [TclString(value=self.expand_value(t), token=t) for t in tokens]
                args_list.extend(new_strings)
                continue
            string = TclString(value=self.expand_value(arg['value']), token=arg['value'])
            args_list.append(string)
        cmd_name = self.expand_value(cmd['value'])
        self_method_name = '_command_' + cmd_name
        if not hasattr(self, self_method_name):
            self._generate_runtime_error(cmd['value'], 'command "%s" doesn\'t exist' % cmd_name)
        return getattr(self, self_method_name)(cmd['value'], args_list)

    def _fix_tokens_positions(self, start_pos, tokens):
        for token in tokens:
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
            assert return_value is None or isinstance(return_value, basestring), type(return_value)
        return return_value

    def _command_set(self, token, args_list):
        if len(args_list) == 1:
            var = self._context['vars'].get(args_list[0].value)
            if var is None:
                self._generate_runtime_error(args_list[0].token, 'variable {} doesn\'t exist'.format(args_list[0].value))
            return var.value
        if len(args_list) != 2:
            self._generate_runtime_error(token, 'set command needs exactly 1 or 2 arguments. %d is given' % len(args_list))
        self._context['vars'][args_list[0].value] = Var(value=args_list[1].value, token=args_list[1].token)
        return args_list[1].value

    def _command_puts(self, token, args_list):
        #TODO Добавить проверку наличия переменной
        if len(args_list) != 1:
            self._generate_runtime_error(token, 'puts command needs exactly 2 arguments. %d is given' % len(args_list))
        print(args_list[0].value)

    def _command_expr(self, token, args_list):
        if not args_list:
            self._generate_runtime_error(token, 'expr command needs at least 1 argument')
        all_tokens = []
        for arg in args_list:
            lexer = TclLexer(arg.value)
            all_tokens.extend(self._fix_tokens_positions(arg.token.pos, lexer.get_tokens()))
        expanded_tokens = [self.expand_value(t) for t in all_tokens]
        eval_str = ''.join(expanded_tokens).replace('&&', ' and ').replace('||', ' or ')
        ret = eval(eval_str)
        if isinstance(ret, float):
            return '{:.16f}'.format(ret) # like in tclsh
        if isinstance(ret, bool):
            return '1' if ret else '0'
        return str(ret)
    def _command_if(self, token, args_list):
        if len(args_list) < 2:
            self._generate_runtime_error(token, 'if command needs at leat 2 arguments: condition and body')
        cond_expr = args_list.pop(0)
        cond_res = self._command_expr(token, (cond_expr,))
        if_body = args_list.pop(0)
        if cond_res != '0':
            return self.exec_subprogram(if_body.token, if_body.value)
        if not args_list:
            return None
        next_arg = args_list.pop(0)
        if next_arg.value == 'else':
            else_body = args_list.pop(0)
            if args_list:
                self._generate_runtime_error(args_list[0].token, 'too many arguments to "if" command')
            return self.exec_subprogram(else_body.token, else_body.value)
        if next_arg.value != 'elseif':
            self._generate_runtime_error(next_arg.token, 'invalid token, it should be "else" or "elseif"')
        return self._command_if(next_arg.token, args_list)
    def _command_incr(self, token, args_list):
        if len(args_list) != 1:
            self._generate_runtime_error(token, 'command "incr" accepts only 1 argument')
        var_name = args_list.pop()
        var_str_value = self._context['vars'].get(var_name.value, Var(value=0, token=None))
        try:
            var_int_value = int(var_str_value.value)
        except ValueError:
            self._generate_runtime_error(var_name.token,
                'variable "{}" value "{}" is not an integer, "incr" command can increment only integer'.format(var_name.value, var_str_value.value))
        var_int_value += 1
        self._context['vars'][var_name.value] = Var(value=str(var_int_value), token=var_str_value.token)
        return str(var_int_value)
    def _command_while(self, token, args_list):
        if len(args_list) != 2:
            self._generate_runtime_error(token, 'command "while" need 2 arguments: condition and body')
        cond_expr, body = args_list
        cond_res = self._command_expr(token, (cond_expr,))
        while cond_res != '0':
            self.exec_subprogram(body.token, body.value)
            cond_res = self._command_expr(token, (cond_expr,))
