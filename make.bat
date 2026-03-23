@echo off
set VENV_DIR=.venv
set PYTHON=%VENV_DIR%\Scripts\python.exe
set PIP=%VENV_DIR%\Scripts\pip.exe
set PYINSTALLER=%VENV_DIR%\Scripts\pyinstaller.exe
set PYTEST=%VENV_DIR%\Scripts\pytest.exe
set SPEC_FILE=rest_client.spec
set TARGET_NAME=rest_client
set DIST_DIR=dist

if "%1" == "" goto all
if "%1" == "all" goto all
if "%1" == "help" goto help
if "%1" == "install" goto install
if "%1" == "test" goto test
if "%1" == "build" goto build
if "%1" == "clean" goto clean
if "%1" == "run" goto run
if "%1" == "run-dist" goto run-dist
if "%1" == "archive" goto archive
echo Unknown target: %1
goto help

:all
goto archive

:install
echo Installing dependencies...
%PIP% install -r requirements.txt
%PIP% install pyinstaller
goto end

:test
echo Running tests...
set PYTHONPATH=.
%PYTEST% tests
goto end

:build
echo Building application...
%PYINSTALLER% --clean --noconfirm %SPEC_FILE%
goto end

:archive
call %0 build
for /f %%i in ('%PYTHON% -c "import app; print(app.__version__)"') do set VERSION=%%i
if "%VERSION%" == "" set VERSION=0.1.0
set ARCHIVE_NAME=%TARGET_NAME%-v%VERSION%-windows-x86_64.zip
echo Creating archive %ARCHIVE_NAME%...
if exist "%DIST_DIR%\%ARCHIVE_NAME%" del /q "%DIST_DIR%\%ARCHIVE_NAME%"
powershell -Command "Compress-Archive -Path '%DIST_DIR%\%TARGET_NAME%' -DestinationPath '%DIST_DIR%\%ARCHIVE_NAME%'"
echo Archive created: %DIST_DIR%\%ARCHIVE_NAME%
goto end

:clean
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
goto end

:run
echo Running application...
%PYTHON% -m app.main
goto end

:run-dist
set TARGET_BIN=%DIST_DIR%\%TARGET_NAME%\%TARGET_NAME%.exe
if exist "%TARGET_BIN%" (
    "%TARGET_BIN%"
) else (
    echo Binary not found. Run 'make build' first.
    exit /b 1
)
goto end

:help
echo Available targets:
echo   install   - Install dependencies (including PyInstaller)
echo   build     - Build the application using PyInstaller
echo   archive   - Create a zip archive for Windows distribution
echo   test      - Run unit tests using pytest
echo   clean     - Remove build artifacts
echo   run       - Run the application from source code
echo   help      - Show this help message
goto end

:end
