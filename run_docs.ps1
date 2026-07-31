$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$PythonCommand = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
& $PythonCommand "tools/docs_portal.py" "serve" "--open" @args
exit $LASTEXITCODE
