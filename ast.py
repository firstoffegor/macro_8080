from token_class import Token, Tokentype

class Node:
    def __init__(self, value: str, left=None, right=None, parent=None):
        self.value = value       # The token name/value (e.g., "=", "+", "a")
        self.left = left         # Left child Node
        self.right = right       # Right child Node
        self.parent = parent     # Reference to parent Node

    def __repr__(self):
        if self.left or self.right:
            return f"Node({self.value}, left={self.left}, right={self.right})"
        return f"Node({self.value})"


class AST:
    def __init__(self, root: Node | None = None):
        self.root = root

    def __repr__(self):
        return f"AST(root={self.root})"


def print_ast(ast: AST) -> None:
    """
    Prints an AST visually using tree-like indentation.
    """
    if not ast or not ast.root:
        print("Empty AST")
        return

    def _print_node(node: Node, prefix: str = "", is_left: bool = True):
        if node is None:
            return
        
        # Decide which branch character to draw
        marker = "├── " if is_left else "└── "
        
        # Print the current node's value
        print(prefix + marker + str(node.value))
        
        # Calculate the spacing for the children
        new_prefix = prefix + ("│   " if is_left else "    ")
        
        # Recursively print the children.
        # We print left first, then right.
        if node.left or node.right:
            if node.left:
                _print_node(node.left, new_prefix, is_left=True)
            else:
                print(new_prefix + "├── None")
                
            if node.right:
                _print_node(node.right, new_prefix, is_left=False)
            else:
                print(new_prefix + "└── None")

    # Start the recursion from the root node
    print("AST Tree Structure:")
    _print_node(ast.root, is_left=False)


def build_statement_ast(tokens: list[Token]) -> Node | None:
    """
    Parses a single statement (which we know is pre-cleaned of spaces/newlines).
    Returns the root Node of that statement.
    """
    if not tokens:
        return None

    PRECEDENCE = {
        "+": 1, "-": 1,
        "*": 2, "/": 2, "//": 2, "%": 2
    }

    # Helper to parse math or value expressions
    def parse_math_expression(token_list: list[Token]) -> Node | None:
        if not token_list:
            return None
        if len(token_list) == 1:
            return Node(value=token_list[0].name)

        split_idx = -1
        lowest_prec = float('inf')
        for idx in range(len(token_list) - 1, -1, -1):
            token = token_list[idx]
            if token.token_type == Tokentype.aop:
                prec = PRECEDENCE.get(token.name, 1)
                if prec < lowest_prec:
                    lowest_prec = prec
                    split_idx = idx

        if split_idx != -1:
            op_node = Node(value=token_list[split_idx].name)
            left_node = parse_math_expression(token_list[:split_idx])
            right_node = parse_math_expression(token_list[split_idx+1:])
            
            op_node.left = left_node
            op_node.right = right_node
            if left_node: left_node.parent = op_node
            if right_node: right_node.parent = op_node
            return op_node

        return Node(value=token_list[0].name)

    # --- STATEMENT ROUTING ---

    # 1. Function Definition ("function some_func...")
    if tokens[0].token_type == Tokentype.func:
        func_name_token = tokens[1]
        func_node = Node(value=f"def {func_name_token.name}")
        
        params = []
        param_idx = 2
        while param_idx < len(tokens) and tokens[param_idx].token_type != Tokentype.closed_p:
            t = tokens[param_idx]
            if t.token_type in (Tokentype.variable_name, Tokentype.type):
                params.append(t.name)
            param_idx += 1
            
        if params:
            func_node.left = Node(value=f"params: {', '.join(params)}")
            func_node.left.parent = func_node
            
        return func_node

    # 2. Return Statements ("return a")
    if tokens[0].token_type == Tokentype.ret:
        return_node = Node(value=tokens[0].name)
        expression_node = parse_math_expression(tokens[1:])
        return_node.right = expression_node
        if expression_node:
            expression_node.parent = return_node
        return return_node

    # 3. Variable Assignment / Declaration (Contains "=")
    binding_idx = -1
    for idx, token in enumerate(tokens):
        if token.token_type == Tokentype.binding:
            binding_idx = idx
            break

    if binding_idx != -1:
        assignment_node = Node(value="=")
        
        if tokens[0].token_type == Tokentype.type:
            type_node = Node(value=tokens[0].name)
            var_node = Node(value=tokens[binding_idx - 1].name)
            var_node.left = type_node
            type_node.parent = var_node
        else:
            var_node = Node(value=tokens[binding_idx - 1].name)
            
        rhs_tokens = tokens[binding_idx + 1:]
        if rhs_tokens[0].token_type == Tokentype.func_name:
            call_node = Node(value=rhs_tokens[0].name)
            args = [t for t in rhs_tokens[1:] if t.token_type not in (Tokentype.open_p, Tokentype.closed_p, Tokentype.comma)]
            call_node.right = parse_math_expression(args)
            if call_node.right:
                call_node.right.parent = call_node
            math_expr_node = call_node
        else:
            math_expr_node = parse_math_expression(rhs_tokens)
        
        assignment_node.left = var_node
        assignment_node.right = math_expr_node
        var_node.parent = assignment_node
        if math_expr_node:
            math_expr_node.parent = assignment_node
            
        return assignment_node

    # 4. Standalone Function Call ("print(...)")
    if tokens[0].token_type == Tokentype.func_name:
        func_node = Node(value=tokens[0].name)
        inner_tokens = tokens[2:-1] if tokens[-1].token_type == Tokentype.closed_p else tokens[2:]
        args_tokens = [t for t in inner_tokens if t.token_type != Tokentype.comma]
        
        func_node.right = parse_math_expression(args_tokens)
        if func_node.right:
            func_node.right.parent = func_node
        return func_node

    # 5. Non-executable expression fallback
    print(f"Warning: Standalone expression '{' '.join([t.name for t in tokens])}' ignored.")
    return None


def build_program_ast(statements: list[list[Token]]) -> AST:
    """
    Takes a list of statements (each statement is a list of tokens).
    Combines them into a single, unified AST.
    """
    if not statements:
        return AST()

    # Base node representing our program block
    root_block = Node(value="BLOCK")
    current_block = root_block

    for idx, stmt_tokens in enumerate(statements):
        # Build the sub-tree for this specific line
        stmt_root = build_statement_ast(stmt_tokens)
        if not stmt_root:
            continue
        
        # The left child of a BLOCK runs the statement
        current_block.left = stmt_root
        stmt_root.parent = current_block

        # If there are more statements coming, prepare the next block on the right
        if idx < len(statements) - 1:
            next_block = Node(value="BLOCK")
            current_block.right = next_block
            next_block.parent = current_block
            current_block = next_block

    return AST(root=root_block)