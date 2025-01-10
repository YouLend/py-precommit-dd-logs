@echo off
setlocal
set HOOK_DIR=%~dp0

for /f "tokens=*" %%u in ('git config user.name') do set USER_NAME=%%u
for /f "tokens=*" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH_NAME=%%b
for /f "tokens=*" %%e in ('git config user.email') do set USER_EMAIL=%%e
for /f "tokens=*" %%p in ('git rev-parse --show-toplevel') do (
    for %%d in (%%p) do set PROJECT_NAME=%%~nxd
)

echo User Name: %USER_NAME% > "%HOOK_DIR%precommit_output.txt"
echo Branch Name: %BRANCH_NAME% >> "%HOOK_DIR%precommit_output.txt"
echo Email: %USER_EMAIL% >> "%HOOK_DIR%precommit_output.txt"
echo Project Name: %PROJECT_NAME% >> "%HOOK_DIR%precommit_output.txt"

echo. >> "%HOOK_DIR%precommit_output.txt"
echo Pre-commit results: >> "%HOOK_DIR%precommit_output.txt"
echo. >> "%HOOK_DIR%precommit_output.txt"

pre-commit run --hook-stage commit | findstr /v "datadog-metrics" >> "%HOOK_DIR%precommit_output.txt" 2>&1

pre-commit run --hook-stage commit --hook-id datadog-metrics

python "%HOOK_DIR%datadog_metrics.py" "%HOOK_DIR%precommit_output.txt"

if exist "%HOOK_DIR%precommit_output.txt" del "%HOOK_DIR%precommit_output.txt"

endlocal
