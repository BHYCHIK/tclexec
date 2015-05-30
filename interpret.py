# -*- coding: utf-8 -*-
from lexer import TclLexer
from parser import build_ast

class Var(dict):
    def __init__(self, **args):
        self.__dict__.update(**args)

class RuntimeErrorException(Exception):
    pass

def _generate_runtime_error(token, description, context):
    raise RuntimeErrorException(description)

def _command_set(token, args_list, context):
    if len(args_list) == 1:
        return context['vars'][args_list[0]].value
    if len(args_list) != 2:
        _generate_runtime_error(token, 'set command needs exactly 1 or 2 arguments. %d is given' % len(args_list), context)
    context['vars'][args_list[0]] = Var(value=args_list[1])
    return args_list[1]

def _command_puts(token, args_list, context):
    #TODO Добавить проверку наличия переменной
    if len(args_list) != 1:
        _generate_runtime_error(token, 'puts command needs exactly 2 arguments. %d is given' % len(args_list), context)
    print(args_list[0])

instractions_procs = {
        'set': _command_set,
        'puts': _command_puts,
        }

def exec_subprogram(subprogram_code, context):
    lexer = TclLexer(subprogram_code)
    tokens = list(lexer.get_tokens())
    ast = build_ast(tokens)
    return execute(ast, context)

def expand_simple_value(token, context):
    if token.type in ('FIGURE_WORD', 'SIMPLE_WORD'):
        return token.value
    if token.type == 'DOLLAR_WORD':
        var = context['vars'].get(token.value)
        if var is None:
            _generate_runtime_error(token, 'expand variable %s doesn\'t exist' % token.value, context)
        return var.value
    if token.type == 'QUOTED_WORD':
        lexer = TclLexer(token.value, in_quoted_context=True)
        tokens = lexer.get_tokens()
        ret_val = []
        for t in tokens:
            ret_val.append(expand_value(t, context))
        return ''.join(ret_val)
    if token.type == 'SUBSTITUTE_WORD':
        return exec_subprogram(token.value, context)

    assert 0


def expand_value(token, context):
    #Need more complicated expanding
    r = expand_simple_value(token, context)
    assert r is not None
    return r

def execute_command(cmd, context):
    args_list = []
    for arg in cmd['children']:
        args_list.append(expand_value(arg['value'], context))
    cmd_name = expand_value(cmd['value'], context)
    proc = instractions_procs.get(cmd_name)
    if proc is None:
        _generate_runtime_error(cmd['value'], 'command %s doesn\'t exist' % cmd_name, context)
    return proc(arg['value'], args_list, context)

def execute(ast, context=None):
    if context is None:
        context = dict()
        context['vars'] = dict()
    return_value = None
    for cmd in ast['children']:
        #print('command: %s %s' % (cmd['value'].value, ' '.join(a['value'].value for a in cmd['children'])))
        return_value = execute_command(cmd, context)
        #print '%s: %s' % (cmd['value'].value, return_value)
        assert return_value is None or isinstance(return_value, basestring)
    return return_value
