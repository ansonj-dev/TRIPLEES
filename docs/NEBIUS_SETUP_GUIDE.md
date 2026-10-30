# Nebius Setup Guide For TRIPLEES

This guide resumes the local setup without creating cloud resources. Keep `SAFE_MODE=true` and never paste credentials into chat, source code, or tracked files.

## Current Workspace State

- `.vscode/mcp.json` matches the official Nebius VS Code stdio configuration.
- `uv` and `uvx` are installed on Windows.
- The official server is in the uv cache, but the attempted start failed during MCP/Pydantic imports.
- Nebius CLI and WSL2 are not installed; no CLI profile or authentication status was verified.
- The supplied project ID has not been confirmed as active.

## Manual Prerequisites

1. Install WSL2 and a Linux distribution using Microsoft's supported installation steps. This is a machine-level change and is left to the user.
2. Open the distribution and install uv and Nebius CLI using their official installers:

	```sh
	curl -LsSf https://astral.sh/uv/install.sh | sh
	curl -sSL https://storage.eu-north1.nebius.cloud/cli/install.sh | bash
	```

	Start a new WSL shell, then verify `uv --version`, `uvx --version`, and `nebius version`. The CLI must be version `0.12.65` or newer. These commands install local developer tools; they do not create Nebius cloud resources.
3. In the Linux terminal, run `nebius profile list` and `nebius profile active`. If no usable profile exists, run `nebius profile create` and complete the browser-based authentication yourself. Choose the intended tenant and project; do not change an existing active project without approval. Do not share command output containing tokens or sensitive identifiers.
4. Install VS Code's WSL support if needed, open this same workspace from the WSL terminal using `code .`, and confirm the VS Code window indicates WSL. The workspace `.vscode/mcp.json` should remain available in that context.
5. In the WSL VS Code window, use the MCP view to start/restart `nebius`. Confirm that startup and initialization succeed, then inspect the listed tool names. Do not treat the current config file alone as a connection test.

The configured command is the official upstream command:

```text
uvx --refresh-package nebius-mcp-server "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
```

The cached version failed with a Pydantic import error in this audit. If the supported official install still fails, stop and capture only the non-secret error text for diagnosis. Do not replace the package source, pin speculative dependencies, or turn safe mode off.

## Read-Only Account Inspection

Only after a successful MCP handshake and profile verification:

1. Run `nebius_profiles` only to confirm profile names/default status; do not retrieve tokens.
2. Run `nebius_available_services` to discover supported service groups.
3. Consult `nebius_cli_help` for each relevant service before composing any command.
4. Use `nebius_cli_execute` only for commands documented as read-only. Safe mode blocks some risky words but is not a full authorization policy.
5. Record tenant/project, region, enabled services, Nemotron models, endpoint/job support, current price, and idle behavior only if returned by authoritative CLI/service documentation. Keep unknown fields marked unknown.

Do not create endpoints, jobs, VMs, storage, networks, or other cloud resources. Do not submit model inference until its pricing and billable behavior are confirmed and the user approves.

## Human Approval Gate

Before any billable operation, present its resource name, model, GPU configuration, region, estimated cost, expected duration, idle billing behavior, and exact stop/delete procedure. Wait for explicit approval. No such action is part of this setup guide.