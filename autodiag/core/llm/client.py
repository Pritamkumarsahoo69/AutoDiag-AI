"""Provider-agnostic LLM interface for AutoDiag-AI."""

import os
import requests
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM generation."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM."""
        pass


class OpenAICompatibleLLM(BaseLLMClient):
    """Client for local OpenAI-compatible endpoints (Ollama, vLLM)."""

    def __init__(self):
        # No cloud calls by default; configure via env vars
        self.base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
        self.model = os.getenv("LLM_MODEL", "llama3")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call the local OpenAI-compatible endpoint returning JSON."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"{{\"error\": \"Failed to call LLM: {str(e)}\"}}"


class MockLLM(BaseLLMClient):
    """Mock LLM client returning deterministic responses for testing."""

    def __init__(self, default_response: str = "{}"):
        self.default_response = default_response
        self.history = []

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self.history.append({"prompt": prompt, "system_prompt": system_prompt})
        return self.default_response
