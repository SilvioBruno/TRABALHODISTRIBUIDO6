$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
New-Item -ItemType Directory -Force -Path grpc_gen | Out-Null
python -m grpc_tools.protoc -I grpc --python_out=grpc_gen --grpc_python_out=grpc_gen grpc/streaming.proto
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Stubs gerados em grpc_gen"
