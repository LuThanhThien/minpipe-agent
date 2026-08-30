from .base_provider import ModelProvider
from .provider_registry import ProviderRegistry


@ProviderRegistry.register
class MonkeyProvider(ModelProvider):
    def __init__(self):
        super().__init__()

    def invoke(self, prompt: str) -> str:
        return "Monkeys like bananas"
