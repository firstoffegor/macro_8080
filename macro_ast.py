from enum import Enum, auto

from token_class import Token, Tokentype


class NodeType(Enum):
    program = auto()       # root of the whole tree
    flow_control = auto()  # while ...
    expression = auto()    # the "test" of a flow-control node
    statement = auto()     # "=", "return", or a "body" holding statements
    function = auto()      # function definition
    func_name = auto()     # the name in a function definition
    func_call = auto()
    op = auto()
    var_name = auto()
    literal = auto()
    type = auto()


class Node:
    def __init__(self, value: str, node_type: NodeType, children=None, parent=None,
                 tokens=None, resolved: bool = True):
        self.value = value           # Token name/value (e.g., "=", "+", "a", "int")
        self.node_type = node_type   # What this node *is* in the tree
        self.children = children if children is not None else []
        self.parent = parent
        # A drafted node keeps its not-yet-parsed tokens and resolved=False
        # until its children have been built.
        self.tokens = tokens if tokens is not None else []
        self.resolved = resolved

    def add_child(self, child_node: "Node"):
        if child_node:
            child_node.parent = self
            self.children.append(child_node)

    def __repr__(self):
        if self.children:
            return f"Node('{self.value}', type={self.node_type.name}, children={len(self.children)})"
        return f"Node('{self.value}', type={self.node_type.name})"


class AST:
    def __init__(self, root: Node | None = None):
        self.root = root

    def __repr__(self):
        return f"AST(root={self.root})"


# How a single token becomes a node.
NODE_TYPE_FOR_TOKEN = {
    Tokentype.literal: NodeType.literal,
    Tokentype.variable_name: NodeType.var_name,
    Tokentype.func_name: NodeType.func_call,
    Tokentype.aop: NodeType.op,
    Tokentype.type: NodeType.type,
    Tokentype.binding: NodeType.statement,
    Tokentype.ret: NodeType.statement,
    Tokentype.func: NodeType.function,
    Tokentype.flow_control: NodeType.flow_control,
}


def node_from_token(token: Token) -> Node:
    node_type = NODE_TYPE_FOR_TOKEN.get(token.token_type)
    if node_type is None:
        raise ValueError(f"unexpected token {token.name!r} ({token.token_type.name})")
    return Node(token.name, node_type)


# Higher number = binds tighter.
PRECEDENCE = {
    "||": 0, "or": 0,
    "&&": 1, "and": 1,
    "<": 2, ">": 2, "<=": 2, ">=": 2, "==": 2, "!=": 2,
    "+": 3, "-": 3,
    "*": 4, "/": 4, "//": 4, "%": 4,
    "**": 5,
}
RIGHT_ASSOCIATIVE = {"**"}


