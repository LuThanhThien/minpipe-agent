from typing import Any, Dict, Optional, Type

from loguru import logger

from .base_provider import ModelProvider


class ProviderRegistry:
    _registry: Dict[str, Type[ModelProvider]] = {}

    @staticmethod
    def register(provider: Type[ModelProvider]) -> Type[ModelProvider]:
        registry = ProviderRegistry._registry
        if not issubclass(provider, ModelProvider):
            raise TypeError("provider must subclass ModelProvider")
        name = provider.__name__
        if name in registry:
            raise ValueError(f"Already registered provider {name}")
        registry[name] = provider
        logger.info(f"=== Register {name}")
        return provider

    @staticmethod
    def get(
        name: str, default: Optional[Type[ModelProvider]] = None
    ) -> Optional[Type[ModelProvider]]:
        return ProviderRegistry._registry.get(name, default)

    @staticmethod
    def create(config: Dict[str, Any]) -> ModelProvider:
        if not isinstance(config, dict):
            raise TypeError("provider config must be a dictionary")

        name = config.get("name")
        if not name:
            raise ValueError("provider config requires 'name'")

        init_config = config.get("init_config", {})
        if not isinstance(init_config, dict):
            raise TypeError("'init_config' must be a dictionary")

        provider = ProviderRegistry.get(name=name)
        if provider is None:
            raise ValueError(f"Not found: {name}")

        return provider(**init_config)
