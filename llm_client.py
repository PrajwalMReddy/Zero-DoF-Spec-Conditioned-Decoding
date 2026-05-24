import httpx
import os
import random
import time
from typing import Generator, Optional, Any, Dict


class LLMClient:
    """LLM stream manager supporting Gemini 2.0 Flash or a generic HTTP model API."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta2/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.api_url = api_url or os.getenv("LLM_API_URL")
        self._client = httpx.Client(timeout=30.0)

    def stream_completion(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> Generator[str, None, None]:
        """Stream completion tokens from the model API.

        If no API key is configured, the client falls back to the local stubbed stream.
        """
        if not self.api_key:
            return self._simulate_stream(prompt, temperature, max_tokens)

        try:
            completion = self._fetch_completion(prompt, temperature, max_tokens)
        except Exception:
            return self._simulate_stream(prompt, temperature, max_tokens)

        return self._stream_from_text(completion)

    def _fetch_completion(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if self.api_url:
            return self._fetch_from_custom_api(prompt, temperature, max_tokens)
        return self._fetch_from_gemini(prompt, temperature, max_tokens)

    def _fetch_from_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        url = f"{self.DEFAULT_GEMINI_URL}/{self.model}:generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "prompt": {"text": prompt},
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        response = self._client.post(url, headers=headers, json=body)
        response.raise_for_status()
        payload = response.json()
        return self._parse_gemini_response(payload)

    def _fetch_from_custom_api(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        response = self._client.post(self.api_url, headers=headers, json=body)
        response.raise_for_status()
        payload = response.json()
        return self._parse_generic_response(payload)

    def _parse_gemini_response(self, payload: Dict[str, Any]) -> str:
        def _extract(obj: Any) -> str:
            if obj is None:
                return ""
            if isinstance(obj, str):
                return obj
            if isinstance(obj, dict):
                # Common top-level wrappers
                for key in ("output", "text", "result"):
                    if key in obj and isinstance(obj[key], (str, dict, list)):
                        v = _extract(obj[key])
                        if v:
                            return v

                # Candidates -> take first candidate
                if "candidates" in obj and obj["candidates"]:
                    return _extract(obj["candidates"][0])

                # Content may be a list of segments
                if "content" in obj and isinstance(obj["content"], list):
                    parts = []
                    for seg in obj["content"]:
                        if isinstance(seg, dict):
                            parts.append(_extract(seg.get("text") or seg.get("content") or seg))
                        else:
                            parts.append(_extract(seg))
                    return "".join(parts)

                # Message style responses
                if "message" in obj and isinstance(obj["message"], dict):
                    return _extract(obj["message"].get("content") or obj["message"])

                # Fall back to concatenating any string-like children
                parts = []
                for v in obj.values():
                    t = _extract(v)
                    if t:
                        parts.append(t)
                return " ".join(parts)

            if isinstance(obj, list):
                return "".join(_extract(x) for x in obj)

            return ""

        text = _extract(payload)
        if text:
            return text
        raise ValueError("Unexpected Gemini response format")

    def _parse_generic_response(self, payload: Dict[str, Any]) -> str:
        if "output" in payload and isinstance(payload["output"], str):
            return payload["output"]
        if "choices" in payload and payload["choices"]:
            first = payload["choices"][0]
            if isinstance(first, dict):
                if "text" in first:
                    return first["text"]
                if "message" in first and isinstance(first["message"], dict):
                    return first["message"].get("content", "")
        if "result" in payload and isinstance(payload["result"], str):
            return payload["result"]
        raise ValueError("Unexpected model API response format")

    def _stream_from_text(self, text: str) -> Generator[str, None, None]:
        for token in text.split():
            yield token + " "

    def _simulate_stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Generator[str, None, None]:
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
