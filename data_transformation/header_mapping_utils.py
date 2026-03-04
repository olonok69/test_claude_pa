import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def load_header_mappings(config_path: Path) -> Dict[str, Any]:
    """Load header mapping definitions from a JSON config file."""

    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_mapped_value(
    record: Optional[Mapping[str, Any]],
    mapping: Dict[str, List[str]],
    target: str,
    default: Optional[Any] = None,
) -> Any:
    """Return the first matching value for *target* using configured aliases."""

    if not record:
        return default

    for candidate in mapping.get(target, []):
        if candidate in record:
            return record.get(candidate)

    return record.get(target, default)
