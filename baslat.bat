@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ===================================================
echo   EKLERISTAN KALITE YONETIM SISTEMI - LEGACY
echo   Sistem Baslatiliyor...
echo ===================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo Sanal ortam aktif ediliyor...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Sanal ortam aktif ediliyor...
    call venv\Scripts\activate.bat
) else (
    echo UYARI: Sanal ortam bulunamadi.
)

echo.
echo Uygulama aciliyor...
echo.

python -m streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo Uygulama kapandi.
    pause
)
