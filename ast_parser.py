import ast
import codeop


class SemanticASTParser:
    """Detect semantic checkpoints in a streaming buffer."""

    STATEMENT_TERMINATORS = ('\n', ';')

    def __init__(self) -> None:
        self._compiler = codeop.Compile()

    def has_statement_boundary(self, speculative_buffer: str) -> bool:
        """True when the buffer ends a statement (newline or semicolon), per §3.3."""
        if not speculative_buffer or not speculative_buffer.strip():
            return False
        trimmed = speculative_buffer.rstrip()
        if trimmed.endswith(';'):
            return True
        return any(char in speculative_buffer for char in self.STATEMENT_TERMINATORS)

    def is_semantic_checkpoint(self, committed_history: str, speculative_buffer: str) -> bool:
        """Return True when the combined code completes a valid semantic block."""
        if not speculative_buffer or not speculative_buffer.strip():
            return False
        if not self.has_statement_boundary(speculative_buffer):
            return False

        candidate_code = committed_history
        if not candidate_code.endswith('\n'):
            candidate_code += '\n'
        candidate_code += speculative_buffer

        try:
            compiled = codeop.compile_command(candidate_code, symbol='exec')
            if compiled is None:
                return False
            if '# END' not in speculative_buffer:
                return False

            # Reject partial bare terminators that are syntactically valid
            # but semantically likely incomplete (e.g. a bare `return` line).
            stripped_lines = [line for line in speculative_buffer.splitlines() if line.strip()]
            if stripped_lines:
                last_line = stripped_lines[-1].strip()
                if last_line in {'return', 'raise', 'break', 'continue', 'pass'}:
                    return False

            # Ensure the combined candidate is syntactically valid, not just complete enough
            ast.parse(candidate_code, mode='exec')
            return True
        except (SyntaxError, ValueError, OverflowError):
            return False

    def parse_to_ast(self, speculative_buffer: str) -> ast.AST:
        return ast.parse(speculative_buffer, mode='exec')
