from ast_parser import SemanticASTParser


def test_is_semantic_checkpoint_for_complete_function():
    parser = SemanticASTParser()
    code = "def foo(x):\n    return x * 2\n"
    assert parser.is_semantic_checkpoint(code)


def test_is_semantic_checkpoint_for_incomplete_code():
    parser = SemanticASTParser()
    code = "def foo(x):\n    return x *"
    assert not parser.is_semantic_checkpoint(code)


def test_parse_to_ast_returns_ast_node():
    parser = SemanticASTParser()
    code = "x = 1\ny = x + 2\n"
    tree = parser.parse_to_ast(code)
    assert hasattr(tree, 'body')
    assert len(tree.body) == 2
