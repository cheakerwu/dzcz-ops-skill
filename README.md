# dzcz-merchant-ops

Local merchant/back-office browser automation runner backed by `agent-browser`.

## Architecture

```
dzcz_merchant_ops/
├── core/                    # 核心引擎
│   ├── pipeline.py          # 管道引擎 - 步骤顺序执行 + 重试
│   ├── step.py              # 步骤基类 - 抽象接口 + execute_with_retry
│   ├── context.py           # 执行上下文 - 不可变状态管理
│   ├── retry.py             # 重试策略 - 指数退避 + 抖动
│   └── errors.py            # 错误体系 - BrowserError / InfrastructureError
├── scheduler/               # 调度系统
│   └── lock.py              # 锁管理器 - 配置文件级锁 + 死锁检测
├── monitor/                 # 监控系统
│   ├── logger.py            # 结构化日志 - JSON Lines
│   └── metrics.py           # 指标收集 - 计数器/直方图/p95
├── config/                  # 配置
│   └── platform.py          # 平台适配 - Windows / macOS
└── cli.py                   # CLI 入口
```

### Core Modules

| Module | Purpose |
|--------|---------|
| **Pipeline** | Sequential step execution with per-step retry |
| **Step** | Abstract base with `execute_with_retry()` |
| **Context** | Immutable state passing through pipeline |
| **RetryPolicy** | Exponential backoff with jitter |
| **Errors** | Two hierarchies: BrowserError (UI) + InfrastructureError (platform) |
| **LockManager** | Per-profile async locks with deadlock detection |
| **StructuredLogger** | JSON-lines logging with TaskLog/StepLog |
| **MetricsCollector** | Counters, gauges, histograms with p95 |
| **PlatformAdapter** | Windows / macOS path and browser abstraction |

## Install Runtime Dependencies

Install `agent-browser` first:

```powershell
npm install -g agent-browser
agent-browser install
```

This project itself only uses the Python standard library.

On Windows, prefer the wrapper. It resolves Python from `MERCHANT_OPS_PYTHON`, `HERMES_PYTHON`, the active conda env, local Hermes env candidates, then PATH. It also skips the WindowsApps python alias because that alias exits with 9009 on machines without Store Python installed.

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json doctor
```

If you move the project or want a stricter portable setup, set Python explicitly before calling the wrapper:

```powershell
$env:MERCHANT_OPS_PYTHON="E:\anaconda\envs\Hermes\python.exe"
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json doctor
```

## State Directory

When using `merchant-ops.ps1`, state defaults to a sibling directory next to this repo:

```text
D:\code\dzcz-merchant-ops-data
```

That path is derived from the script location, not hardcoded in the Python CLI. Override it with:

```powershell
$env:DZCZ_MERCHANT_OPS_HOME="D:\code\dzcz-merchant-ops-data"
```

If you call Python directly without the wrapper, the CLI default is:

```text
~/.dzcz-merchant-ops/
```

For Hermes or day-to-day validation, prefer one calling style and keep it
consistent. The wrapper and direct `python -m dzcz_merchant_ops` can otherwise
look at different profile registries and artifact directories.

## Bilibili Validation

Enroll a login profile from any directory:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile enroll `
  --platform bilibili `
  --merchant-key test-account `
  --merchant-name "Bilibili Test Account" `
  --account-label main `
  --home-url https://www.bilibili.com
```

Log in manually in the opened browser. Then check the saved profile:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile check `
  --profile-id bilibili__test-account__main
```

Open a saved profile for manual inspection or login repair:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile open `
  --profile-id bilibili__test-account__main `
  --url https://www.bilibili.com
```

For the most stable current flow, keep one fixed ops session open for the
profile. If the page is logged out, log in manually inside this browser window
first:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json profile open `
  --profile-id bilibili__test-account__main `
  --session bilibili__test-account__main__ops `
  --url https://www.bilibili.com/video/BV1UvXVBnEy6
```

Then run the deterministic like workflow against that already-open session:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task run `
  --workflow bilibili.video.like.fixed `
  --profile-id bilibili__test-account__main `
  --input video_url=https://www.bilibili.com/video/BV1UvXVBnEy6 `
  --reuse-session
```

`--reuse-session` reuses the already-open ops session and then closes the task
browser when the task finishes. Add `--keep-session-open` only when you want to
leave that browser window open for manual follow-up. The runner also parses the
deterministic browser result into `operation_result`; for the like workflow,
`operation_result.confirmed` and `operation_result.after.liked` must be `true`.

The AI-driven workflow still exists as `bilibili.video.like`, but it requires
`AI_GATEWAY_API_KEY`. Use `bilibili.video.like.fixed` for local validation when
no AI gateway is configured.

An example successful `operation_result` looks like this:

```json
{
  "ok": true,
  "confirmed": true,
  "clicked": true,
  "before": {"liked": false, "text": "124"},
  "after": {"liked": true, "text": "125"}
}
```

Report the latest run, including artifact paths, login state, command summaries,
and stale-running diagnostics:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task report
```

Inspect one workflow definition before running it:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json workflow show bilibili.video.like.fixed
```

`bilibili.video.like.fixed` is the first stable validation workflow. Its
definition includes `executor`, `session_policy`, `open_url_input`, phases,
success condition, and failure hints so Hermes can explain what it is about to
run and how success will be confirmed.

Send one test DM:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\code\dzcz-merchant-ops\merchant-ops.ps1" --json task run `
  --workflow bilibili.dm.send `
  --profile-id bilibili__test-account__main `
  --input dm_url=https://message.bilibili.com/ `
  --input message="test message"
```

Use only your own test accounts or accounts that explicitly agreed to receive test messages.

## Hermes

Use `skills/hermes/dzcz-merchant-ops/SKILL.md` as the Hermes skill wrapper. It keeps Hermes thin: Hermes parses the user request and calls this runner; the runner owns profiles, workflows, locks, and artifacts.

## Testing

```powershell
# 运行所有测试
pytest tests/ -v

# 运行测试覆盖率
pytest tests/ --cov=dzcz_merchant_ops --cov-report=term-missing

# 运行集成测试
python tests/integration_test.py
```

**Test Results:**
- Unit tests: 138 passed
- Core module coverage: 95%+

## Cross-Platform

### Windows
- State: `%APPDATA%\dzcz-merchant-ops\`
- Browser: `C:\Program Files\Google\Chrome\Application\chrome.exe`

### macOS
- State: `~/.dzcz-merchant-ops/`
- Browser: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

Platform adapter auto-detects via `os.name` and `sys.platform`. No code changes needed when deploying to macOS.

```bash
# macOS 部署
git clone <repo>
cd dzcz-merchant-ops
pip install -e .
pytest tests/ -v
```
