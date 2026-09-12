import subprocess

from loguru import logger

from .base_provider import ModelProvider
from .provider_registry import ProviderRegistry


@ProviderRegistry.register
class CopilotProvider(ModelProvider):
    def __init__(
        self,
        timeout: int = 60,
    ):
        super().__init__()
        self.timeout = timeout

    def invoke(
        self,
        prompt: str,
    ) -> str:
        cmd = [
            "copilot",
            "-p",
            prompt,
            "-s",
            "--no-color",
        ]

        logger.debug(
            "Running Copilot CLI: {}",
            " ".join(cmd[:2] + ["<prompt>"] + cmd[3:]),
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Copilot timed out after {self.timeout}s") from exc

        except FileNotFoundError as exc:
            raise RuntimeError("Copilot CLI is not installed or not in PATH") from exc

        if result.returncode != 0:
            raise RuntimeError("Copilot CLI failed:\n" f"{result.stderr.strip()}")

        response = result.stdout.strip()

        if not response:
            raise RuntimeError("Copilot returned an empty response")

        return response