def parse_expression(token_list: list[Token]) -> Node | None:
    if not token_list:
        return None

    # Strip outer matching parentheses if whole expression is wrapped in them
    if token_list[0].token_type == Tokentype.open_p and token_list[-1].token_type == Tokentype.closed_p:
        depth = 0
        matches = True
        for idx, t in enumerate(token_list):
            if t.token_type == Tokentype.open_p:
                depth += 1
            elif t.token_type == Tokentype.closed_p:
                depth -= 1
            if depth == 0 and idx < len(token_list) - 1:
                matches = False
                break
        if matches:
            return parse_expression(token_list[1:-1])

    # 1. Look for binary operators outside of nested parentheses
    split_idx = -1
    lowest_prec = float('inf')
    depth = 0

    for idx in range(len(token_list) - 1, -1, -1):
        token = token_list[idx]
        if token.token_type == Tokentype.closed_p:
            depth += 1
        elif token.token_type == Tokentype.open_p:
            depth -= 1
        elif depth == 0 and token.token_type == Tokentype.aop:
            prec = PRECEDENCE.get(token.name, 1)
            # Scanning right to left: "<" picks the rightmost operator of the
            # lowest precedence (left-associative); "**" is right-associative,
            # so on a tie we keep moving left to pick the leftmost one.
            if prec < lowest_prec or (prec == lowest_prec and token.name in RIGHT_ASSOCIATIVE):
                lowest_prec = prec
                split_idx = idx

    if split_idx != -1:
        op_node = node_from_token(token_list[split_idx])

        left_node = parse_expression(token_list[:split_idx])
        right_node = parse_expression(token_list[split_idx + 1:])

        if left_node:
            op_node.add_child(left_node)
        if right_node:
            op_node.add_child(right_node)

        return op_node

    # 2. Match function calls: func_name(...)
    if token_list[0].token_type == Tokentype.func_name and len(token_list) > 1 and token_list[1].token_type == Tokentype.open_p:
        func_node = node_from_token(token_list[0])

        inner_tokens = token_list[2:-1] if token_list[-1].token_type == Tokentype.closed_p else token_list[2:]

        # Split args by commas at the top-level depth
        args_lists = []
        curr_arg = []
        depth = 0
        for t in inner_tokens:
            if t.token_type == Tokentype.open_p:
                depth += 1
                curr_arg.append(t)
            elif t.token_type == Tokentype.closed_p:
                depth -= 1
                curr_arg.append(t)
            elif t.token_type == Tokentype.comma and depth == 0:
                if curr_arg:
                    args_lists.append(curr_arg)
                    curr_arg = []
            else:
                curr_arg.append(t)
        if curr_arg:
            args_lists.append(curr_arg)

        for arg_tokens in args_lists:
            arg_node = parse_expression(arg_tokens)
            if arg_node:
                func_node.add_child(arg_node)

        return func_node

    # 3. Base case: single token
    return node_from_token(token_list[0])


def build_statement_ast(tokens: list[Token]) -> Node | None:
    if not tokens:
        return None

    # --- STATEMENT ROUTING ---

    # 1. Function Definition ("function some_func...")
    if tokens[0].token_type == Tokentype.func:
        func_node = node_from_token(tokens[0])

        name_node = Node(tokens[1].name, NodeType.func_name)
        func_node.add_child(name_node)

        param_idx = 2
        while param_idx < len(tokens) and tokens[param_idx].token_type != Tokentype.closed_p:
            t = tokens[param_idx]
            if t.token_type in (Tokentype.variable_name, Tokentype.type):
                name_node.add_child(node_from_token(t))
            param_idx += 1

        return func_node

    # 2. Return Statements ("return a + b")
    if tokens[0].token_type == Tokentype.ret:
        return_node = node_from_token(tokens[0])

        expr_node = parse_expression(tokens[1:])
        if expr_node:
            return_node.add_child(expr_node)

        return return_node

    # 3. Variable Assignment / Declaration (Contains "=")
    binding_idx = -1
    for idx, token in enumerate(tokens):
        if token.token_type == Tokentype.binding:
            binding_idx = idx
            break

    if binding_idx != -1:
        if binding_idx == 0:
            raise ValueError("assignment is missing a target before '='")
        assignment_node = node_from_token(tokens[binding_idx])

        var_node = node_from_token(tokens[binding_idx - 1])

        if tokens[0].token_type == Tokentype.type:
            var_node.add_child(node_from_token(tokens[0]))

        assignment_node.add_child(var_node)

        rhs_node = parse_expression(tokens[binding_idx + 1:])
        if rhs_node:
            assignment_node.add_child(rhs_node)

        return assignment_node

    # 4. Any other standalone statement is an expression (e.g. a function call)
    return parse_expression(tokens)


def is_blank(statement: list[Token]) -> bool:
    """A line with nothing on it except indentation."""
    return all(t.token_type == Tokentype.tab for t in statement)


def indent_of(statement: list[Token]) -> int:
    depth = 0
    for token in statement:
        if token.token_type != Tokentype.tab:
            break
        depth += 1
    return depth


