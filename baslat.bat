@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ===================================================
echo   EKLERİSTAN KALİTE YÖNETİM SİSTEMİ (QMS)
echo   Sistem Başlatılıyor...
echo ===================================================
echo.

:: Sanal ortam kontrolü
if exist ".venv\Scripts\activate.bat" (
    echo Sanal ortam (.venv) algılandı, aktif ediliyor...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Sanal ortam (venv) algılandı, aktif ediliyor...
    call venv\Scripts\activate.bat
) else (
    echo UYARI: Sanal ortam bulunamadı. Sistem Python'u kullanılacak.
    echo Sanal ortam kullanmanız tavsiye edilir.
)

echo.
echo Gerekli kütüphaneler kontrol ediliyor...
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [HATA] Kütüphane kurulumunda bir sorun oluştu!
        echo Lütfen internet bağlantınızı ve Python kurulumunuzu kontrol edin.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [UYARI] requirements.txt dosyası bulunamadı, kütüphane kontrolü geçiliyor.
)

echo.
echo Uygulama açılıyor...
echo Lütfen tarayıcı penceresini kapatmayınız.
echo.

python -m streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo Uygulama beklenmedik bir şekilde kapandı.
    pause
)