"""Human-editable TOML company files, adapted to the existing API representation."""
import json
import math
import re
import tomllib
from pathlib import Path


def decode(path):
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        company = raw["company"]
        values = raw["financials"]
        sources = raw.get("sources", {})
        data = dict(company)
        data["schema_version"] = 2
        data["fields"] = {}
        for key, value in values.items():
            if value == "":
                value = None
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError(f"{key}: use a number or empty quotes for missing data")
            data["fields"][key] = {**sources.get(key, {}), "value": value}
        data["models"] = raw.get("models", {})
        data["benchmark"] = raw.get("benchmark", {})
        data["reports"] = raw.get("reports", {})
        research = path.parent / "research" / f"{path.stem}.json"
        data["history"] = json.loads(research.read_text(encoding="utf-8")) if research.exists() else []
        return data
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Repair {path.name}: {error}") from error


def encode(data):
    def identifier(key):
        return key if re.fullmatch(r"[A-Za-z0-9_-]+", key) else json.dumps(key)
    def literal(value):
        if value is None:
            return '""'
        return json.dumps(value, ensure_ascii=False, allow_nan=False)

    lines = ["# COMPANY BRAIN — edit the numbers below and save.",
             '# Missing value = "". Rates are decimals: 0.10 means 10%.',
             "# Money totals are actual PHP; shares are actual share counts.",
             "# Financials are reported data. Models contain editable assumptions.", ""]
    def section(name, values):
        lines.append(f"[{name}]")
        for key, value in values.items():
            if not isinstance(value, dict):
                lines.append(f"{identifier(key)} = {literal(value)}")
        lines.append("")
        for key, value in values.items():
            if isinstance(value, dict):
                section(f"{name}.{identifier(key)}", value)

    section("company", {key: data.get(key, "") for key in ("ticker", "name", "industry", "archetype", "currency", "pse_edge_url", "rationale", "notes")})
    section("financials", {key: field.get("value") for key, field in data["fields"].items()})
    for method, inputs in data.get("models", {}).items():
        section(f"models.{identifier(method)}", inputs)
    lines.extend(["# Source dates and notes — update these when changing a reported figure.", ""])
    for key, field in data["fields"].items():
        section(f"sources.{identifier(key)}", {k: v for k, v in field.items() if k != "value"})
    section("benchmark", data.get("benchmark", {}))
    section("reports", data.get("reports", {}))
    return "\n".join(lines)


def stock_path(root, ticker):
    brain = root / "brain" / f"{ticker}.toml"
    return brain if brain.exists() else root / "stock_data" / f"{ticker}.json"


def stock_paths(root):
    brain = list((root / "brain").glob("*.toml"))
    return sorted(brain or (root / "stock_data").glob("*.json"))
