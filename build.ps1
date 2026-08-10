param(
  [ValidateSet('help', 'setup', 'backend', 'frontend-dev', 'frontend-build', 'frontend-lint', 'frontend-preview', 'clean')]
  [string]$Task = 'help'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendRoot = Join-Path $repoRoot 'frontend'

function Invoke-CommandInDir {
  param(
    [string]$Command,
    [string[]]$Arguments,
    [string]$WorkingDirectory = $repoRoot
  )

  Push-Location $WorkingDirectory
  try {
    $argumentList = @('/c', $Command) + $Arguments
    $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList $argumentList -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
      exit $proc.ExitCode
    }
  } finally {
    Pop-Location
  }
}

switch ($Task) {
  'help' {
    @(
      'SentXStock commands:',
      '  .\\build.ps1 setup            Install backend + frontend dependencies',
      '  .\\build.ps1 backend          Run Flask backend on http://localhost:5000',
      '  .\\build.ps1 frontend-dev     Run Vite dev server on http://localhost:5173',
      '  .\\build.ps1 frontend-build   Build the React frontend',
      '  .\\build.ps1 frontend-lint    Run the frontend linter',
      '  .\\build.ps1 frontend-preview Preview the production frontend build',
      '  .\\build.ps1 clean            Remove generated frontend dist assets'
    ) | ForEach-Object { Write-Host $_ }
  }
  'setup' {
    Invoke-CommandInDir -Command 'python' -Arguments @('-m', 'pip', 'install', '-r', 'requirements.txt')
    Invoke-CommandInDir -Command 'npm' -Arguments @('install') -WorkingDirectory $frontendRoot
  }
  'backend' {
    Invoke-CommandInDir -Command 'python' -Arguments @('server.py')
  }
  'frontend-dev' {
    Invoke-CommandInDir -Command 'npm' -Arguments @('run', 'dev') -WorkingDirectory $frontendRoot
  }
  'frontend-build' {
    Invoke-CommandInDir -Command 'npm' -Arguments @('run', 'build') -WorkingDirectory $frontendRoot
  }
  'frontend-lint' {
    Invoke-CommandInDir -Command 'npm' -Arguments @('run', 'lint') -WorkingDirectory $frontendRoot
  }
  'frontend-preview' {
    Invoke-CommandInDir -Command 'npm' -Arguments @('run', 'preview') -WorkingDirectory $frontendRoot
  }
  'clean' {
    $distPath = Join-Path $frontendRoot 'dist'
    if (Test-Path $distPath) {
      Remove-Item -Recurse -Force $distPath
    }
  }
}