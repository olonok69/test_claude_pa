# Neo4j Aura Backup Guide

This guide explains how to install and configure the Aura backup wrapper that lives in this repository, and how to run common backup and restore operations for our PA Neo4j instances.

## 1. Prerequisites

1. **Python environment** – use the repo's virtual environment (`.venv`) so the helper script can import the PA package.
2. **aura-cli binary** – download the latest release from <https://github.com/neo4j/cli/releases> and place `aura-cli.exe` somewhere you can run (for example `D:\repos\PA\aura-cli\aura-cli.exe`).
3. **Aura API credentials** – create a client ID and secret via Aura Console → *Account settings → API keys*. Keep both values handy; the secret is only shown once.

## 2. Install and register aura-cli

1. Download `aura-cli_windows_amd64.exe` and rename it to `aura-cli.exe`.
2. Place it in `D:\repos\PA\aura-cli\` (or another folder). Update `neo4j.backup.aura_cli_path` in [PA/config/neo4j_backup_config.yaml](PA/config/neo4j_backup_config.yaml) if the path differs.
3. Add your Aura API key to the CLI:

   ```powershell
   D:\repos\PA\aura-cli\aura-cli.exe credential add \
       --name "PA Aura Production" \
       --client-id <YOUR_CLIENT_ID> \
       --client-secret <YOUR_CLIENT_SECRET>
   D:\repos\PA\aura-cli\aura-cli.exe credential use "PA Aura Production"
   ```

The backup wrapper reuses whichever credential is set as the default in aura-cli.

## 3. Environment variables

Populate `PA/keys/.env` with the Neo4j connection URIs and passwords. The helper script automatically loads `PA/keys/.env` plus any extra `--env-file` you pass. Required variables:

```
NEO4J_URI_PROD=neo4j+s://<instance_id>.databases.neo4j.io
NEO4J_PASSWORD_PROD=<password>
NEO4J_URI_TEST=...
NEO4J_URI_DEV=...
```

Optional overrides:

```
AURA_CLI_PATH=D:/tools/aura-cli.exe
AURA_BLANK_SNAPSHOT_ID=<uuid>
AURA_BLANK_SOURCE_ID=<instance_id_that_holds_blank_snapshot>
```

`env:` placeholders in the YAML will pull from these entries.

## 4. Configure `neo4j_backup_config.yaml`

File: [PA/config/neo4j_backup_config.yaml](PA/config/neo4j_backup_config.yaml)

Key sections:

```yaml
neo4j:
  environment: "prod"
  backup:
    aura_cli_path: "D:\\repos\\PA\\aura-cli\\aura-cli.exe"
    poll_interval_seconds: 30
    command_timeout_seconds: 900
    reset_workflow:
      snapshot_id: "env:AURA_BLANK_SNAPSHOT_ID"
      source_instance_id: "env:AURA_BLANK_SOURCE_ID"
    instances:
      prod:
        instance_id: "env:NEO4J_URI_PROD"
        source_instance_id: "env:NEO4J_URI_PROD"
        restore_target_id: "env:NEO4J_URI_PROD"
      test:
        instance_id: "env:NEO4J_URI_TEST"
      dev:
        instance_id: "env:NEO4J_URI_DEV"
```

The wrapper normalizes URI values into Aura instance IDs automatically.

## 5. Backup CLI usage

Run commands from the repo root (after activating the virtual environment). All examples load the default `.env` file:

```powershell
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env <command> [options]
```

### 5.1 Create snapshot

```powershell
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env \
       create --environment prod --await
```

- `--await` waits until Aura reports `status: Completed`.
- Use `--instance-id` to override the instance mapping.

### 5.2 List and inspect snapshots

```powershell
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env list --environment prod
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env \
       get --environment prod <snapshot_id>
```

### 5.3 Restore from a snapshot

```powershell
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env \
       restore --environment prod --snapshot-id <uuid> --await
```

- `--latest` can be used instead of `--snapshot-id` to pick the most recent snapshot from the mapped instance.
- `--source-instance-id` allows cloning from a different Aura instance.

### 5.4 Full cycle (backup → reset → restore)

```powershell
python -m PA.scripts.neo4j_backup_cli --env-file PA\keys\.env \
       cycle --environment prod --blank-snapshot-id <blank_uuid> --await
```

This command:
1. Creates a new snapshot of the target instance.
2. Overwrites the instance with the specified blank snapshot (or values from `reset_workflow`).
3. Restores the snapshot created in step 1.

Each stage waits for completion when `--await` is used, and the command emits a JSON object containing the three results.

### 5.5 Raw aura-cli invocation

If you need to inspect or debug, run aura-cli directly:

```powershell
D:\repos\PA\aura-cli\aura-cli.exe instance snapshot create --instance-id c60e8856 --output json
D:\repos\PA\aura-cli\aura-cli.exe instance snapshot list --instance-id c60e8856 --output json
```

The Python wrapper logs these commands at DEBUG level (`--log-level DEBUG`) along with stdout/stderr.

## 6. Blank/template snapshots

Aura overwrites always require a source snapshot. To reset an instance to "blank":

1. Create a small Aura instance (or reuse an existing one) that contains the template state.
2. Run `aura-cli instance snapshot create --instance-id <template>` and note the `snapshot_id`.
3. Store the ID (and optionally the template's instance ID) in environment variables or directly in `reset_workflow`.
4. Use the `cycle` command or a manual `restore` pointing at that snapshot whenever you need to wipe the target instance.

## 7. Troubleshooting

- **`default credential not set`** – run `aura-cli credential use <name>`.
- **`credentials invalid/expired`** – delete the stored credential, generate a new API key in Aura Console, and add it again.
- **`Access is denied`** – ensure `aura-cli.exe` is a valid executable and that your user has execute permission (avoid zero-byte placeholder files).
- **`aura-cli did not return a snapshot_id`** – rerun with `--log-level DEBUG` to see the raw stdout/stderr; most often Aura returned an error message explaining the issue.

## 8. Downloading snapshots

AuraDB Professional lets you export completed snapshots, but the download still happens through the Aura Console UI. Use the console to download a completed snapshot (for example `36baa7d5-4f25-4f24-8aff-01ef84a82a48`) after the CLI reports it as `exportable: true`.

---

With this setup the entire backup workflow (create, list, restore, full cycle) can be performed from the repo using `PA/scripts/neo4j_backup_cli.py`. Keep the Aura CLI credential current and ensure the `.env` file has the correct instance URIs so the wrapper can resolve the right targets.
