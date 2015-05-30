from lexer import TclLexer

class Var(dict):
    def __init__(self, **args):
        self.__dict__.update(**args)

class RuntimeErrorException(Exception):
    pass

def _generate_runtime_error(token, description, context):
    raise RuntimeErrorException(description)

def _command_set(token, args_list, context):
    if len(args_list) != 2:
        _generate_runtime_error(token, 'set command needs exactly 2 arguments. %d is given' % len(args_list), context)
    context['vars'][args_list[0]] = Var(value=args_list[1])

def _command_puts(token, args_list, context):
    if len(args_list) != 1:
        _generate_runtime_error(token, 'puts command needs exactly 2 arguments. %d is given' % len(args_list), context)
    print(args_list[0])

instractions_procs = {
        'set': _command_set,
        'puts': _command_puts,
        }

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
    assert 0


def expand_value(token, context):
    #Need more complicated expanding
    return expand_simple_value(token, context)

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
        return_value = execute_command(cmd, context)
