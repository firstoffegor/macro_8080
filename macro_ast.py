from token_class import Token, Tokentype

class Node:
    def __init__(self, value: str, token_type: Tokentype, children=None, parent=None):
        self.value = value           # Token name/value (e.g., "=", "+", "a", "int")
        self.token_type = token_type # The Tokentype enum
        self.children = children if children is not None else []
        self.parent = parent

    def add_child(self, child_node: "Node"):
        if child_node:
            child_node.parent = self
            self.children.append(child_node)

    def __repr__(self):
        if self.children:
            return f"Node('{self.value}', type={self.token_type.name}, children={len(self.children)})"
        return f"Node('{self.value}', type={self.token_type.name})"


class AST:
    def __init__(self, root: Node | None = None):
        self.root = root

    def __repr__(self):
        return f"AST(root={self.root})"


# --- REPLACED: Updated to handle operators, parentheses, and nested function calls ---
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

    PRECEDENCE = {
        "+": 1, "-": 1,
        "*": 2, "/": 2, "//": 2, "%": 2
    }

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
            if prec < lowest_prec:
                lowest_prec = prec
                split_idx = idx

    if split_idx != -1:
        op_token = token_list[split_idx]
        op_node = Node(value=op_token.name, token_type=op_token.token_type)
        
        left_node = parse_expression(token_list[:split_idx])
        right_node = parse_expression(token_list[split_idx + 1:])
        
        if left_node:
            op_node.add_child(left_node)
        if right_node:
            op_node.add_child(right_node)
            
        return op_node

    # 2. Match function calls: func_name(...)
    if token_list[0].token_type == Tokentype.func_name and len(token_list) > 1 and token_list[1].token_type == Tokentype.open_p:
        fn_token = token_list[0]
        func_node = Node(value=fn_token.name, token_type=fn_token.token_type)
        
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
    t = token_list[0]
    return Node(value=t.name, token_type=t.token_type)


def build_statement_ast(tokens: list[Token]) -> Node | None:
    if not tokens:
        return None

    # --- STATEMENT ROUTING ---

    # 1. Function Definition ("function some_func...")
    if tokens[0].token_type == Tokentype.func:
        func_keyword_token = tokens[0]
        func_node = Node(value=func_keyword_token.name, token_type=func_keyword_token.token_type)
        
        func_name_token = tokens[1]
        name_node = Node(value=func_name_token.name, token_type=func_name_token.token_type)
        func_node.add_child(name_node)
        
        param_idx = 2
        while param_idx < len(tokens) and tokens[param_idx].token_type != Tokentype.closed_p:
            t = tokens[param_idx]
            if t.token_type in (Tokentype.variable_name, Tokentype.type):
                name_node.add_child(Node(value=t.name, token_type=t.token_type))
            param_idx += 1
            
        return func_node

    # 2. Return Statements ("return a + b")
    if tokens[0].token_type == Tokentype.ret:
        ret_token = tokens[0]
        return_node = Node(value=ret_token.name, token_type=ret_token.token_type)
        
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
        bind_token = tokens[binding_idx]
        assignment_node = Node(value=bind_token.name, token_type=bind_token.token_type)
        
        var_token = tokens[binding_idx - 1]
        var_node = Node(value=var_token.name, token_type=var_token.token_type)
        
        if tokens[0].token_type == Tokentype.type:
            type_token = tokens[0]
            var_node.add_child(Node(value=type_token.name, token_type=type_token.token_type))
            
        assignment_node.add_child(var_node)
        
        # --- MODIFIED: Delegates RHS parsing entirely to parse_expression ---
        rhs_node = parse_expression(tokens[binding_idx + 1:])
        if rhs_node:
            assignment_node.add_child(rhs_node)
                
        return assignment_node

    # --- MODIFIED: Route 4 now delegates any standalone statement directly to parse_expression ---
    return parse_expression(tokens)


def make_statements_from_tokens(tokens: list[Token]) -> list[list[Token]]:
    statements = []
    current_statement = []

    for token in tokens:
        if token.token_type == Tokentype.newline:
            if current_statement:  
                statements.append(current_statement)
                current_statement = []
        else:
            current_statement.append(token)

    if current_statement:
        statements.append(current_statement)
    return statements


def build_program_ast(statements: list[list[Token]]) -> AST:
    if not statements:
        return AST()

    program_root = Node(value="PROGRAM", token_type=Tokentype.func)

    for stmt_tokens in statements:
        stmt_node = build_statement_ast(stmt_tokens)
        if stmt_node:
            program_root.add_child(stmt_node)

    return AST(root=program_root)


def print_ast(ast: AST) -> None:
    if not ast or not ast.root:
        print("Empty AST")
        return

    def _print_node(node: Node, prefix: str = "", is_last: bool = True):
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}{node.value} ({node.token_type.name})")
        
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        for i, child in enumerate(node.children):
            _print_node(child, new_prefix, is_last=(i == len(node.children) - 1))

    print("AST Tree Structure:")
    _print_node(ast.root, is_last=True)