from macro_ast import Node, build_program_ast, make_statements_from_tokens, print_ast
from token_class import Tokentype
from parser import parse_tokens



def test_ast_node_has_zero_children_in_empty_node():
    n1 = Node("=", Tokentype.binding)
    assert len(n1.children) == 0


def test_make_statements_from_tokens():
    code = """
    int a = b + c
    int d = g + h
    """
    tokens = parse_tokens(code)
    stmts = make_statements_from_tokens(tokens)
    assert len(stmts) == 2


def test_ast_precedence():
    code = "int a = b + c * d\n"
    tokens = parse_tokens(code)
    stmts = make_statements_from_tokens(tokens)
    ast = build_program_ast(stmts)
    binding = ast.root.children[0]
    assert binding.token_type == Tokentype.binding
    assert binding.children[1].value == "+"
    assert binding.children[1].children[1].value == "*"

def test_double_function_call():
    code = "fun1(fun2(a + b))\n"
    tokens = parse_tokens(code)
    stmts = make_statements_from_tokens(tokens)
    ast = build_program_ast(stmts)
    assert ast.root.children[0].value == "fun1"
    assert ast.root.children[0].children[0].children[0].children[0].value == "a"

def test_function_call():
    code = "a = fun1(b + c * d)\n"
    tokens = parse_tokens(code)
    stmts = make_statements_from_tokens(tokens)
    ast = build_program_ast(stmts)
    assert ast.root.children[0].children[1].children[0].children[1].value == "*"
    assert ast.root.children[0].children[1].children[0].children[0].value == "b"
    assert ast.root.children[0].children[0].value == "a"


