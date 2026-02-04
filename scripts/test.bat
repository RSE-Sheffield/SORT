@echo off
setlocal EnableDelayedExpansion

echo Running flake8 on home...
flake8 home
if %ERRORLEVEL% neq 0 (
    echo Flake8 failed for home
    exit /b 1
)

echo Running flake8 on survey...
flake8 survey
if %ERRORLEVEL% neq 0 (
    echo Flake8 failed for survey
    exit /b 1
)

echo Running Django tests for home...
python manage.py test home/tests --parallel=auto --failfast
if %ERRORLEVEL% neq 0 (
    echo Django tests failed for home
    exit /b 1
)

echo Running Django tests for survey...
python manage.py test survey/tests --parallel=auto --failfast
if %ERRORLEVEL% neq 0 (
    echo Django tests failed for survey
    exit /b 1
)

echo Running npm tests...
npm test
if %ERRORLEVEL% neq 0 (
    echo npm tests failed
    exit /b 1
)

echo.
echo All tests passed successfully!
exit /b 0