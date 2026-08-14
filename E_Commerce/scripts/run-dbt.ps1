param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$DbtArgs
)
  
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir '..')

# Ensure we are running from the root of the dbt project
Set-Location $repoRoot

# 1. Format the command string for dynamic logging
$commandString = if ($DbtArgs.Count -gt 0) { $DbtArgs -join " " } else { "build" }

# 2. Run dbt (Defaulting to 'dbt build' if no arguments are given)
if ($DbtArgs.Count -gt 0) {
    Write-Host "🚀 Executing custom command: dbt $commandString" -ForegroundColor Cyan
    & dbt @DbtArgs
} else {
    Write-Host "🚀 Executing full build: dbt build" -ForegroundColor Cyan
    & dbt build
}

# 3. Capture the exit code of dbt
$dbtExitCode = $LASTEXITCODE

# 4. If dbt failed, automatically trigger the AI Agent
if ($dbtExitCode -ne 0) {
    Write-Host "`n⚠️ dbt $commandString failed!" -ForegroundColor Red
    Write-Host "🤖 Launching Autonomous dbt Debugger Agent..." -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------" -ForegroundColor Yellow
    
    # Run the Python agent script
    python dbt_agent.py
    
    # Exit with dbt's error code for CI/CD compatibility
    exit $dbtExitCode
} else {
    Write-Host "`n✅ dbt $commandString completed successfully! No errors detected." -ForegroundColor Green
}