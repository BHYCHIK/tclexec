class RuntimeErrorException(Exception):
    pass

def _generate_runtime_error(token, description, context):
    raise RuntimeErrorException(description)

def _command_set(token, args_list, context):
    if len(args_list) != 2:
        _generate_runtime_error(token, 'set command needs exactly 2 arguments. %d is given' % len(args_list), context)
    context['vars'][args_list[0]] = args_list[1]

def _command_puts(token, args_list, context):
    if len(args_list) != 1:
        _generate_runtime_error(token, 'puts command needs exactly 2 arguments. %d is given' % len(args_list), context)
    print(args_list[0])

instractions_procs = {
        'set': _command_set,
        'puts': _command_puts,
        }

def expand_value(token, context):
    #Need more complicated expanding
    return token.value

def execute_command(cmd, context):
    args_list = []
    for arg in cmd['children']:
        args_list.append(expand_value(arg['value'], context))
    instractions_procs[expand_value(cmd['value'], context)](arg['value'], args_list, context)

def execute(ast, context=None):
    if context is None:
        context = dict()
        context['vars'] = dict()
    return_value = None
    for cmd in ast['children']:
        return_value = execute_command(cmd, context)
