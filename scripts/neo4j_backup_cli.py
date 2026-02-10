"""Lightweight CLI wrapper around Neo4jBackupManager."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Iterable

# Ensure 'PA' package root is importable when running as a standalone script.
if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from utils.neo4j_backup_manager import AuraCLIError, Neo4jBackupManager
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATHS = [
    REPO_ROOT / "PA" / "keys" / ".env",
    REPO_ROOT / "keys" / ".env",
]

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "neo4j_backup_config.yaml"
)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def load_env_files(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path:
            continue
        expanded = Path(path).expanduser()
        if expanded.exists():
            load_dotenv(expanded, override=False)


def handle_create(args: argparse.Namespace, manager: Neo4jBackupManager) -> Any:
    return manager.create_snapshot(
        environment=args.environment,
        instance_id=args.instance_id,
        await_completion=args.await_completion,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


def handle_list(args: argparse.Namespace, manager: Neo4jBackupManager) -> Any:
    snapshots = manager.list_snapshots(
        environment=args.environment,
        instance_id=args.instance_id,
        date=args.date,
    )
    return {"snapshots": snapshots}


def handle_get(args: argparse.Namespace, manager: Neo4jBackupManager) -> Any:
    snapshot = manager.get_snapshot(
        snapshot_id=args.snapshot_id,
        environment=args.environment,
        instance_id=args.instance_id,
    )
    return snapshot


def handle_restore(args: argparse.Namespace, manager: Neo4jBackupManager) -> Any:
    return manager.restore_from_snapshot(
        environment=args.environment,
        snapshot_id=args.snapshot_id,
        use_latest_snapshot=args.use_latest_snapshot,
        source_instance_id=args.source_instance_id,
        target_instance_id=args.target_instance_id,
        await_completion=args.await_completion,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


def handle_cycle(args: argparse.Namespace, manager: Neo4jBackupManager) -> Any:
    return manager.backup_reset_restore(
        environment=args.environment,
        instance_id=args.instance_id,
        blank_snapshot_id=args.blank_snapshot_id,
        blank_source_instance_id=args.blank_source_instance_id,
        await_completion=args.await_completion,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Aura snapshots for project Neo4j databases",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to a YAML config file that contains neo4j.backup definitions",
    )
    parser.add_argument(
        "--env-file",
        action="append",
        help="Additional .env file to load before resolving environment variables (can be repeated)",
    )
    parser.add_argument(
        "--aura-cli-path",
        help="Optional override for the aura-cli binary to execute",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create an on-demand snapshot")
    create_parser.add_argument("--environment", "-e", help="Logical environment to target (prod/dev/test)")
    create_parser.add_argument("--instance-id", help="Override the instance id instead of config mapping")
    create_parser.add_argument("--poll-interval", type=int, help="Seconds between polling attempts")
    create_parser.add_argument("--timeout", type=int, help="Seconds to wait for completion")
    create_parser.add_argument(
        "--await",
        dest="await_completion",
        action="store_true",
        help="Wait until the snapshot status is Completed",
    )
    create_parser.set_defaults(func=handle_create)

    list_parser = subparsers.add_parser("list", help="List recent snapshots")
    list_parser.add_argument("--environment", "-e", help="Logical environment to target")
    list_parser.add_argument("--instance-id", help="Override the instance id")
    list_parser.add_argument("--date", help="Optional YYYY-MM-DD filter")
    list_parser.set_defaults(func=handle_list)

    get_parser = subparsers.add_parser("get", help="Inspect a single snapshot")
    get_parser.add_argument("snapshot_id", help="Snapshot identifier to inspect")
    get_parser.add_argument("--environment", "-e", help="Logical environment to target")
    get_parser.add_argument("--instance-id", help="Override the instance id")
    get_parser.set_defaults(func=handle_get)

    restore_parser = subparsers.add_parser("restore", help="Overwrite an instance from a snapshot")
    restore_parser.add_argument("--environment", "-e", help="Logical environment to target")
    restore_parser.add_argument("--snapshot-id", dest="snapshot_id", help="Snapshot identifier to restore")
    restore_parser.add_argument(
        "--latest",
        dest="use_latest_snapshot",
        action="store_true",
        help="Automatically pick the most recent completed snapshot",
    )
    restore_parser.add_argument(
        "--source-instance-id",
        help="Override the source instance when copying data",
    )
    restore_parser.add_argument(
        "--target-instance-id",
        help="Override the instance that will be overwritten",
    )
    restore_parser.add_argument("--poll-interval", type=int, help="Seconds between status checks")
    restore_parser.add_argument("--timeout", type=int, help="Seconds to wait for completion")
    restore_parser.add_argument(
        "--await",
        dest="await_completion",
        action="store_true",
        help="Wait until the target instance is running again",
    )
    restore_parser.set_defaults(func=handle_restore)

    cycle_parser = subparsers.add_parser(
        "cycle",
        help="Create a backup, reset the instance with a blank snapshot, then restore the backup",
    )
    cycle_parser.add_argument("--environment", "-e", help="Logical environment to target")
    cycle_parser.add_argument("--instance-id", help="Override the instance id to operate on")
    cycle_parser.add_argument(
        "--blank-snapshot-id",
        help="Snapshot identifier representing a blank database state",
    )
    cycle_parser.add_argument(
        "--blank-source-instance-id",
        help="Source instance that owns the blank snapshot (if different)",
    )
    cycle_parser.add_argument("--poll-interval", type=int, help="Seconds between status checks")
    cycle_parser.add_argument("--timeout", type=int, help="Seconds to wait for each operation")
    cycle_parser.add_argument(
        "--await",
        dest="await_completion",
        action="store_true",
        help="Wait until each overwrite completes",
    )
    cycle_parser.set_defaults(func=handle_cycle)

    return parser


def main(argv: Any = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "restore" and not (args.snapshot_id or args.use_latest_snapshot):
        parser.error("restore command requires --snapshot-id or --latest")

    configure_logging(args.log_level)
    logger = logging.getLogger("neo4j_backup_cli")

    env_paths = list(DEFAULT_ENV_PATHS)
    if args.env_file:
        env_paths.extend(Path(p) for p in args.env_file)
    load_env_files(env_paths)

    try:
        manager = Neo4jBackupManager(
            config_file=args.config,
            aura_cli_path=args.aura_cli_path,
            logger=logging.getLogger("neo4j_backup"),
        )
        result = args.func(args, manager)
        if result is not None:
            print_json(result)
    except (AuraCLIError, ValueError, FileNotFoundError, TimeoutError) as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
