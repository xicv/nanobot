"""Test Anthropic api_base support."""

from nanobot.config.schema import Config, ProviderConfig, ProvidersConfig


def test_anthropic_api_base_returned() -> None:
    """Test that get_api_base returns Anthropic api_base when configured."""
    config = Config(
        providers=ProvidersConfig(
            anthropic=ProviderConfig(
                api_key="sk-ant-test",
                api_base="https://custom-anthropic.example.com"
            )
        )
    )
    assert config.get_api_base() == "https://custom-anthropic.example.com"


def test_anthropic_api_base_without_key() -> None:
    """Test that Anthropic api_base is not returned when no API key."""
    config = Config(
        providers=ProvidersConfig(
            anthropic=ProviderConfig(
                api_key="",
                api_base="https://custom-anthropic.example.com"
            )
        )
    )
    # Should return None since no API key is set
    assert config.get_api_base() is None


def test_openrouter_takes_precedence() -> None:
    """Test that OpenRouter takes precedence over Anthropic."""
    config = Config(
        providers=ProvidersConfig(
            openrouter=ProviderConfig(
                api_key="sk-or-test",
                api_base="https://openrouter.ai/api/v1"
            ),
            anthropic=ProviderConfig(
                api_key="sk-ant-test",
                api_base="https://custom-anthropic.example.com"
            )
        )
    )
    assert config.get_api_base() == "https://openrouter.ai/api/v1"


def test_anthropic_api_key_priority() -> None:
    """Test that Anthropic API key is returned when Anthropic is configured."""
    config = Config(
        providers=ProvidersConfig(
            anthropic=ProviderConfig(
                api_key="sk-ant-test123",
                api_base="https://custom-anthropic.example.com"
            )
        )
    )
    assert config.get_api_key() == "sk-ant-test123"


def test_vllm_api_base_still_works() -> None:
    """Test that vLLM api_base still works after Anthropic changes."""
    config = Config(
        providers=ProvidersConfig(
            vllm=ProviderConfig(
                api_key="dummy",
                api_base="http://localhost:8000/v1"
            )
        )
    )
    assert config.get_api_base() == "http://localhost:8000/v1"
