import ast
import codeop


class SemanticASTParser:
    """Detect semantic checkpoints in a streaming buffer."""

    def __init__(self) -> None:
        self._compiler = codeop.Compile()

    def is_semantic_checkpoint(self, speculative_buffer: str) -> bool:
        """Return True when speculative_buffer completes a valid semantic block."""
        if not speculative_buffer or not speculative_buffer.strip():
            return False

        try:
            compiled = codeop.compile_command(speculative_buffer, symbol='exec')
            return compiled is not None
        except (SyntaxError, ValueError, OverflowError):
            return False

    def parse_to_ast(self, speculative_buffer: str) -> ast.AST:
        return ast.parse(speculative_buffer, mode='exec')
