from datetime import timedelta
import tomllib
from pydantic import BaseModel

# TODO: validate config

class AlertConfig(BaseModel):
    execution_max_time: timedelta
    reconcile_max_time: timedelta
    domains: list[int]

class AlertProviderConfig(BaseModel):
    channel_id: int
    app_token: str

class ChainConfig(BaseModel):
    chain_id: int
    domain_id: int
    core_contract: str

class ProviderConfig(BaseModel):
    url: str
    type: str
    from_block: str = ""

class SchedulerConfig(BaseModel):
    conn_str: str

class Config(BaseModel):
    max_worker: int = 8
    chains: dict[str, ChainConfig]
    providers: dict[str, ProviderConfig]
    alert_providers: dict[str, AlertProviderConfig]
    alerts: AlertConfig
    scheduler: SchedulerConfig

def load_config(config_file) -> Config:
    data = {}
    with open(config_file, 'rb') as f:
        data = tomllib.load(f)
    return Config(**data)
