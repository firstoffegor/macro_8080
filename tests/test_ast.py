from macro_ast import Node, build_program_ast, make_statements_from_tokens
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
    code = "int a = b + c * d"
    tokens = parse_tokens(code)
    stmts = make_statements_from_tokens(tokens)
    ast = build_program_ast(stmts)
    binding = ast.root.children[0]
    assert binding.token_type == Tokentype.binding
    assert binding.children[1].value == "+"
    assert binding.children[1].children[1].value == "*"
