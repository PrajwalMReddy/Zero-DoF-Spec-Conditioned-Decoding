import os

from llm_client import LLMClient


def test_stream_completion_uses_stub_when_no_key():
    # Ensure no API key is present
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("LLM_API_KEY", None)

    client = LLMClient()
    tokens = list(client.stream_completion(prompt="# Baseline synthesis prompt", temperature=0.2))
    text = "".join(tokens)

    assert "# END" in text or "synthesized_function" in text


def test_high_temperature_inserts_mutation_marker():
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("LLM_API_KEY", None)

    client = LLMClient()
    tokens = list(client.stream_completion(prompt="# baseline", temperature=0.9))
    text = "".join(tokens)

    assert "# mutated" in text