def make_statements_from_tokens(tokens: list[Token]) -> list[list[Token]]:
    """Split tokens into lines (statements); blank lines are dropped.

    Each statement keeps its leading tab tokens, so blocks can be found later.
    """
    statements = []
    current_statement = []

    for token in tokens:
        if token.token_type == Tokentype.newline:
            if current_statement and not is_blank(current_statement):
                statements.append(current_statement)
            current_statement = []
        else:
            current_statement.append(token)

    if current_statement and not is_blank(current_statement):
        statements.append(current_statement)
    return statements


# --- while loops: draft top-down, resolve bottom-up ------------------------------

def draft_while(header: list[Token], body_lines: list[list[Token]]) -> Node:
    """Top-down: build the flow_control node with unresolved 'test' and 'body'
    children that only hold their tokens for now.

    header     -- "while", the condition and the closing ":"
    body_lines -- the indented lines, with one level of indentation removed
    """
    if header[-1].token_type != Tokentype.column:
        raise SyntaxError("a while header must end with ':'")
    test_tokens = header[1:-1]
    if not test_tokens:
        raise SyntaxError("while needs a condition")
    if not body_lines:
        raise IndentationError("expected an indented block after 'while'")

    body_tokens = []
    for line in body_lines:
        body_tokens.extend(line)
        body_tokens.append(Token("\n", Tokentype.newline))

    loop = node_from_token(header[0])
    loop.add_child(Node("test", NodeType.expression, tokens=test_tokens, resolved=False))
    loop.add_child(Node("body", NodeType.statement, tokens=body_tokens, resolved=False))
    return loop


def resolve(node: Node) -> None:
    """Turn a drafted node's tokens into real children."""
    if node.resolved:
        return
    if node.node_type == NodeType.expression:
        node.add_child(parse_expression(node.tokens))
    elif node.node_type == NodeType.statement and node.value == "body":
        # The body is a block of its own, so it may hold nested loops.
        for child in build_statements(make_statements_from_tokens(node.tokens)):
            node.add_child(child)
    node.resolved = True


def resolve_tree(node: Node) -> Node:
    """Bottom-up: resolve the children first, then the node itself."""
    for child in node.children:
        resolve_tree(child)
    resolve(node)
    return node


def build_statements(statements: list[list[Token]]) -> list[Node]:
    """Build the nodes for a block of lines that all start at indentation 0."""
    nodes = []
    i = 0
    while i < len(statements):
        statement = statements[i]
        if is_blank(statement):
            i += 1
            continue
        if indent_of(statement) > 0:
            raise IndentationError("unexpected indent")

        if statement[0].token_type == Tokentype.flow_control:
            # Every following indented line belongs to the loop's body.
            body_lines = []
            i += 1
            while i < len(statements) and (is_blank(statements[i]) or indent_of(statements[i]) > 0):
                if not is_blank(statements[i]):
                    body_lines.append(statements[i][1:])  # remove one indent level
                i += 1
            nodes.append(resolve_tree(draft_while(statement, body_lines)))
            continue

        node = build_statement_ast(statement)
        if node:
            nodes.append(node)
        i += 1
    return nodes


def build_program_ast(statements: list[list[Token]]) -> AST:
    if not statements:
        return AST()

    program_root = Node(value="PROGRAM", node_type=NodeType.program)

    for node in build_statements(statements):
        program_root.add_child(node)

    return AST(root=program_root)


def print_ast(ast: AST) -> None:
    if not ast or not ast.root:
        print("Empty AST")
        return

    def _print_node(node: Node, prefix: str = "", is_last: bool = True):
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}{node.value} ({node.node_type.name})")

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(node.children):
            _print_node(child, new_prefix, is_last=(i == len(node.children) - 1))

    print("AST Tree Structure:")
    _print_node(ast.root, is_last=True)
