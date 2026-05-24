import argparse

from llm_client import LLMClient


def run_baseline(prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
    client = LLMClient()
    return ''.join(client.stream_completion(prompt=prompt, temperature=temperature, max_tokens=max_tokens))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the raw baseline LLM generation.')
    parser.add_argument('--prompt', type=str, default='# Baseline synthesis prompt\n', help='Prompt text to generate from.')
    parser.add_argument('--prompt-file', type=str, help='Path to a prompt file.')
    parser.add_argument('--temperature', type=float, default=0.2, help='Sampling temperature.')
    parser.add_argument('--max-tokens', type=int, default=256, help='Maximum number of tokens to generate.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.prompt_file:
        with open(args.prompt_file, 'r', encoding='utf-8') as handle:
            prompt = handle.read()
    else:
        prompt = args.prompt

    print('Baseline output:')
    print(run_baseline(prompt, temperature=args.temperature, max_tokens=args.max_tokens))


if __name__ == '__main__':
    main()
