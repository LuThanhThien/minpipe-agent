import requests
import subprocess
import time
from typing import Any, Dict, Optional

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

    def invoke(self, prompt: str) -> str:
        return {}
