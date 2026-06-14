---
name: dzcz-merchant-ops
description: Run local merchant/back-office browser automation through the dzcz merchant-ops runner and agent-browser. Use when the user asks Hermes to enroll a login profile, check a saved browser login state, run a merchant operation workflow, explore a browser workflow, or validate Bilibili test flows before moving to real merchant backends.
version: 0.2.0
author: dzcz
license: MIT
platforms: [windows, macos]
metadata:
  hermes:
    tags: [dzcz, merchant-ops, browser-automation, agent-browser, bilibili]
    category: dzcz
---

# DZCZ Merchant Ops

Use this skill as a thin Hermes entrypoint for local browser automation. Do not operate the browser directly when a matching `merchant-ops` runner command exists. The runner owns login profiles, workflow execution, artifacts, and locks.

## Runner

On Windows, call the wrapper by absolute path so Hermes can run it from any working directory:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json <command>
```

The wrapper resolves Python from `MERCHANT_OPS_PYTHON`, `HERMES_PYTHON`, the active conda env, local Hermes env candidates, then PATH. It sets `${DZCZ_MERCHANT_OPS_HOME}` to the project sibling `dzcz-merchant-ops-data` when the variable is not already set.

The runner stores state under `${DZCZ_MERCHANT_OPS_HOME}`:

- `registry.sqlite` for profile and run records
- `profiles/` for agent-browser persistent profile directories
- `workflows/` for user-promoted workflow JSON
- `artifacts/` for screenshots and command logs
- `locks/` for global/profile execution locks

## Profile IDs

Use this format:

```text
platform__merchant-key__account-label
```

Keep `merchant-key` ASCII and path-safe. Store the human-readable shop/account name separately.

Examples:

```text
bilibili__test-account__main
meituan__zs-kr__ops01
```

## Current Workflows

- `bilibili.video.like.fixed`: input `video_url`; deterministic DOM workflow, preferred for local validation
- `bilibili.video.like`: input `video_url`; AI-driven workflow, requires `AI_GATEWAY_API_KEY`
- `bilibili.dm.send`: inputs `dm_url`, `message`
- `bilibili.search.like.first`: input `keyword`; search for videos and like the first result

Treat these as technical validation flows. They prove profile enrollment, profile matching, agent-browser execution, artifact capture, and Hermes invocation before real merchant backends are available.

## Common Commands

Check dependencies:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json doctor
```

Enroll a Bilibili login profile. This opens a browser; the operator logs in manually:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile enroll \
  --platform bilibili \
  --merchant-key test-account \
  --merchant-name "Bilibili Test Account" \
  --account-label main \
  --home-url https://www.bilibili.com
```

Check the saved profile:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile check \
  --profile-id bilibili__test-account__main
```

Open a saved profile for manual inspection or login repair:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile open \
  --profile-id bilibili__test-account__main \
  --url https://www.bilibili.com
```

For the current stable Bilibili validation flow, first open the fixed ops
session and let the operator log in manually if needed:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile open \
  --profile-id bilibili__test-account__main \
  --session bilibili__test-account__main__ops \
  --url https://www.bilibili.com/video/BV1UvXVBnEy6
```

Then run the deterministic workflow against that session:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task run \
  --workflow bilibili.video.like.fixed \
  --profile-id bilibili__test-account__main \
  --input video_url=https://www.bilibili.com/video/BV1UvXVBnEy6 \
  --reuse-session
```

Treat `operation_result.confirmed == true` and
`operation_result.after.liked == true` as the machine-readable success signal.
The AI workflow `bilibili.video.like` requires `AI_GATEWAY_API_KEY`; prefer
`bilibili.video.like.fixed` for local validation.

`--reuse-session` reuses the existing ops session and closes the task browser
after completion. Add `--keep-session-open` only when the operator explicitly
wants the browser window to remain open.

Report the latest or selected run:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task report
```

Inspect one workflow definition:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json workflow show bilibili.video.like.fixed
```

Use `workflow show` when deciding how to explain a workflow before running it.
Stable deterministic workflows include `executor`, `session_policy`,
`open_url_input`, `success_condition`, and `failure_hints`.

Send one test DM:

```bash
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task run \
  --workflow bilibili.dm.send \
  --profile-id bilibili__test-account__main \
  --input dm_url=https://message.bilibili.com/ \
  --input message="test message"
```

## Hermes Behavior

When a user requests an operation:

1. Identify `platform`, `merchant_key` or `profile_id`, workflow, and workflow inputs.
2. If no profile is registered, ask the operator to enroll one.
3. Run the wrapper command with `--json`.
4. Return the runner status, `run_id`, artifact directory, screenshot path, and any error.
5. If status is `failed`, include the runner error and artifact directory.
6. If login expired or requires manual intervention, guide the operator through the login process.

Do not ask for passwords or cookies. Login is done by opening the persistent profile and letting the operator log in manually.

## Login Flow Handling

The runner supports multiple login methods:

- **Password login**: Requires manual intervention
- **SMS verification**: Requires manual intervention (operator receives code)
- **QR code scan**: Requires manual intervention (operator scans with phone)

When a login is required:
1. Runner detects login status via `LoginDetectionStep`
2. If login expired, raises `LoginExpiredError` with `requires_intervention=True`
3. Hermes should guide the operator to complete login manually
4. After login, re-run the workflow

## Error Recovery

The runner automatically recovers from transient errors:

- **BrowserError**: Retries with exponential backoff
- **LoginExpiredError**: Triggers re-login flow
- **PageLoadError**: Reloads page

For permanent errors or manual intervention required, Hermes should:
1. Report the error to the operator
2. Provide guidance on how to fix it
3. Allow re-running the workflow after fix

## Concurrency

The runner serializes execution with a global lock and a per-profile lock. If a lock is held, report that another browser task is running and ask the user to retry after it finishes.

## Migration Notes

Workflow definitions and registry schema are portable. Browser profile directories are not treated as portable across Windows and macOS. On a new Mac, reinstall `agent-browser`, copy workflow/registry metadata if needed, then re-enroll login profiles.

## Architecture

The runner uses a pipeline-based architecture for workflow execution:

- **Pipeline**: Sequential step execution with per-step retry and error recovery
- **Step**: Abstract base with `execute_with_retry()` for BrowserError recovery
- **Context**: Immutable state passing through pipeline
- **RetryPolicy**: Exponential backoff with jitter (configurable)
- **LockManager**: Per-profile async locks with deadlock detection
- **StructuredLogger**: JSON-lines logging with TaskLog/StepLog
- **MetricsCollector**: Counters, gauges, histograms with p95
- **LoginDetectionStep**: Login status detection (password/SMS/QR code)
- **InterventionManager**: Manual intervention handling for complex login flows
- **RecoveryManager**: Error recovery strategies (login, page load, retry)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=dzcz_merchant_ops --cov-report=term-missing

# Integration test
python tests/integration_test.py
```

Core modules have 95%+ test coverage.

## macOS Deployment

```bash
git clone <repo>
cd dzcz-merchant-ops
pip install -e .
pytest tests/ -v
```

Platform adapter auto-detects via `os.name` and `sys.platform`. No code changes needed.
