"""Model factory utilities for Deep Agents reporting workflow."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI, ChatOpenAI


@dataclass
class ModelSettings:
    provider: str = "azure"
    model_name: Optional[str] = None
    temperature: float = 1.0
    max_tokens: int = 4000
    max_retries: int = 6


class ModelConfigurationError(RuntimeError):
    """Raised when required model configuration is missing."""


def create_chat_model(settings: ModelSettings):
    """Instantiate a chat model for the workflow based on provider settings."""

    provider = settings.provider.lower()

    if provider == "azure":
        deployment = settings.model_name or os.getenv("AZURE_DEPLOYMENT")
        endpoint = os.getenv("AZURE_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")
        api_version = os.getenv("AZURE_API_VERSION")

        if not all([deployment, endpoint, api_key, api_version]):
            raise ModelConfigurationError(
                "Azure OpenAI configuration incomplete. Ensure AZURE_DEPLOYMENT, "
                "AZURE_ENDPOINT, AZURE_API_KEY, and AZURE_API_VERSION are defined."
            )

        model = AzureChatOpenAI(
            azure_endpoint=endpoint,
            deployment_name=deployment,
            openai_api_key=api_key,
            openai_api_version=api_version,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            max_retries=settings.max_retries,
        )
        
        # Force temperature to 1.0 for models that don't support 0.0
        if hasattr(model, 'temperature'):
            model.temperature = 1.0
        
        return model

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ModelConfigurationError("OPENAI_API_KEY environment variable is required for provider 'openai'.")

        model_name = settings.model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        model = ChatOpenAI(
            model=model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            max_retries=settings.max_retries,
        )
        
        # Force temperature to 1.0 for models that don't support 0.0
        if hasattr(model, 'temperature'):
            model.temperature = 1.0
            
        return model

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ModelConfigurationError(
                "ANTHROPIC_API_KEY environment variable is required for provider 'anthropic'."
            )

        model_name = settings.model_name or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        model = ChatAnthropic(
            model=model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            max_retries=settings.max_retries,
            api_key=api_key,
        )

        return model

    raise ModelConfigurationError(
        f"Unsupported provider '{settings.provider}'. Choose 'azure', 'openai', or 'anthropic'."
    )
