"""
eco_system — Profile Loader
profiles/base.yaml를 기본값으로, 직무 프로필을 오버레이 방식으로 병합
"""

import os
import yaml
from typing import Any


PROFILES_DIR = os.path.join(os.path.dirname(__file__), "..", "profiles")


def _deep_merge(base: dict, override: dict) -> dict:
    """재귀적 deep merge. override가 base를 덮어씀."""
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_profile(name: str) -> dict[str, Any]:
    """
    프로필 로드. base.yaml을 기반으로 지정 프로필을 오버레이.

    Args:
        name: 프로필 이름 (예: "ra_equity", "quant", "macro")
              "base"를 지정하면 base.yaml만 반환

    Returns:
        병합된 설정 dict

    Example:
        profile = load_profile("ra_equity")
        tickers = profile["data"]["tickers"]["core"]
    """
    base_path = os.path.join(PROFILES_DIR, "base.yaml")
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"base.yaml 없음: {base_path}")

    with open(base_path, encoding="utf-8") as f:
        base = yaml.safe_load(f)

    if name == "base":
        return base

    profile_path = os.path.join(PROFILES_DIR, f"{name}.yaml")
    if not os.path.exists(profile_path):
        available = _list_profiles()
        raise ValueError(
            f"프로필 '{name}' 없음. 사용 가능: {available}\n"
            f"profiles/{name}.yaml을 생성하거나 기존 프로필을 사용하세요."
        )

    with open(profile_path, encoding="utf-8") as f:
        override = yaml.safe_load(f)

    # extends 키 제거 후 병합
    override.pop("extends", None)

    merged = _deep_merge(base, override)
    merged["_profile_name"] = name
    return merged


def _list_profiles() -> list[str]:
    """사용 가능한 프로필 목록 반환 (base 제외)."""
    files = os.listdir(PROFILES_DIR)
    return sorted(
        f.replace(".yaml", "")
        for f in files
        if f.endswith(".yaml") and f != "base.yaml"
    )


def list_profiles() -> None:
    """사용 가능한 프로필 출력."""
    profiles = _list_profiles()
    print("사용 가능한 프로필:")
    for name in profiles:
        path = os.path.join(PROFILES_DIR, f"{name}.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        desc = data.get("description", "")
        print(f"  --profile {name:<15} {desc}")
