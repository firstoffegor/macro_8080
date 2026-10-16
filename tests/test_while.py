import pytest

from macro_ast import NodeType, build_program_ast, make_statements_from_tokens
from parser import parse_tokens
from recognizer import recognise_token
from token_class import Tokentype

WHILE_CODE = (
    "while (a && b):\n"
    "    a = a + b\n"
    "    a = a + 1\n"
    "    fun1(a - b)\n"
)


def build(code: str):
    return build_program_ast(make_statements_from_tokens(parse_tokens(code)))


def shape(node):
    return node.node_type, node.value


def all_nodes(node):
    yield node
    for child in node.children:
        yield from all_nodes(child)


# --- tokens ---------------------------------------------------------------

def test_while_header_and_body_tokens():
    tokens = parse_tokens("while (a && b):\n    a = a + b\n")
    assert [t.token_type for t in tokens] == [
        Tokentype.flow_control, Tokentype.open_p, Tokentype.variable_name,
        Tokentype.aop, Tokentype.variable_name, Tokentype.closed_p,
        Tokentype.column, Tokentype.newline,
        Tokentype.tab, Tokentype.variable_name, Tokentype.binding,
        Tokentype.variable_name, Tokentype.aop, Tokentype.variable_name,
        Tokentype.newline,
    ]


def test_while_directly_followed_by_paren_is_still_the_keyword():
    tokens = parse_tokens("while(a):\n")
    assert (tokens[0].name, tokens[0].token_type) == ("while", Tokentype.flow_control)


def test_four_spaces_make_one_tab_token():
    tokens = parse_tokens("    a\n")
    assert [t.token_type for t in tokens][:2] == [Tokentype.tab, Tokentype.variable_name]


def test_nested_indentation_makes_several_tab_tokens():
    tokens = parse_tokens("        a\n")
    assert [t.token_type for t in tokens][:3] == [Tokentype.tab, Tokentype.tab, Tokentype.variable_name]


def test_tab_character_is_a_tab_token():
    tokens = parse_tokens("\ta\n")
    assert [t.token_type for t in tokens][:2] == [Tokentype.tab, Tokentype.variable_name]


def test_spaces_inside_a_line_are_not_indentation():
    tokens = parse_tokens("a      =      1\n")
    assert Tokentype.tab not in [t.token_type for t in tokens]


@pytest.mark.parametrize("word", ["&&", "and"])
def test_logical_and_is_an_operator(word):
    assert recognise_token(word).token_type == Tokentype.aop


def test_whitespace_only_lines_are_not_statements():
    tokens = parse_tokens("a = 1\n    \nb = 2\n    ")
    assert len(make_statements_from_tokens(tokens)) == 2


# --- AST structure (the tree from the sketch) ---------------------------------

def test_while_ast_structure():
    loop = build(WHILE_CODE).root.children[0]
    assert shape(loop) == (NodeType.flow_control, "while")

    test, body = loop.children

    # [0] expression "test" -> op && -> a, b
    assert shape(test) == (NodeType.expression, "test")
    cond = test.children[0]
    assert shape(cond) == (NodeType.op, "&&")
    assert [shape(c) for c in cond.children] == [(NodeType.var_name, "a"), (NodeType.var_name, "b")]

    # [1] statement "body" -> three statements
    assert shape(body) == (NodeType.statement, "body")
    assert len(body.children) == 3

    first = body.children[0]
    assert shape(first) == (NodeType.statement, "=")
    target, rhs = first.children
    assert shape(target) == (NodeType.var_name, "a")
    assert shape(rhs) == (NodeType.op, "+")
    assert [shape(c) for c in rhs.children] == [(NodeType.var_name, "a"), (NodeType.var_name, "b")]

    second = body.children[1]
    assert shape(second) == (NodeType.statement, "=")
    assert [shape(c) for c in second.children[1].children] == [(NodeType.var_name, "a"), (NodeType.literal, "1")]

    call = body.children[2]
    assert shape(call) == (NodeType.func_call, "fun1")
    assert shape(call.children[0]) == (NodeType.op, "-")


def test_and_keyword_builds_the_same_tree_as_double_ampersand():
    cond = build("while (a and b):\n    a = 1\n").root.children[0].children[0].children[0]
    assert shape(cond) == (NodeType.op, "and")
    assert [c.value for c in cond.children] == ["a", "b"]


def test_while_without_parentheses():
    loop = build("while a && b:\n    a = 1\n").root.children[0]
    assert shape(loop.children[0].children[0]) == (NodeType.op, "&&")


def test_logical_and_binds_looser_than_arithmetic():
    cond = build("while (a + 1 && b):\n    a = 1\n").root.children[0].children[0].children[0]
    assert cond.value == "&&"
    assert cond.children[0].value == "+"


def test_every_node_is_resolved_and_has_a_parent():
    ast = build(WHILE_CODE)
    for node in all_nodes(ast.root):
        assert node.resolved
    for node in all_nodes(ast.root):
        for child in node.children:
            assert child.parent is node


def test_drafted_nodes_keep_their_tokens():
    loop = build(WHILE_CODE).root.children[0]
    test, body = loop.children
    assert [t.name for t in test.tokens] == ["(", "a", "&&", "b", ")"]
    assert body.tokens  # the drafted body slice is still there


def test_statements_after_the_loop_are_outside_it():
    ast = build("x = 1\nwhile (a):\n    x = 2\ny = 3\n")
    assert [shape(n) for n in ast.root.children] == [
        (NodeType.statement, "="),
        (NodeType.flow_control, "while"),
        (NodeType.statement, "="),
    ]
    assert len(ast.root.children[1].children[1].children) == 1


def test_blank_line_inside_a_body_is_ignored():
    loop = build("while (a):\n    a = 1\n\n    b = 2\n").root.children[0]
    assert len(loop.children[1].children) == 2


def test_nested_while():
    code = (
        "while (a):\n"
        "    while (b):\n"
        "        c = 1\n"
        "    d = 2\n"
    )
    outer = build(code).root.children[0]
    body = outer.children[1]
    inner, after = body.children
    assert shape(inner) == (NodeType.flow_control, "while")
    assert shape(inner.children[1].children[0]) == (NodeType.statement, "=")
    assert shape(after) == (NodeType.statement, "=")


# --- errors ---------------------------------------------------------------

def test_while_header_without_colon_is_a_syntax_error():
    with pytest.raises(SyntaxError):
        build("while (a)\n    a = 1\n")


def test_while_without_a_body_is_an_indentation_error():
    with pytest.raises(IndentationError):
        build("while (a):\nb = 1\n")


def test_unexpected_indent_is_an_indentation_error():
    with pytest.raises(IndentationError):
        build("    a = 1\n")
