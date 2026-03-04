#!/usr/bin/env python
"""Dry-run runner that executes both data transformation scripts and compares outputs to current filesystem state.

The script backs up existing outputs, runs the transformers, computes hash-based diffs, reports any changes, and
restores the originals (unless --keep-new is provided) so the working tree stays untouched.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class ScriptSpec:
    name: str
    path: Path
    args: List[str]
    outputs: List[Path]


@dataclass
class CompareResult:
    status: str  # unchanged|new_file|missing_after|missing_before_and_after|changed
    row_delta: Optional[int] = None
    cols_added: Optional[List[str]] = None
    cols_removed: Optional[List[str]] = None
    sample_diff: Optional[str] = None


def backup_outputs(paths: List[Path], backup_dir: Path) -> Dict[Path, Optional[Path]]:
    backups: Dict[Path, Optional[Path]] = {}
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            target = backup_dir / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            backups[path] = target
        else:
            backups[path] = None
    return backups


def restore_outputs(backups: Dict[Path, Optional[Path]]) -> None:
    for original, backup in backups.items():
        if backup and backup.exists():
            shutil.copy2(backup, original)
        elif original.exists():
            original.unlink()


def _load_json_array(path: Path) -> List[Dict]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _collect_keys(records: List[Dict], sample_size: int = 200) -> set:
    keys = set()
    for item in records[:sample_size]:
        if isinstance(item, dict):
            keys.update(item.keys())
    return keys


def _first_diff(before: List[Dict], after: List[Dict]) -> Optional[Tuple[int, str]]:
    limit = min(len(before), len(after))
    for idx in range(limit):
        b = before[idx]
        a = after[idx]
        if b != a:
            differing_keys = []
            if isinstance(b, dict) and isinstance(a, dict):
                for k in sorted(set(b.keys()) | set(a.keys())):
                    if b.get(k) != a.get(k):
                        differing_keys.append(k)
            return idx, (f"Record {idx} differs; differing fields: {', '.join(differing_keys) if differing_keys else 'multiple fields'}")
    if len(before) != len(after):
        return limit, "Records differ after matched prefix (length mismatch)."
    return None


def compare_outputs(backups: Dict[Path, Optional[Path]]) -> Dict[Path, CompareResult]:
    results: Dict[Path, CompareResult] = {}
    for original, backup in backups.items():
        existed_before = backup is not None
        exists_now = original.exists()

        if not existed_before and not exists_now:
            results[original] = CompareResult(status="missing_before_and_after")
            continue
        if existed_before and not exists_now:
            results[original] = CompareResult(status="missing_after")
            continue
        if not existed_before and exists_now:
            results[original] = CompareResult(status="new_file")
            continue

        # Both exist: structural comparison
        before_records = _load_json_array(backup)
        after_records = _load_json_array(original)

        if before_records == after_records:
            results[original] = CompareResult(status="unchanged")
            continue

        before_keys = _collect_keys(before_records)
        after_keys = _collect_keys(after_records)
        cols_added = sorted(list(after_keys - before_keys)) or None
        cols_removed = sorted(list(before_keys - after_keys)) or None
        row_delta = len(after_records) - len(before_records)
        diff_info = _first_diff(before_records, after_records)
        sample_diff = diff_info[1] if diff_info else None

        results[original] = CompareResult(
            status="changed",
            row_delta=row_delta,
            cols_added=cols_added,
            cols_removed=cols_removed,
            sample_diff=sample_diff,
        )
    return results


def run_script(script: ScriptSpec) -> None:
    cmd = [sys.executable, str(script.path)] + script.args
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)


def build_specs(include_legacy: bool) -> List[ScriptSpec]:
    cpc_outputs = [
        DATA_DIR / "cpcn" / "20251201_CPCN24_25_demographics_graphql.json",
        DATA_DIR / "cpcn" / "20251201_eventregistration_CPCN24_25_graphql.json",
        DATA_DIR / "cpcn" / "20251201_eventregistration_CPC25_demographics_graphql.json",
        DATA_DIR / "cpcn" / "20251201_eventregistration_CPC25_graphql.json",
    ]
    lva_outputs = [
        DATA_DIR / "lva" / "20251104_eventregistration_LVS24_graphql.json",
        DATA_DIR / "lva" / "20251127_eventregistration_LVS25_graphql.json",
        DATA_DIR / "lva" / "20251127_eventregistration_LVS24_25_graphql.json",
        DATA_DIR / "lva" / "20251104_eventregistration_LVS24_demographics_graphql.json",
        DATA_DIR / "lva" / "20251127_eventregistration_LVS25_demographics_graphql.json",
        DATA_DIR / "lva" / "20251127_eventregistration_LVS24_25_demographics_graphql.json",
    ]

    if include_legacy:
        cpc_outputs.extend(
            [
                DATA_DIR / "cpcn" / "20251201_CPCN24_25_demographics_legacy.json",
                DATA_DIR / "cpcn" / "20251201_eventregistration_CPCN24_25_legacy.json",
                DATA_DIR / "cpcn" / "20251201_eventregistration_CPC25_demographics_legacy.json",
                DATA_DIR / "cpcn" / "20251201_eventregistration_CPC25_legacy.json",
            ]
        )
        lva_outputs.extend(
            [
                DATA_DIR / "lva" / "20251104_eventregistration_LVS24_legacy.json",
                DATA_DIR / "lva" / "20251127_eventregistration_LVS25_legacy.json",
                DATA_DIR / "lva" / "20251127_eventregistration_LVS24_25_legacy.json",
                DATA_DIR / "lva" / "20251104_eventregistration_LVS24_demographics_legacy.json",
                DATA_DIR / "lva" / "20251127_eventregistration_LVS25_demographics_legacy.json",
                DATA_DIR / "lva" / "20251127_eventregistration_LVS24_25_demographics_legacy.json",
            ]
        )

    specs = [
        ScriptSpec(
            name="CPC",
            path=PROJECT_ROOT / "data_transformation" / "transform_cpc_data.py",
            args=["--legacy"] if include_legacy else [],
            outputs=cpc_outputs,
        ),
        ScriptSpec(
            name="LVA",
            path=PROJECT_ROOT / "data_transformation" / "transform_lva_data.py",
            args=["--legacy"] if include_legacy else [],
            outputs=lva_outputs,
        ),
    ]
    return specs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run transformers and compare outputs to existing files.")
    parser.add_argument("--legacy", action="store_true", help="Include legacy outputs when running scripts.")
    parser.add_argument(
        "--keep-new",
        action="store_true",
        help="Do not restore backed-up outputs after comparison (will leave regenerated files).",
    )
    args = parser.parse_args()

    specs = build_specs(args.legacy)
    all_outputs = [path for spec in specs for path in spec.outputs]

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir)
        backups = backup_outputs(all_outputs, backup_dir)
        comparison_results: Dict[Path, CompareResult] = {}

        try:
            for spec in specs:
                run_script(spec)
            comparison_results = compare_outputs(backups)
        finally:
            if not args.keep_new:
                restore_outputs(backups)

    changed = {p: res for p, res in comparison_results.items() if res.status == "changed"}
    new_files = {p: res for p, res in comparison_results.items() if res.status == "new_file"}
    missing_after = {p: res for p, res in comparison_results.items() if res.status == "missing_after"}

    print("=== Dry-run summary ===")
    print(f"Scripts run: {[spec.name for spec in specs]}")
    print(f"Legacy mode: {args.legacy}")
    print(f"Restored originals: {not args.keep_new}")
    print()

    if changed:
        print("Changed files:")
        for path in sorted(changed):
            res = changed[path]
            parts = [f"row_delta={res.row_delta}"]
            if res.cols_added:
                parts.append(f"cols_added={res.cols_added}")
            if res.cols_removed:
                parts.append(f"cols_removed={res.cols_removed}")
            print(f" - {path.relative_to(PROJECT_ROOT)} | " + "; ".join(parts))
            if res.sample_diff:
                print(f"   sample_diff: {res.sample_diff}")
    else:
        print("No files changed.")

    if new_files:
        print("\nNewly created files:")
        for path in sorted(new_files):
            print(f" - {path.relative_to(PROJECT_ROOT)}")

    if missing_after:
        print("\nMissing after run:")
        for path in sorted(missing_after):
            print(f" - {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
