$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-MerchantOpsPython {
    foreach ($envName in @("MERCHANT_OPS_PYTHON", "HERMES_PYTHON")) {
        $candidate = [Environment]::GetEnvironmentVariable($envName)
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    if ($env:CONDA_PREFIX) {
        $candidate = Join-Path $env:CONDA_PREFIX "python.exe"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    # Local development fallback for this Windows machine. Prefer env vars above for portability.
    foreach ($candidate in @(
        "E:\anaconda\envs\Hermes\python.exe",
        "E:\miniconda3\envs\Hermes\python.exe",
        (Join-Path $env:USERPROFILE "anaconda3\envs\Hermes\python.exe"),
        (Join-Path $env:USERPROFILE "miniconda3\envs\Hermes\python.exe")
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    $pathPython = Get-Command python -ErrorAction SilentlyContinue
    if ($pathPython -and $pathPython.Source -notlike "*\WindowsApps\python.exe") {
        return $pathPython.Source
    }

    throw "Python not found. Set MERCHANT_OPS_PYTHON to the Hermes python.exe path, or activate the Hermes conda environment first."
}

$python = Resolve-MerchantOpsPython

if (-not $env:AGENT_BROWSER_BIN) {
    $candidate = Join-Path $env:APPDATA "npm\agent-browser.cmd"
    if (Test-Path -LiteralPath $candidate) {
        $env:AGENT_BROWSER_BIN = $candidate
    }
}

if (-not $env:DZCZ_MERCHANT_OPS_HOME) {
    $projectParent = Split-Path -Parent $scriptDir
    $env:DZCZ_MERCHANT_OPS_HOME = Join-Path $projectParent "dzcz-merchant-ops-data"
}

Push-Location $scriptDir
try {
    & $python -m dzcz_merchant_ops @args
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $exitCode