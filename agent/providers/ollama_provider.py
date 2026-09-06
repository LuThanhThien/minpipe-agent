import requests
import subprocess
import time
from typing import Any, Dict, Optional

from loguru import logger

from .base_provider import ModelProvider
from .provider_registry import ProviderRegistry


@ProviderRegistry.register
class OllamaProvider(ModelProvider):
    def __init__(
        self,
        model: str = "qwen2.5-coder:0.5b",
        base_url: str = "http://localhost:11434",
        auto_pull: bool = True,
        timeout: int = 60,
    ):
        super().__init__()

        self.model = model
        self.base_url = base_url
        self.auto_pull = auto_pull
        self.timeout = timeout
        self._ollama_process: Optional[subprocess.Popen] = None

    def _start_server(self) -> None:
        if self._ollama_process and self._ollama_process.poll() is None:
            return

        self._ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _get_tags(self) -> Dict[str, Any]:
        last_error = None
        for should_start in (False, True):
            if should_start:
                logger.info("Starting Ollama server with 'ollama serve'")
                self._start_server()

            deadline = time.time() + 20
            while time.time() < deadline:
                try:
                    response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    last_error = e
                    time.sleep(0.5)

            if should_start:
                break

        raise ConnectionError(
            f"Failed to connect to Ollama server at {self.base_url}. "
            f"Attempted to run 'ollama serve'. Error: {last_error}"
        )

    def _ensure_model(self) -> None:
        payload = self._get_tags()
        model_names = {m.get("name", "") for m in payload.get("models", [])}
        if self.model in model_names:
            return

        if not self.auto_pull:
            raise ValueError(
                f"Model '{self.model}' not found on Ollama server. "
                "Set auto_pull=True to automatically install the model."
            )

        logger.info(f"Model '{self.model}' not found. Pulling from Ollama registry")
        subprocess.run(["ollama", "pull", self.model], check=True)
        logger.info(f"Model '{self.model}' installed successfully")

    def _check_ollama_server(self) -> None:
        self._ensure_model()

    def invoke(self, prompt: str) -> str:
        self._check_ollama_server()
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()["response"]
