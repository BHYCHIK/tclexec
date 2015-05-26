import pygraphviz as pgv

def gen_command_node(command, args):
    return {'value': command, 'children': args}

def build_ast(tokens):
    command_read = False
    commands = []
    command = None
    args = []
    for token in tokens:
        if token.type == 'COMMENT':
            continue

        if token.type == 'END_OF_STATEMENT':
            if not command_read:
                continue
            command_read = False
            commands.append(gen_command_node(command, args))
            args = []
            command = None
            continue

        if not command_read:
            command = token
            command_read = True
        else:
            args.append(token)
    
    return {'value': 'Program', 'children': commands}
        
def draw_ast(ast):
    G=pgv.AGraph()
    G.add_node(ast['value'])
    root_node = G.get_node(ast['value'])
    for command in ast['children']:
        G.add_node(command['value'].value)
        cmd_node = G.get_node(command['value'].value)
        G.add_edge(root_node, cmd_node)
    G.draw('/home/denis/Desktop/ast.png')
       
