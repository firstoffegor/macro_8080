import pytest

from extract_scopes import extract_scopes
from macro_ast import NodeType, build_program_ast, make_statements_from_tokens
from parser import parse_tokens
from recognizer import recognise_token
from token_class import Tokentype


def parse_expr(code: str):
    """Parse a single-statement program and return that statement's node."""
    tokens = parse_tokens(code)
    ast = build_program_ast(make_statements_from_tokens(tokens))
    return ast.root.children[0]


# --- recognizer ---------------------------------------------------------

def test_underscore_is_a_variable_not_an_operator():
    assert recognise_token("_").token_type == Tokentype.variable_name


def test_minus_is_an_operator():
    assert recognise_token("-").token_type == Tokentype.aop


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "//", "**", "%"])
def test_all_arithmetic_operators(op):
    assert recognise_token(op).token_type == Tokentype.aop


def test_only_a_lone_equals_is_a_binding():
    assert recognise_token("=").token_type == Tokentype.binding
    assert recognise_token("==").token_type != Tokentype.binding
    assert recognise_token("<=").token_type != Tokentype.binding
    assert recognise_token("!=").token_type != Tokentype.binding


# --- parser / tokenizer -------------------------------------------------

def test_last_token_is_kept_without_trailing_newline():
    tokens = parse_tokens("a = 123")
    assert [t.name for t in tokens] == ["a", "=", "123"]


def test_true_false_none_all_emitted():
    tokens = parse_tokens("True False None")
    assert [t.name for t in tokens] == ["True", "False", "None"]
    assert all(t.token_type == Tokentype.literal for t in tokens)


def test_call_name_is_func_name():
    tokens = parse_tokens("print(a + b)")
    assert (tokens[0].name, tokens[0].token_type) == ("print", Tokentype.func_name)


def test_grouping_paren_does_not_emit_empty_func_name():
    tokens = parse_tokens("a + (b + c)\n")
    assert all(t.name != "" for t in tokens)
    assert not any(t.token_type == Tokentype.func_name for t in tokens)


# --- expression parsing -------------------------------------------------

def test_grouping_parens_build_the_right_tree():
    node = parse_expr("a + (b + c)\n")
    assert node.value == "+"
    assert node.children[0].value == "a"
    assert node.children[1].value == "+"
    assert [c.value for c in node.children[1].children] == ["b", "c"]


def test_minus_parses_as_binary_operator():
    node = parse_expr("x = a - b\n")
    rhs = node.children[1]
    assert (rhs.value, rhs.node_type) == ("-", NodeType.op)


def test_subtraction_is_left_associative():
    node = parse_expr("a - b - c\n")  # (a - b) - c
    assert node.value == "-"
    assert node.children[0].value == "-"
    assert node.children[1].value == "c"


def test_power_binds_tighter_than_addition():
    node = parse_expr("a + b ** c\n")  # a + (b ** c)
    assert node.value == "+"
    assert node.children[1].value == "**"


def test_power_is_right_associative():
    node = parse_expr("a ** b ** c\n")  # a ** (b ** c)
    assert node.value == "**"
    assert node.children[0].value == "a"
    assert node.children[1].value == "**"


def test_assignment_without_target_raises():
    with pytest.raises(ValueError):
        parse_expr("= 5\n")


# --- extract_scopes -----------------------------------------------------

def test_declaration_does_not_swallow_following_lines():
    tokens = parse_tokens("int a = 1 + 2\nprint(b)\nint c = 3\n")
    global_scope = extract_scopes(tokens)[0]
    assert global_scope.variables == {"a": ("1", "+", "2"), "c": "3"}


def test_single_line_declaration_without_trailing_newline():
    tokens = parse_tokens("int a = 5")
    assert extract_scopes(tokens)[0].variables == {"a": "5"}


def test_return_ends_function_scope_and_skips_its_line():
    code = "function f(int x)\nint y = x + 1\nreturn y\nint z = 5\n"
    scopes = extract_scopes(parse_tokens(code))
    assert [s.name for s in scopes] == ["global", "f"]
    assert scopes[1].variables == {"y": ("x", "+", "1")}
    assert scopes[0].variables == {"z": "5"}
