"""Test LiteLLM provider Anthropic api_base support."""

import os

import pytest

from nanobot.providers.litellm_provider import LiteLLMProvider


@pytest.mark.unit
def test_anthropic_detection_with_api_key() -> None:
    """Test Anthropic provider detection with sk-ant- key prefix."""
    provider = LiteLLMProvider(
        api_key="sk-ant-test123",
        api_base=None,
        default_model="anthropic/claude-sonnet-4-5"
    )
    # When api_key starts with sk-ant-, it should be detected as Anthropic
    assert provider.is_anthropic is True
    # is_openrouter should be False when key is sk-ant-
    assert provider.is_openrouter in (False, None)  # None or False both OK
    assert provider.is_vllm is False


@pytest.mark.unit
def test_anthropic_detection_with_model_name() -> None:
    """Test Anthropic provider detection via model name."""
    provider = LiteLLMProvider(
        api_key="any-key",
        api_base=None,
        default_model="anthropic/claude-opus-4-5"
    )
    # When model contains "anthropic" and not OpenRouter, should be Anthropic
    assert provider.is_anthropic is True
    # is_openrouter should be False (or None if not set)
    assert provider.is_openrouter in (False, None)  # None or False both OK
    assert provider.is_vllm is False


@pytest.mark.unit
def test_anthropic_with_custom_api_base() -> None:
    """Test Anthropic provider with custom api_base."""
    custom_base = "https://custom.anthropic.example.com"
    provider = LiteLLMProvider(
        api_key="sk-ant-test123",
        api_base=custom_base,
        default_model="anthropic/claude-sonnet-4-5"
    )
    assert provider.is_anthropic is True
    assert provider.api_base == custom_base


@pytest.mark.unit
def test_anthropic_env_variable_set() -> None:
    """Test that ANTHROPIC_API_KEY is set for Anthropic provider."""
    # Clear any existing value
    original = os.environ.get("ANTHROPIC_API_KEY")
    os.environ.pop("ANTHROPIC_API_KEY", None)

    try:
        LiteLLMProvider(
            api_key="sk-ant-test456",
            api_base=None,
            default_model="anthropic/claude-sonnet-4-5"
        )
        assert os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-test456"
    finally:
        # Restore original value
        if original is not None:
            os.environ["ANTHROPIC_API_KEY"] = original
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.unit
def test_openrouter_not_confused_with_anthropic() -> None:
    """Test that OpenRouter is not detected as Anthropic."""
    provider = LiteLLMProvider(
        api_key="sk-or-test",
        api_base=None,
        default_model="anthropic/claude-sonnet-4-5"
    )
    assert provider.is_openrouter is True
    assert provider.is_anthropic is False
    assert provider.is_vllm is False


@pytest.mark.unit
def test_vllm_not_confused_with_anthropic() -> None:
    """Test that vLLM with api_base is not detected as Anthropic."""
    provider = LiteLLMProvider(
        api_key="dummy-key",
        api_base="http://localhost:8000/v1",
        default_model="claude-sonnet-4-5"
    )
    assert provider.is_vllm is True
    assert provider.is_anthropic is False
    assert provider.is_openrouter is False


@pytest.mark.unit
def test_anthropic_api_base_not_vllm() -> None:
    """Test that Anthropic with api_base is detected as Anthropic, not vLLM."""
    provider = LiteLLMProvider(
        api_key="sk-ant-test",
        api_base="https://custom.example.com",
        default_model="anthropic/claude-sonnet-4-5"
    )
    assert provider.is_anthropic is True
    assert provider.is_vllm is False
    assert provider.is_openrouter is False
