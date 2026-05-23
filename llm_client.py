import random
import time
from typing import Generator, Optional


class LLMClient:
    """Stubbed LLM stream manager.

    Replace the stubbed behavior with a real Gemini 2.0 Flash API integration.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def stream_completion(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> Generator[str, None, None]:
        """Stream completion tokens from the LLM.

        This implementation returns a simulated token stream for local testing.
        """
        return self._simulate_stream(prompt, temperature, max_tokens)

    def _simulate_stream(self, prompt: str, temperature: float, max_tokens: int) -> Generator[str, None, None]:
        completion = self._default_stub_completion(prompt, max_tokens)
        if temperature >= 0.7:
            completion = self._mutate_completion(completion)

        for token in completion.split():
            time.sleep(0.002)
            yield token + " "

    def _default_stub_completion(self, prompt: str, max_tokens: int) -> str:
        if "def" in prompt or "class" in prompt:
            return "return x * 2\n# END"
        return "def synthesized_function(x):\n    return x * 2\n# END"

    def _mutate_completion(self, completion: str) -> str:
        tokens = completion.split()
        if not tokens:
            return completion
        insert_index = min(len(tokens) - 1, random.randint(0, len(tokens) - 1))
        tokens.insert(insert_index, "# mutated")
        return " ".join(tokens)
