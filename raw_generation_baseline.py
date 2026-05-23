from llm_client import LLMClient


def run_baseline(prompt: str) -> str:
    client = LLMClient()
    return ''.join(client.stream_completion(prompt=prompt, temperature=0.2))


if __name__ == '__main__':
    prompt = '''# Baseline synthesis prompt\n'''
    print('Baseline output:')
    print(run_baseline(prompt))
