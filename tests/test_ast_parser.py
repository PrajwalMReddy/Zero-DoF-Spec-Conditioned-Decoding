from ast_parser import SemanticASTParser


def test_is_semantic_checkpoint_for_complete_function():
    parser = SemanticASTParser()
    code = "def foo(x):\n    return x * 2\n# END"
    assert parser.is_semantic_checkpoint('', code)


def test_is_semantic_checkpoint_for_incomplete_code():
    parser = SemanticASTParser()
    code = "def foo(x):\n    return x *"
    assert not parser.is_semantic_checkpoint('', code)


def test_is_semantic_checkpoint_rejects_bare_return_without_newline():
    parser = SemanticASTParser()
    code = "def foo(x): return "
    assert not parser.is_semantic_checkpoint('', code)


def test_is_semantic_checkpoint_rejects_bare_return_line():
    parser = SemanticASTParser()
    committed = "def foo(x):\n"
    speculative = "    return\n"
    assert not parser.is_semantic_checkpoint(committed, speculative)


def test_is_semantic_checkpoint_with_prefix_returns_true():
    parser = SemanticASTParser()
    committed = "def foo(x):\n"
    speculative = "    return x * 2\n# END"
    assert parser.is_semantic_checkpoint(committed, speculative)


def test_semantic_checkpoint_accepts_semicolon_boundary():
    parser = SemanticASTParser()
    committed = "def foo(x):\n"
    speculative = "    return x * 2;\n# END"
    assert parser.is_semantic_checkpoint(committed, speculative)


def test_parse_to_ast_returns_ast_node():
    parser = SemanticASTParser()
    code = "x = 1\ny = x + 2\n"
    tree = parser.parse_to_ast(code)
    assert hasattr(tree, 'body')
    assert len(tree.body) == 2
