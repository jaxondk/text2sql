import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.llm.providers import get_llm_provider

logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self):
        self.config_dir = os.path.join(os.getcwd(), "data", "config")
        self.llm_config_file = os.path.join(self.config_dir, "llms.json")

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Create config file if it doesn't exist
        if not os.path.exists(self.llm_config_file):
            with open(self.llm_config_file, "w") as f:
                # Add default OpenAI configuration
                default_config = [
                    {
                        "id": "default-openai",
                        "name": "Default OpenAI",
                        "provider": "openai",
                        "model": "gpt-4o",
                        "description": "Default OpenAI GPT-4o model",
                        "config": {},
                    }
                ]
                json.dump(default_config, f, indent=2)

    async def list_llms(self) -> List[Dict[str, Any]]:
        """
        List all available LLM configurations
        """
        configs = self._load_configs()
        return configs

    async def add_llm(
        self,
        name: str,
        provider: str,
        model: str,
        description: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Dict[str, Any] = {},
    ) -> str:
        """
        Add a new LLM configuration
        """
        # Validate provider
        if provider not in await self.list_providers():
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Generate ID
        llm_id = str(uuid.uuid4())

        # Load existing configs
        configs = self._load_configs()

        # Add new config
        new_config = {
            "id": llm_id,
            "name": name,
            "provider": provider,
            "model": model,
            "description": description,
            "config": config,
        }

        # Add API key to config if provided
        if api_key:
            new_config["config"]["api_key"] = api_key

        configs.append(new_config)

        # Save configs
        self._save_configs(configs)

        return llm_id

    async def get_llm(self, llm_id: str):
        """
        Get LLM instance by ID
        """
        # If llm_id is a provider name, get the first config for that provider
        configs = self._load_configs()
        config = None

        for cfg in configs:
            if cfg["id"] == llm_id:
                config = cfg
                break

        # If not found by ID, try to find by provider name
        if not config:
            for cfg in configs:
                if cfg["provider"] == llm_id:
                    config = cfg
                    break

        # If still not found, use the first available config
        if not config and configs:
            config = configs[0]

        if not config:
            raise ValueError(f"No LLM configuration found for ID: {llm_id}")

        # Get provider
        provider_instance = get_llm_provider(
            provider=config["provider"],
            model=config["model"],
            **config.get("config", {}),
        )

        return provider_instance

    async def remove_llm(self, llm_id: str) -> bool:
        """
        Remove an LLM configuration
        """
        configs = self._load_configs()

        # Find config by ID
        for i, config in enumerate(configs):
            if config["id"] == llm_id:
                # Don't remove the last config
                if len(configs) == 1:
                    raise ValueError("Cannot remove the last LLM configuration")

                # Remove from configs
                configs.pop(i)
                self._save_configs(configs)
                return True

        return False

    async def list_providers(self) -> List[str]:
        """
        List all available LLM providers
        """
        # For now, return hardcoded list of supported providers
        return ["openai", "anthropic", "local"]

    def _load_configs(self) -> List[Dict[str, Any]]:
        """
        Load LLM configurations from file
        """
        try:
            with open(self.llm_config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading LLM configs: {str(e)}")
            return []

    def _save_configs(self, configs: List[Dict[str, Any]]):
        """
        Save LLM configurations to file
        """
        try:
            with open(self.llm_config_file, "w") as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving LLM configs: {str(e)}")

    def _get_config_by_id(self, llm_id: str) -> Optional[Dict[str, Any]]:
        """
        Get LLM configuration by ID
        """
        configs = self._load_configs()
        for config in configs:
            if config["id"] == llm_id:
                return config
        return None
