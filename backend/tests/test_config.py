import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "secret_key",
    [
        "",
        "short",
        "development-only-change-me",
        "replace-with-a-random-32-byte-secret",
        "change_me_in_production_use_a_32_plus_byte_random_hex_string_here",
    ],
)
def test_production_rejects_insecure_secret_key(secret_key: str):
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, app_env="production", secret_key=secret_key)


def test_production_accepts_non_placeholder_secret_key():
    settings = Settings(
        _env_file=None,
        app_env="production",
        secret_key="8fb77c4db3224188a51eefaf4a8f97de",
    )

    assert settings.app_env == "production"
