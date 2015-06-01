from lexer import MultiToken
import pygraphviz as pgv

def gen_command_node(command, args):
    return {'value': command, 'children': args}

def build_ast(tokens):
    command_read = False
    commands = []
    command = None
    args = []

    def build_statement(args, command):
        command_args = []
        for arg in args:
            if isinstance(arg, MultiToken):
                cmd_arg = {'value': arg, 'children': tuple({'value': a, 'children': ()} for a in arg.subtokens)}
            else:
                cmd_arg = {'value': arg, 'children': ()}
            command_args.append(cmd_arg)
        commands.append(gen_command_node(command, tuple(command_args)))

    for token in tokens:
        if token.type == 'COMMENT':
            continue

        if token.type == 'END_OF_STATEMENT':
            if not command_read:
                continue
            command_read = False
            build_statement(args, command)
            args = []
            command = None
            continue

        if not command_read:
            command = token
            command_read = True
        else:
            args.append(token)
    if command_read:
        build_statement(args, command)

    return {'value': 'Program', 'children': commands}

def create_node(g, value, label):
    g.add_node(value)
    n = g.get_node(value)
    n.attr['label'] = label
    return n

def draw_ast(ast):
    G=pgv.AGraph()
    root_node = create_node(G, 'Program', None)
    for command in ast['children']:
        cmd_node = create_node(G, command['value'].get_id(), command['value'])
        G.add_edge(root_node, cmd_node)
        for arg in command['children']:
            arg_node = create_node(G, arg['value'].get_id() , arg['value'])
            G.add_edge(cmd_node, arg_node)

            subargs = arg.get('children', ())
            for subarg in subargs:
                subarg_node = create_node(G, subarg['value'].get_id(), subarg['value'])
                G.add_edge(arg_node, subarg_node)
    G.layout(prog='dot')
    G.draw('ast.dot')
    G.draw('ast.png')
