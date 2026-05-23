from dataclasses import dataclass
from typing import List

from ast_parser import SemanticASTParser
from llm_client import LLMClient
from oracle_sandbox import Specification, evaluate_executable_oracle


@dataclass
class DecodingSessionState:
    prompt: str
    specifications: List[Specification]
    committed_history: str
    speculative_buffer: str = ''
    current_retry_count: int = 0

    def __init__(self, prompt: str, specifications: List[Specification]):
        self.prompt = prompt
        self.specifications = specifications
        self.committed_history = prompt
        self.speculative_buffer = ''
        self.current_retry_count = 0


def generation_is_complete(session: DecodingSessionState, completion_marker: str = '# END') -> bool:
    return completion_marker in session.committed_history or session.current_retry_count >= 10


def run_zero_scd_synthesis(system_prompt: str, spec_invariants: List[Specification]) -> str:
    session = DecodingSessionState(system_prompt, spec_invariants)
    parser = SemanticASTParser()
    client = LLMClient()

    while not generation_is_complete(session):
        token_stream = client.stream_completion(
            prompt=session.committed_history,
            temperature=0.2 if session.current_retry_count == 0 else 0.7,
        )

        for token in token_stream:
            session.speculative_buffer += token

            if parser.is_semantic_checkpoint(session.speculative_buffer):
                candidate_code = session.committed_history + '\n' + session.speculative_buffer
                success, diagnostic = evaluate_executable_oracle(candidate_code, session.specifications)

                if success:
                    session.committed_history += '\n' + session.speculative_buffer
                    session.speculative_buffer = ''
                    session.current_retry_count = 0
                    break
                else:
                    session.speculative_buffer = ''
                    session.current_retry_count += 1
                    session.committed_history += f"\n# Error: Specification failed for: {diagnostic}. Rectify this error."
                    break

        if session.current_retry_count >= 10:
            break

    return session.committed_history


if __name__ == '__main__':
    def sample_predicate(namespace, sample):
        if 'synthesized_function' not in namespace:
            return False
        try:
            return namespace['synthesized_function'](sample['value']) == sample['value'] * 2
        except Exception:
            return False

    spec = Specification(
        description='synthesized_function should double integer inputs',
        predicate=sample_predicate,
        sample_inputs=[{'value': x} for x in [0, 1, 2, 10, -5]],
    )

    output = run_zero_scd_synthesis('''# Complete the function implementation below''', [spec])
    print(output)
