# Nebius MCP Audit

Audit date: 2026-10-30

## Results

| Check | Result |
| --- | --- |
| Workspace MCP configuration | Present at `.vscode/mcp.json`; valid JSON and valid VS Code stdio-server shape. |
| Configured launcher | `uvx --refresh-package nebius-mcp-server nebius-mcp-server@git+https://github.com/nebius/mcp-server@main`. |
| Safe mode | `SAFE_MODE=true`; preserved. |
| uv/uvx | Installed locally; version `0.12.15`. |
| Nebius MCP package | Present in the local uv cache. The official launcher resolved/downloaded its environment but failed during Python import. |
| Nebius CLI | Not found on PATH or in the standard Windows home install location. |
| WSL2 | Not installed. The official Nebius setup guide requires WSL2 for CLI use on Windows. The install prompt was cancelled. |
| Authentication/profile | Unknown and unverified; no local CLI was available to query profile state. No credentials were read or displayed. |
| MCP handshake | Failed/not completed. Server import terminated before initialization. |
| Connected MCP tools | None discoverable because initialization failed. |
| Nebius cloud access | Not tested; there was no authenticated CLI profile. |

The official Nebius MCP setup guide and README were inspected. They confirm this workspace configuration shape for VS Code and require Nebius CLI version 0.12.65 or newer, a configured CLI profile, Python 3.13 or newer, and uv. The configured source is the official `nebius/mcp-server` repository. Its current cached startup failed with `ImportError: cannot import name 'eval_type_backport' from 'pydantic._internal._typing_extra'` while importing the MCP dependency. The MCP protocol handshake and tool listing therefore could not be tested. No configuration change was needed: its schema and `SAFE_MODE=true` match the official VS Code example.

The official project documents these tools, but they are not available in this uninitialized session:

| Tool | Documented purpose |
| --- | --- |
| `nebius_profiles` | List configured CLI profile names and identify the default profile. |
| `nebius_available_services` | Discover service groups and nested services supported by the installed CLI. |
| `nebius_cli_help` | Retrieve CLI help for a specific service before composing a command. |
| `nebius_cli_execute` | Execute a Nebius CLI command. With safe mode enabled, selected unsafe command words are blocked; this is not a general guarantee that every possible command is read-only. |

Only explicitly documented, read-only commands should be used for account inspection. Do not use the execute tool to create or modify resources. Token/key retrieval is forbidden by the server; safe mode must remain enabled.

## Commands And Checks

- `uv --version` and `uvx --version`: both report `0.12.15`.
- `uv tool list`: no persistent uv tools installed.
- `Get-Command nebius`: no Nebius CLI executable found.
- `wsl.exe -l -q`: WSL is not installed; the offered installation prompt was cancelled.
- `uvx --refresh-package nebius-mcp-server "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main" --help`: package resolution completed, but import failed in the cached MCP/Pydantic dependency before help or server startup.
- PowerShell `ConvertFrom-Json` validation: `.vscode/mcp.json` parsed successfully; `type=stdio`, `command=uvx`, `SAFE_MODE=true`, and official source confirmed.
- Local `GET http://127.0.0.1:8000/api/ai/health`: unavailable because the local API was not running. This endpoint would report backend provider configuration only; it does not test Nebius auth or inference.

The official documentation inspected was `https://github.com/nebius/mcp-server/blob/main/README.md` and `https://github.com/nebius/mcp-server/blob/main/AGENT_SETUP.md`. No TRIPLEES GitHub repository was accessed. No cloud resource or blockchain operation was attempted.

## Blockers

1. Install WSL2 and a supported Linux distribution, then install Nebius CLI 0.12.65 or newer inside that distribution.
2. Resolve the launcher dependency import failure through the official package's supported dependency set; do not switch to another package or disable safe mode.
3. Create/select a Nebius CLI profile interactively and verify it locally without sharing tokens.
4. Open the workspace in VS Code's WSL context and restart the MCP server. Verify the initialization status and tool list in VS Code before any account inspection.

The user-supplied project identifier was not verified as active and is intentionally omitted from this audit.