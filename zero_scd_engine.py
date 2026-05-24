from dataclasses import dataclass
import argparse
import time
import random
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


def generation_is_complete(session: DecodingSessionState, max_retries: int = 10, completion_marker: str = '# END') -> bool:
    return completion_marker in session.committed_history or session.current_retry_count >= max_retries


def run_zero_scd_synthesis(
    system_prompt: str,
    spec_invariants: List[Specification],
    max_retries: int = 10,
    backoff_base: float = 0.05,
    max_backoff: float = 2.0,
    jitter: bool = True,
    sandbox_timeout: float = 0.02,
) -> str:
    """Run the Zero-SCD synthesis loop with retry/backoff support.

    - `max_retries`: maximum retry attempts before aborting
    - `backoff_base`: base sleep in seconds for exponential backoff
    - `max_backoff`: maximum backoff cap in seconds
    - `jitter`: whether to add +/-20%% random jitter to backoff
    - `sandbox_timeout`: timeout for sandbox execution in seconds
    """
    session = DecodingSessionState(system_prompt, spec_invariants)
    parser = SemanticASTParser()
    client = LLMClient()

    while not generation_is_complete(session, max_retries=max_retries):
        try:
            token_stream = client.stream_completion(
                prompt=session.committed_history,
                temperature=0.2 if session.current_retry_count == 0 else 0.7,
            )
        except Exception:
            session.current_retry_count += 1
            # backoff on client failures
            sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
            if jitter:
                sleep *= random.uniform(0.8, 1.2)
            time.sleep(sleep)
            if session.current_retry_count >= max_retries:
                break
            continue

        try:
            for token in token_stream:
                session.speculative_buffer += token

                if parser.is_semantic_checkpoint(session.speculative_buffer):
                    candidate_code = session.committed_history + '\n' + session.speculative_buffer
                    try:
                        success, diagnostic = evaluate_executable_oracle(
                            candidate_code,
                            session.specifications,
                            timeout=sandbox_timeout,
                        )
                    except Exception as exc:
                        success = False
                        diagnostic = f'Oracle exception: {exc}'

                    if success:
                        session.committed_history += '\n' + session.speculative_buffer
                        session.speculative_buffer = ''
                        session.current_retry_count = 0
                        break
                    else:
                        session.speculative_buffer = ''
                        session.current_retry_count += 1
                        session.committed_history += f"\n# Error: Specification failed for: {diagnostic}. Rectify this error."

                        # exponential backoff before allowing the next speculative attempt
                        sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
                        if jitter:
                            sleep *= random.uniform(0.8, 1.2)
                        time.sleep(sleep)
                        break
        except Exception:
            # If streaming fails mid-way, treat as a transient failure and backoff
            session.current_retry_count += 1
            sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
            if jitter:
                sleep *= random.uniform(0.8, 1.2)
            time.sleep(sleep)

        if session.current_retry_count >= max_retries:
            break

    return session.committed_history


def sample_predicate(namespace, sample):
    if 'synthesized_function' not in namespace:
        return False
    try:
        return namespace['synthesized_function'](sample['value']) == sample['value'] * 2
    except Exception:
        return False


def default_specification() -> Specification:
    return Specification(
        description='synthesized_function should double integer inputs',
        predicate=sample_predicate,
        sample_inputs=[{'value': x} for x in [0, 1, 2, 10, -5]],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the Zero-SCD synthesis engine.')
    parser.add_argument('--prompt', type=str, default='# Complete the function implementation below', help='Prompt text to send to the LLM.')
    parser.add_argument('--prompt-file', type=str, help='Path to a prompt file.')
    parser.add_argument('--max-retries', type=int, default=10, help='Maximum retry attempts before aborting.')
    parser.add_argument('--backoff-base', type=float, default=0.05, help='Base backoff delay in seconds.')
    parser.add_argument('--max-backoff', type=float, default=2.0, help='Max backoff delay in seconds.')
    parser.add_argument('--no-jitter', action='store_true', help='Disable jitter on backoff delays.')
    parser.add_argument('--sandbox-timeout', type=float, default=0.02, help='Sandbox execution timeout in seconds.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.prompt_file:
        with open(args.prompt_file, 'r', encoding='utf-8') as handle:
            prompt = handle.read()
    else:
        prompt = args.prompt

    spec = default_specification()
    output = run_zero_scd_synthesis(
        prompt,
        [spec],
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
        max_backoff=args.max_backoff,
        jitter=not args.no_jitter,
        sandbox_timeout=args.sandbox_timeout,
    )
    print(output)


if __name__ == '__main__':
    main()
