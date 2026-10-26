$ErrorActionPreference = 'Stop'
try {
    function Get-AppListeners {
        foreach ($line in (netstat.exe -ano -p tcp)) {
            if ($line -match '^\s*TCP\s+\S+:8000\s+\S+\s+LISTENING\s+(\d+)\s*$') {
                [pscustomobject]@{ OwningProcess = [int]$Matches[1] }
            }
        }
        if ($LASTEXITCODE -ne 0) { throw 'Could not inspect port 8000.' }
    }
    $listeners = @(Get-AppListeners)
    foreach ($processId in @($listeners.OwningProcess | Sort-Object -Unique)) {
        if (-not $processId) { continue }
        $server = Get-CimInstance Win32_Process -Filter "ProcessId = $processId"
        $expectedPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
        if (-not $server.CommandLine -or $server.CommandLine.IndexOf($expectedPython, [StringComparison]::OrdinalIgnoreCase) -lt 0 -or $server.CommandLine -notmatch '(?i)\buvicorn\s+app:app\b') {
            throw "Port 8000 belongs to another process (PID $processId). Close that app before restarting."
        }
        Write-Host "Stopping the previous YouTube Analyzer server (PID $processId)..."
        taskkill.exe /PID $processId /T /F
        if ($LASTEXITCODE -ne 0) { throw "Could not stop the previous server (PID $processId)." }
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            if (-not (Get-AppListeners)) { break }
            Start-Sleep -Milliseconds 200
        }
    }
    if (Get-AppListeners) {
        throw 'Port 8000 is still occupied. Try again after the old server exits.'
    }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
exit 0
