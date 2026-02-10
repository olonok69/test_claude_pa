import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

from utils.config_utils import load_config
from utils.neo4j_utils import determine_environment_key


class AuraCLIError(RuntimeError):
    """Raised when the aura-cli command fails or returns an unexpected payload."""


class Neo4jBackupManager:
    """High level helper around aura-cli for creating and restoring Aura snapshots."""

    SNAPSHOT_SUCCESS_STATES = {"Completed"}
    SNAPSHOT_ERROR_STATES = {"Failed"}
    INSTANCE_SUCCESS_STATES = {"running", "ready"}
    INSTANCE_ERROR_STATES = {"failed", "error", "suspended"}

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        aura_cli_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if config_file:
            self._config_path = Path(config_file).expanduser().resolve()
            config = load_config(config_file)
        else:
            self._config_path = None

        if config is None:
            raise ValueError("Configuration dictionary or config_file path is required")

        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.neo4j_cfg = self.config.get("neo4j", {}) or {}
        self.backup_cfg = (
            self.neo4j_cfg.get("backup")
            or self.config.get("neo4j_backup")
            or {}
        )
        self.reset_cfg = self.backup_cfg.get("reset_workflow") or {}
        self.default_environment = self.neo4j_cfg.get("environment")
        self.poll_interval = int(self.backup_cfg.get("poll_interval_seconds") or 30)
        self.command_timeout = int(self.backup_cfg.get("command_timeout_seconds") or 600)
        self.operation_timeout = int(self.backup_cfg.get("operation_timeout_seconds") or 3600)

        raw_instances = self.backup_cfg.get("instances") or {}
        self.instance_map = {str(key).lower(): value for key, value in raw_instances.items()}

        cli_candidates = [
            aura_cli_path,
            self.backup_cfg.get("aura_cli_path"),
            os.getenv("AURA_CLI_PATH"),
            "aura-cli",
        ]
        self.aura_cli_path = self._resolve_cli_path(cli_candidates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_snapshot(
        self,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
        await_completion: bool = True,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        mapping = self._resolve_instance_entry(environment, instance_id)
        args = [
            "instance",
            "snapshot",
            "create",
            "--output",
            "json",
            "--instance-id",
            mapping["instance_id"],
        ]
        response = self._run_cli_command(args)
        self.logger.debug("Snapshot create response: %s", response)
        snapshot_info = self._extract_data(response)
        snapshot_id = (
            snapshot_info.get("snapshot_id")
            or snapshot_info.get("id")
            or (snapshot_info.get("data") or {}).get("snapshot_id")
            or (snapshot_info.get("data") or {}).get("id")
        )
        if not snapshot_id:
            raise AuraCLIError(
                f"aura-cli did not return a snapshot_id. Response payload: {snapshot_info}"
            )

        if await_completion:
            final_snapshot = self.wait_for_snapshot(
                snapshot_id=snapshot_id,
                environment=mapping["environment"],
                instance_id=mapping["instance_id"],
                poll_interval=poll_interval,
                timeout=timeout,
            )
            return final_snapshot

        return snapshot_info

    def list_snapshots(
        self,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        mapping = self._resolve_instance_entry(environment, instance_id)
        args = [
            "instance",
            "snapshot",
            "list",
            "--output",
            "json",
            "--instance-id",
            mapping["instance_id"],
        ]
        if date:
            args.extend(["--date", date])

        response = self._run_cli_command(args)
        return self._extract_list(response)

    def get_snapshot(
        self,
        snapshot_id: str,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not snapshot_id:
            raise ValueError("snapshot_id is required")

        mapping = self._resolve_instance_entry(environment, instance_id)
        args = [
            "instance",
            "snapshot",
            "get",
            "--output",
            "json",
            "--instance-id",
            mapping["instance_id"],
            snapshot_id,
        ]
        response = self._run_cli_command(args)
        return self._extract_data(response)

    def get_latest_snapshot(
        self,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        snapshots = self.list_snapshots(environment=environment, instance_id=instance_id)
        if not snapshots:
            return None

        snapshots.sort(key=lambda snap: self._parse_timestamp(snap.get("timestamp")), reverse=True)
        return snapshots[0]

    def restore_from_snapshot(
        self,
        environment: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        use_latest_snapshot: bool = False,
        source_instance_id: Optional[str] = None,
        target_instance_id: Optional[str] = None,
        await_completion: bool = True,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        mapping = self._resolve_instance_entry(environment, target_instance_id)
        source_instance = self._resolve_env_reference(source_instance_id) or mapping["source_instance_id"]
        if source_instance == mapping["restore_target_id"]:
            source_instance = None

        if not snapshot_id:
            if not use_latest_snapshot:
                raise ValueError("snapshot_id is required unless use_latest_snapshot=True")
            latest_snapshot = self.get_latest_snapshot(environment=environment, instance_id=source_instance)
            if not latest_snapshot:
                raise AuraCLIError("No snapshots available to restore from")
            snapshot_id = latest_snapshot.get("snapshot_id")

        if not snapshot_id:
            raise AuraCLIError("Unable to determine snapshot_id to restore")

        args = [
            "instance",
            "overwrite",
            mapping["restore_target_id"],
            "--output",
            "json",
        ]
        if source_instance:
            args.extend(["--source-instance-id", source_instance])
        if snapshot_id:
            args.extend(["--source-snapshot-id", snapshot_id])

        response = self._run_cli_command(args)
        result = self._extract_data(response)

        if not await_completion:
            return result

        final_state = self.wait_for_instance_status(
            instance_id=mapping["restore_target_id"],
            desired_statuses=self.INSTANCE_SUCCESS_STATES,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        return final_state

    def backup_reset_restore(
        self,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
        blank_snapshot_id: Optional[str] = None,
        blank_source_instance_id: Optional[str] = None,
        await_completion: bool = True,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a snapshot, reset the instance to a blank snapshot, and restore it back."""

        mapping = self._resolve_instance_entry(environment, instance_id)

        created_snapshot = self.create_snapshot(
            environment=environment,
            instance_id=mapping["instance_id"],
            await_completion=True,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        created_snapshot_id = (
            created_snapshot.get("snapshot_id")
            or created_snapshot.get("id")
            or (created_snapshot.get("data") or {}).get("snapshot_id")
        )
        if not created_snapshot_id:
            raise AuraCLIError("Could not determine snapshot id for created backup")

        blank_snapshot_id = blank_snapshot_id or self.reset_cfg.get("snapshot_id")
        blank_source_instance_id = blank_source_instance_id or self.reset_cfg.get("source_instance_id")
        blank_snapshot_id = self._resolve_env_reference(blank_snapshot_id)
        blank_source_instance_id = self._resolve_env_reference(blank_source_instance_id)

        if not blank_snapshot_id:
            raise AuraCLIError(
                "Blank snapshot id is required. Provide --blank-snapshot-id or define neo4j.backup.reset_workflow.snapshot_id"
            )

        blank_reset_result = self.restore_from_snapshot(
            environment=environment,
            snapshot_id=blank_snapshot_id,
            source_instance_id=blank_source_instance_id,
            target_instance_id=mapping["restore_target_id"],
            await_completion=await_completion,
            poll_interval=poll_interval,
            timeout=timeout,
        )

        final_restore_result = self.restore_from_snapshot(
            environment=environment,
            snapshot_id=created_snapshot_id,
            source_instance_id=mapping["instance_id"],
            target_instance_id=mapping["restore_target_id"],
            await_completion=await_completion,
            poll_interval=poll_interval,
            timeout=timeout,
        )

        return {
            "backup_snapshot": created_snapshot,
            "blank_reset_result": blank_reset_result,
            "final_restore_result": final_restore_result,
        }

    def wait_for_snapshot(
        self,
        snapshot_id: str,
        environment: Optional[str] = None,
        instance_id: Optional[str] = None,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not snapshot_id:
            raise ValueError("snapshot_id is required")

        mapping = self._resolve_instance_entry(environment, instance_id)
        interval = int(poll_interval or self.poll_interval)
        deadline = time.time() + int(timeout or self.operation_timeout)

        self.logger.info(
            "Waiting for snapshot %s on %s to finish...",
            snapshot_id,
            mapping["instance_id"],
        )

        while True:
            snapshot = self.get_snapshot(
                snapshot_id=snapshot_id,
                environment=mapping["environment"],
                instance_id=mapping["instance_id"],
            )
            status = str(snapshot.get("status", "")).strip() or str(snapshot.get("data", {}).get("status", "")).strip()
            if status in self.SNAPSHOT_SUCCESS_STATES:
                self.logger.info("Snapshot %s completed with status %s", snapshot_id, status)
                return snapshot
            if status in self.SNAPSHOT_ERROR_STATES:
                raise AuraCLIError(f"Snapshot {snapshot_id} failed with status {status}")

            if time.time() >= deadline:
                raise TimeoutError(f"Timed out waiting for snapshot {snapshot_id} to complete")

            time.sleep(interval)

    def wait_for_instance_status(
        self,
        instance_id: str,
        desired_statuses: Optional[Sequence[str]] = None,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not instance_id:
            raise ValueError("instance_id is required")

        interval = int(poll_interval or self.poll_interval)
        deadline = time.time() + int(timeout or self.operation_timeout)
        target_statuses = {s.lower() for s in (desired_statuses or self.INSTANCE_SUCCESS_STATES)}

        self.logger.info("Waiting for instance %s to reach %s", instance_id, ",".join(target_statuses))

        while True:
            instance = self.get_instance(instance_id)
            status = str(instance.get("status", "")).lower()

            if status in target_statuses:
                self.logger.info("Instance %s is now %s", instance_id, status)
                return instance
            if status in self.INSTANCE_ERROR_STATES:
                raise AuraCLIError(f"Instance {instance_id} entered error status {status}")

            if time.time() >= deadline:
                raise TimeoutError(f"Timed out waiting for instance {instance_id} to reach {target_statuses}")

            time.sleep(interval)

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        args = [
            "instance",
            "get",
            instance_id,
            "--output",
            "json",
        ]
        response = self._run_cli_command(args)
        return self._extract_data(response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_instance_entry(
        self, environment: Optional[str], instance_override: Optional[str]
    ) -> Dict[str, Any]:
        if instance_override:
            resolved_id = self._normalize_instance_value(
                self._resolve_env_reference(instance_override)
            )
            return {
                "environment": (environment or self.default_environment or "prod").lower(),
                "instance_id": resolved_id,
                "source_instance_id": resolved_id,
                "restore_target_id": resolved_id,
            }

        env_lower, resolved_key = determine_environment_key(environment or self.default_environment, logger=self.logger)
        candidates = [env_lower, resolved_key.lower(), resolved_key]

        entry = None
        for candidate in candidates:
            entry = self.instance_map.get(candidate)
            if entry:
                break

        if entry is None:
            raise AuraCLIError(
                f"No Aura instance mapping found for environment '{env_lower}'. Configure neo4j.backup.instances first."
            )

        normalized = self._normalize_instance_entry(entry)
        normalized["environment"] = env_lower
        return normalized

    def _normalize_instance_entry(self, entry: Any) -> Dict[str, str]:
        if isinstance(entry, str):
            entry_dict: Dict[str, Any] = {"instance_id": entry}
        elif isinstance(entry, dict):
            entry_dict = dict(entry)
        else:
            raise AuraCLIError("Instance mapping must be a string or dict")

        def pick(*keys: str) -> Optional[str]:
            for key in keys:
                if key in entry_dict and entry_dict[key] is not None:
                    return str(entry_dict[key])
            return None

        instance_id = self._resolve_env_reference(
            pick("instance_id", "id", "primary", "default")
        )
        if not instance_id:
            raise AuraCLIError("Instance mapping missing 'instance_id'")

        source_instance_id = self._resolve_env_reference(
            pick("source_instance_id", "source", "source_instance", "source_id")
        ) or instance_id
        restore_target_id = self._resolve_env_reference(
            pick("restore_target_id", "target", "target_instance_id", "restore_target")
        ) or instance_id

        return {
            "instance_id": self._normalize_instance_value(instance_id),
            "source_instance_id": self._normalize_instance_value(source_instance_id),
            "restore_target_id": self._normalize_instance_value(restore_target_id),
        }

    def _resolve_env_reference(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = str(value).strip()
        prefix = "env:"
        if value.lower().startswith(prefix):
            env_var = value[len(prefix) :].strip()
            resolved = os.getenv(env_var)
            if not resolved:
                raise AuraCLIError(
                    f"Environment variable '{env_var}' referenced in backup config is not set"
                )
            return resolved
        return value

    def _normalize_instance_value(self, value: Optional[str]) -> str:
        if not value:
            raise AuraCLIError("Instance identifier cannot be empty")

        trimmed = value.strip()
        if "://" not in trimmed:
            return trimmed

        parsed = urlparse(trimmed)
        host = (parsed.hostname or "").strip()
        if not host:
            return trimmed

        if host.endswith(".databases.neo4j.io"):
            host = host.split(".")[0]
        elif "." in host:
            host = host.split(".")[0]

        return host or trimmed

    def _resolve_cli_path(self, candidates: Sequence[Optional[str]]) -> str:
        search_roots: List[Path] = []
        if self._config_path:
            search_roots.append(self._config_path.parent)
        search_roots.append(Path.cwd())

        for candidate in candidates:
            if not candidate:
                continue
            expanded = os.path.expanduser(str(candidate))
            expanded_path = Path(expanded)

            relative_options = [expanded_path]
            if not expanded_path.is_absolute():
                relative_options.extend(root / expanded_path for root in search_roots)

            for option in relative_options:
                if option.exists():
                    resolved_path = str(option.resolve())
                    self.logger.debug("Using aura-cli at %s", resolved_path)
                    return resolved_path

            discovered = shutil.which(expanded)
            if discovered:
                self.logger.debug("Using aura-cli discovered on PATH at %s", discovered)
                return discovered

        raise FileNotFoundError(
            "Unable to locate aura-cli binary. Install aura-cli or set neo4j.backup.aura_cli_path"
        )

    def _run_cli_command(self, args: Sequence[str], timeout: Optional[int] = None) -> Dict[str, Any]:
        cmd = [self.aura_cli_path] + list(args)
        pretty_cmd = " ".join(cmd)
        self.logger.debug("Running command: %s", pretty_cmd)

        try:
            completed = subprocess.run(  # noqa: S603,S607 - user supplied CLI
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout or self.command_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise AuraCLIError(f"aura-cli command timed out: {pretty_cmd}") from exc

        self.logger.debug(
            "aura-cli exited with %s. STDOUT: %s STDERR: %s",
            completed.returncode,
            completed.stdout.strip(),
            completed.stderr.strip(),
        )

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            raise AuraCLIError(
                f"aura-cli failed (exit {completed.returncode}) while running '{pretty_cmd}'.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            )

        stdout = completed.stdout.strip()
        if not stdout:
            return {}

        return self._parse_cli_output(stdout)

    def _parse_cli_output(self, output: str) -> Dict[str, Any]:
        decoder = json.JSONDecoder()
        stripped = output.lstrip()
        try:
            parsed, _ = decoder.raw_decode(stripped)
            return parsed
        except json.JSONDecodeError as exc:
            raise AuraCLIError(f"Unable to parse aura-cli output as JSON: {output}") from exc

    def _extract_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload:
            return {}
        data = payload.get("data", payload)
        if isinstance(data, list):
            return data[0] if data else {}
        if isinstance(data, dict):
            return data
        return {"data": data}

    def _extract_list(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not payload:
            return []
        data = payload.get("data", payload)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> datetime:
        if not value:
            return datetime.min
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return datetime.min
