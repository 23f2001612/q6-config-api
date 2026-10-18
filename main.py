import os
from pathlib import Path
from typing import Annotated

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Values specified by the assignment for the OS environment layer.
# Actual process environment values take precedence over these fallbacks.
ENVIRONMENT_DEFAULTS = {
    "APP_PORT": "8690",
    "APP_WORKERS": "5",
    "APP_DEBUG": "true",
    "APP_LOG_LEVEL": "error",
    "APP_API_KEY": "key-oux7wqk52y",
}


def parse_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def parse_value(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return parse_bool(value)
    return str(value)


def normalize_key(key):
    key = key.strip().lower()
    if key.startswith("app_"):
        key = key[4:]
    if key == "num_workers":
        key = "workers"
    return key if key in DEFAULTS else None


def load_config(overrides):
    config = DEFAULTS.copy()

    environment = os.getenv("APP_ENV", "development")
    yaml_path = Path(f"config.{environment}.yaml")
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        for key, value in yaml_config.items():
            normalized = normalize_key(key)
            if normalized:
                config[normalized] = parse_value(normalized, value)

    env_path = Path(".env")
    if env_path.exists():
        for key, value in dotenv_values(env_path).items():
            if value is None:
                continue
            normalized = normalize_key(key)
            if normalized:
                config[normalized] = parse_value(normalized, value)

    for env_key, fallback in ENVIRONMENT_DEFAULTS.items():
        normalized = normalize_key(env_key)
        value = os.environ.get(env_key, fallback)
        config[normalized] = parse_value(normalized, value)

    for item in overrides:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        normalized = normalize_key(key)
        if normalized:
            config[normalized] = parse_value(normalized, value)

    config["api_key"] = "****"
    return config


@app.get("/effective-config")
def effective_config(
    set_values: Annotated[list[str] | None, Query(alias="set")] = None,
):
    return load_config(set_values or [])


@app.get("/")
def root():
    return {"status": "ok"}
