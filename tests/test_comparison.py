import pytest

from macro_ast import NodeType, build_program_ast, make_statements_from_tokens
from parser import parse_tokens
from recognizer import recognise_token
from token_class import Tokentype

COMPARISONS = ["<", ">", "<=", ">=", "==", "!="]
LOGICAL = ["&&", "and", "||", "or"]


def build(code: str):
    return build_program_ast(make_statements_from_tokens(parse_tokens(code)))


def expr(code: str):
    """The node of a single-line expression statement."""
    return build(code).root.children[0]


def shape(node):
    return node.node_type, node.value


# --- tokens ---------------------------------------------------------------

@pytest.mark.parametrize("op", COMPARISONS + LOGICAL)
def test_operator_is_recognised(op):
    assert recognise_token(op).token_type == Tokentype.aop


def test_a_lone_equals_is_still_the_binding():
    assert recognise_token("=").token_type == Tokentype.binding


def test_operators_stay_separate_tokens():
    tokens = parse_tokens("a >= b\n")
    assert [(t.name, t.token_type) for t in tokens[:3]] == [
        ("a", Tokentype.variable_name),
        (">=", Tokentype.aop),
        ("b", Tokentype.variable_name),
    ]


# --- the tree ---------------------------------------------------------------

@pytest.mark.parametrize("op", COMPARISONS + LOGICAL)
def test_operator_builds_an_op_node(op):
    node = expr(f"a {op} b\n")
    assert shape(node) == (NodeType.op, op)
    assert [c.value for c in node.children] == ["a", "b"]


def test_arithmetic_binds_tighter_than_comparison():
    node = expr("a + 1 < b * 2\n")  # (a + 1) < (b * 2)
    assert node.value == "<"
    assert [c.value for c in node.children] == ["+", "*"]


def test_comparison_binds_tighter_than_and():
    node = expr("a < b && c > d\n")  # (a < b) && (c > d)
    assert node.value == "&&"
    assert [c.value for c in node.children] == ["<", ">"]


def test_and_binds_tighter_than_or():
    node = expr("a || b && c\n")  # a || (b && c)
    assert node.value == "||"
    assert node.children[0].value == "a"
    assert node.children[1].value == "&&"


def test_or_and_and_keywords_follow_the_same_precedence():
    node = expr("a or b and c\n")
    assert node.value == "or"
    assert node.children[1].value == "and"


def test_or_splits_before_a_comparison_on_its_left():
    node = expr("a == b or c != d\n")  # (a == b) or (c != d)
    assert node.value == "or"
    assert [c.value for c in node.children] == ["==", "!="]


def test_comparisons_are_left_associative():
    node = expr("a < b < c\n")  # (a < b) < c
    assert node.value == "<"
    assert node.children[0].value == "<"
    assert node.children[1].value == "c"


def test_parentheses_override_precedence():
    node = expr("(a || b) && c\n")
    assert node.value == "&&"
    assert node.children[0].value == "||"


def test_comparison_on_the_right_of_an_assignment():
    node = expr("x = a == b\n")
    assert shape(node) == (NodeType.statement, "=")
    target, rhs = node.children
    assert shape(target) == (NodeType.var_name, "x")
    assert shape(rhs) == (NodeType.op, "==")


def test_comparison_inside_a_function_call():
    call = expr("f(a < b, c)\n")
    assert shape(call) == (NodeType.func_call, "f")
    assert [c.value for c in call.children] == ["<", "c"]


def test_literal_operand():
    node = expr("i < 10\n")
    assert shape(node.children[1]) == (NodeType.literal, "10")


# --- while loops -----------------------------------------------------------

@pytest.mark.parametrize("op", COMPARISONS)
def test_while_with_a_comparison_test(op):
    loop = build(f"while (i {op} 10):\n    i = i + 1\n").root.children[0]
    test, body = loop.children
    cond = test.children[0]
    assert shape(cond) == (NodeType.op, op)
    assert [shape(c) for c in cond.children] == [(NodeType.var_name, "i"), (NodeType.literal, "10")]
    assert len(body.children) == 1


def test_while_with_a_compound_condition():
    loop = build("while (i < 10 && j != 0 || done == 1):\n    i = i + 1\n").root.children[0]
    cond = loop.children[0].children[0]
    assert cond.value == "||"
    assert cond.children[0].value == "&&"
    assert [c.value for c in cond.children[0].children] == ["<", "!="]
    assert cond.children[1].value == "=="
