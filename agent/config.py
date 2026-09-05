import importlib.util
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str) -> Dict[str, Any]:
    path = Path(config_path).resolve()
    spec = importlib.util.spec_from_file_location("agent_config", str(path))
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load config file: {path}")

    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    config = getattr(config_module, "CONFIG", None)
    if not isinstance(config, dict):
        raise TypeError(f"Config file must define a dictionary named CONFIG: {path}")
    return config


def resolve_node_provider_config(
    config: Dict[str, Any], node_name: str
) -> Dict[str, Any]:
    if not isinstance(config, dict):
        raise TypeError("CONFIG must be a dictionary")

    if "nodes" in config:
        nodes = config.get("nodes", {})
        assert node_name in nodes, f"CONFIG['nodes']['{node_name}'] is not found"
        node_config = nodes.get(node_name)
        if not isinstance(node_config, dict):
            raise ValueError(f"CONFIG['nodes']['{node_name}'] must be a dictionary")
        return node_config

    if "name" in config:
        return config

    provider_config = config.get("provider")
    if isinstance(provider_config, dict):
        return provider_config

    raise ValueError(f"Could not resolve provider config for node '{node_name}'")
