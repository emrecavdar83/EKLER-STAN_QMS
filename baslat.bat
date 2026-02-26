@echo off
setlocal
color 0A
cd /d "%~dp0"

echo ===================================================
echo   EKLERISTAN QMS - LEGACY BOOT
echo ===================================================

:CHECK_VENV
if exist ".venv\Scripts\activate.bat" (
    goto ACTIVATE_DOTVENV
)
if exist "venv\Scripts\activate.bat" (
    goto ACTIVATE_VENV
)
if exist "venv_stable\Scripts\activate.bat" (
    goto ACTIVATE_STABLE
)
echo [WARN] Sanal ortam bulunamadi!
goto START_APP

:ACTIVATE_DOTVENV
echo [.venv] Aktif ediliyor...
call .venv\Scripts\activate.bat
goto START_APP

:ACTIVATE_VENV
echo [venv] Aktif ediliyor...
call venv\Scripts\activate.bat
goto START_APP

:ACTIVATE_STABLE
echo [venv_stable] Aktif ediliyor...
call venv_stable\Scripts\activate.bat
goto START_APP

:START_APP
echo.
echo Uygulama baslatiliyor...
python -m streamlit run app.py

echo.
echo Uygulama %errorlevel% kodu ile kapandi.
pause
