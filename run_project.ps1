$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$PythonCommand = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$Arguments = @($args)
if ($Arguments.Count -eq 0) { $Arguments = @("start") }

& $PythonCommand "tools/project_launcher.py" @Arguments
exit $LASTEXITCODE
