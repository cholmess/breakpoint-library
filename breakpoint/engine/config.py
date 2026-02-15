import json
import os
from importlib import resources

from breakpoint.engine.errors import ConfigValidationError
from breakpoint.engine.waivers import parse_waivers


def load_config(config_path: str | None = None, environment: str | None = None) -> dict:
    try:
        default_config = _load_default_config()
        chosen_path = config_path or os.getenv("BREAKPOINT_CONFIG")
        merged_config = default_config
        if chosen_path:
            with open(chosen_path, "r", encoding="utf-8") as f:
                custom = json.load(f)
            merged_config = _deep_merge(default_config, custom)

        chosen_environment = environment or os.getenv("BREAKPOINT_ENV")
        if chosen_environment:
            merged_config = _apply_environment_overrides(merged_config, chosen_environment)
        else:
            merged_config = dict(merged_config)
            merged_config.pop("environments", None)

        _validate_config(merged_config)
        return merged_config
    except ConfigValidationError:
        raise
    except Exception as exc:
        raise ConfigValidationError(str(exc)) from exc


def _load_default_config() -> dict:
    package = "breakpoint.config"
    resource = resources.files(package).joinpath("default_policies.json")
    with resource.open("r", encoding="utf-8") as f:
        return json.load(f)


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_environment_overrides(config: dict, environment: str) -> dict:
    env_map = config.get("environments")
    if env_map is None:
        raise ConfigValidationError(
            f"Config environment '{environment}' was requested, but no 'environments' section exists."
        )
    if not isinstance(env_map, dict):
        raise ConfigValidationError("Config key 'environments' must be a JSON object.")
    if environment not in env_map:
        available = ", ".join(sorted(env_map.keys())) or "(none)"
        raise ConfigValidationError(
            f"Unknown config environment '{environment}'. Available environments: {available}."
        )

    env_override = env_map.get(environment)
    if not isinstance(env_override, dict):
        raise ConfigValidationError(f"Environment override for '{environment}' must be a JSON object.")

    merged = _deep_merge(config, env_override)
    merged.pop("environments", None)
    return merged


def _validate_config(config: dict) -> None:
    _validate_policy_thresholds(config, policy="cost_policy")
    _validate_policy_thresholds(config, policy="latency_policy")
    _validate_drift_thresholds(config)
    parse_waivers(config.get("waivers"))


def _validate_policy_thresholds(config: dict, policy: str) -> None:
    policy_config = config.get(policy, {})
    if not isinstance(policy_config, dict):
        raise ConfigValidationError(f"Config key '{policy}' must be a JSON object.")

    warn_value = policy_config.get("warn_increase_pct")
    block_value = policy_config.get("block_increase_pct")
    if not isinstance(warn_value, (int, float)):
        raise ConfigValidationError(f"Config key '{policy}.warn_increase_pct' must be numeric.")
    if not isinstance(block_value, (int, float)):
        raise ConfigValidationError(f"Config key '{policy}.block_increase_pct' must be numeric.")
    if float(warn_value) < 0 or float(block_value) < 0:
        raise ConfigValidationError(f"Config key '{policy}' thresholds must be >= 0.")
    if float(block_value) < float(warn_value):
        raise ConfigValidationError(
            f"Config key '{policy}.block_increase_pct' must be >= '{policy}.warn_increase_pct'."
        )


def _validate_drift_thresholds(config: dict) -> None:
    drift = config.get("drift_policy", {})
    if not isinstance(drift, dict):
        raise ConfigValidationError("Config key 'drift_policy' must be a JSON object.")

    length_delta = drift.get("warn_length_delta_pct")
    short_ratio = drift.get("warn_short_ratio")
    min_similarity = drift.get("warn_min_similarity")

    if not isinstance(length_delta, (int, float)):
        raise ConfigValidationError("Config key 'drift_policy.warn_length_delta_pct' must be numeric.")
    if float(length_delta) < 0:
        raise ConfigValidationError("Config key 'drift_policy.warn_length_delta_pct' must be >= 0.")

    if not isinstance(short_ratio, (int, float)):
        raise ConfigValidationError("Config key 'drift_policy.warn_short_ratio' must be numeric.")
    if not 0 <= float(short_ratio) <= 1:
        raise ConfigValidationError("Config key 'drift_policy.warn_short_ratio' must be in [0, 1].")

    if not isinstance(min_similarity, (int, float)):
        raise ConfigValidationError("Config key 'drift_policy.warn_min_similarity' must be numeric.")
    if not 0 <= float(min_similarity) <= 1:
        raise ConfigValidationError("Config key 'drift_policy.warn_min_similarity' must be in [0, 1].")
