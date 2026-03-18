"""Configuration management with YAML loading and Bitwarden credential resolution."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class AuthConfig(BaseModel):
    provider: str = "bitwarden"
    lookup: str = ""
    method: str = "flybuys"  # "flybuys" or "direct" — which login method to use


class BrowserConfig(BaseModel):
    cdp_port: int | None = None  # Calculated from BRAVE_CDP_SLOT env var
    cdp_host: str = "127.0.0.1"
    timeout: int = 30000
    headless: bool = False

    @property
    def cdp_url(self) -> str:
        return f"http://{self.cdp_host}:{self.cdp_port}"


class AntiDetectionConfig(BaseModel):
    min_delay: float = 0.5
    max_delay: float = 2.5
    max_requests_per_minute: int = 30
    inter_key_delay_min: float = 0.05
    inter_key_delay_max: float = 0.15


class StoreConfig(BaseModel):
    store_id: str = "0357"  # Default store
    shopping_method: str = "delivery"  # "delivery" or "clickAndCollect"


class APIConfig(BaseModel):
    base_url: str = "https://www.coles.com.au"
    api_base: str = "https://api.coles.com.au"
    subscription_key: str = ""  # Auto-discovered if empty


class RateLimitConfig(BaseModel):
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0


class ColesConfig(BaseModel):
    site: str = "coles.com.au"
    auth: AuthConfig = AuthConfig()
    browser: BrowserConfig = BrowserConfig()
    anti_detection: AntiDetectionConfig = AntiDetectionConfig()
    store: StoreConfig = StoreConfig()
    api: APIConfig = APIConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()


_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "coles.yaml"


def load_config(path: Path | None = None) -> ColesConfig:
    if path is None:
        path = _DEFAULT_CONFIG_PATH
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    config = ColesConfig(**data)
    # Determine CDP port: COLES_CDP_PORT > BRAVE_CDP_SLOT > YAML value > default slot 5
    env_slot = os.environ.get("BRAVE_CDP_SLOT", "5")
    env_port = os.environ.get("COLES_CDP_PORT")
    if env_port:
        config.browser.cdp_port = int(env_port)
    elif env_slot and env_slot.isdigit():
        config.browser.cdp_port = 61000 + int(env_slot)
    elif config.browser.cdp_port is None:
        # No YAML value and no env var, default to slot 5
        config.browser.cdp_port = 61005
    env_host = os.environ.get("COLES_CDP_HOST")
    if env_host:
        config.browser.cdp_host = env_host
    return config
