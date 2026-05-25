from dataclasses import dataclass
import argparse
import os
import time
import random
from typing import List, Optional

ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key, value)

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
    client: Optional[LLMClient] = None,
    max_retries: int = 10,
    backoff_base: float = 0.05,
    max_backoff: float = 2.0,
    jitter: bool = True,
    sandbox_timeout: float = 3.0,
    verbose: bool = False,
) -> str:
    """Run the Zero-SCD synthesis loop with retry/backoff support.

    - `max_retries`: maximum retry attempts before aborting
    - `backoff_base`: base sleep in seconds for exponential backoff
    - `max_backoff`: maximum backoff cap in seconds
    - `jitter`: whether to add +/-20%% random jitter to backoff
    - `sandbox_timeout`: timeout for sandbox execution in seconds
    - `verbose`: print progress messages during synthesis
    """
    session = DecodingSessionState(system_prompt, spec_invariants)
    parser = SemanticASTParser()
    client = client or LLMClient()
    if verbose:
        print(f"[Zero-SCD] prompt={repr(system_prompt)}")
        print(f"[Zero-SCD] model={client.model} api_key_set={client.api_key is not None} stub_mode={client.uses_stub}")


    while not generation_is_complete(session, max_retries=max_retries):
        try:
            temperature = 0.2 if session.current_retry_count == 0 else 0.7
            if verbose:
                print(f"[Zero-SCD] attempt={session.current_retry_count + 1} temperature={temperature}")
            token_stream = client.stream_completion(
                prompt=session.committed_history,
                temperature=temperature,
            )
        except Exception as exc:
            session.current_retry_count += 1
            if verbose:
                print(f"[Zero-SCD] client failure: {exc}")
            sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
            if jitter:
                sleep *= random.uniform(0.8, 1.2)
            time.sleep(sleep)
            if session.current_retry_count >= max_retries:
                break
            continue

        try:
            created_checkpoint = False
            for token in token_stream:
                session.speculative_buffer += token

                if parser.is_semantic_checkpoint(session.committed_history, session.speculative_buffer):
                    created_checkpoint = True
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
                        if verbose:
                            print('[Zero-SCD] checkpoint accepted')
                        break
                    else:
                        session.speculative_buffer = ''
                        session.current_retry_count += 1
                        session.committed_history += f"\n# Error: Specification failed for: {diagnostic}. Rectify this error."
                        if verbose:
                            print(f"[Zero-SCD] checkpoint rejected: {diagnostic}")

                        sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
                        if jitter:
                            sleep *= random.uniform(0.8, 1.2)
                        time.sleep(sleep)
                        break

            if not created_checkpoint:
                session.speculative_buffer = ''
                session.current_retry_count += 1
                session.committed_history += '\n# Error: No semantic checkpoint found; retrying.'
                if verbose:
                    print('[Zero-SCD] stream completed without checkpoint; retrying')
                sleep = min(max_backoff, backoff_base * (2 ** (session.current_retry_count - 1)))
                if jitter:
                    sleep *= random.uniform(0.8, 1.2)
                time.sleep(sleep)
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
    parser.add_argument('--api-key', type=str, help='Optional LLM API key (overrides env vars).')
    parser.add_argument('--model', type=str, help='Optional model name (overrides LLM_MODEL / default).')
    parser.add_argument('--api-url', type=str, help='Optional model endpoint URL (overrides LLM_API_URL).')
    parser.add_argument('--max-retries', type=int, default=10, help='Maximum retry attempts before aborting.')
    parser.add_argument('--backoff-base', type=float, default=0.05, help='Base backoff delay in seconds.')
    parser.add_argument('--max-backoff', type=float, default=2.0, help='Max backoff delay in seconds.')
    parser.add_argument('--no-jitter', action='store_true', help='Disable jitter on backoff delays.')
    parser.add_argument('--sandbox-timeout', type=float, default=3.0, help='Sandbox execution timeout in seconds.')
    parser.add_argument('--verbose', action='store_true', help='Print progress and diagnostic messages.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.prompt_file:
        with open(args.prompt_file, 'r', encoding='utf-8') as handle:
            prompt = handle.read()
    else:
        prompt = args.prompt

    spec = default_specification()
    client = LLMClient(api_key=args.api_key, model=args.model, api_url=args.api_url)
    output = run_zero_scd_synthesis(
        prompt,
        [spec],
        client=client,
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
        max_backoff=args.max_backoff,
        jitter=not args.no_jitter,
        sandbox_timeout=args.sandbox_timeout,
        verbose=args.verbose,
    )
    print(output)


if __name__ == '__main__':
    main()
