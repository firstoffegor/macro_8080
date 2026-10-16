from macro_ast import Node, NodeType, build_program_ast, make_statements_from_tokens
from parser import parse_tokens


def build(code: str):
    return build_program_ast(make_statements_from_tokens(parse_tokens(code)))


def all_nodes(node):
    yield node
    for child in node.children:
        yield from all_nodes(child)


def test_token_type_is_removed():
    node = Node("a", NodeType.var_name)
    assert not hasattr(node, "token_type")
    assert node.node_type == NodeType.var_name


def test_no_node_in_a_built_tree_has_token_type():
    ast = build("int a = b + fun1(c)\n")
    for node in all_nodes(ast.root):
        assert not hasattr(node, "token_type")
        assert isinstance(node.node_type, NodeType)


def test_program_root_has_its_own_node_type():
    ast = build("a = 1\n")
    assert ast.root.node_type == NodeType.program


def test_correct_node_type_for_expression():
    # a + 1 * fun1(b)
    ast = build("a + 1 * fun1(b)\n")
    plus = ast.root.children[0]
    assert plus.node_type == NodeType.op

    a, times = plus.children
    assert a.node_type == NodeType.var_name
    assert times.node_type == NodeType.op

    one, call = times.children
    assert one.node_type == NodeType.literal
    assert call.node_type == NodeType.func_call
    assert call.children[0].node_type == NodeType.var_name


def test_correct_node_type_for_declaration():
    ast = build("int a = 1\n")
    assign = ast.root.children[0]
    assert (assign.node_type, assign.value) == (NodeType.statement, "=")

    target, rhs = assign.children
    assert target.node_type == NodeType.var_name
    assert target.children[0].node_type == NodeType.type
    assert rhs.node_type == NodeType.literal


def test_return_is_a_statement():
    ast = build("return a + b\n")
    ret = ast.root.children[0]
    assert (ret.node_type, ret.value) == (NodeType.statement, "return")
    assert ret.children[0].node_type == NodeType.op
