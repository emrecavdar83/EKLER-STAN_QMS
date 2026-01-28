@echo off
echo ===================================================
echo   EKLERISTAN KALITE YONETIM SISTEMI (QMS)
echo   Sistem Baslatiliyor...
echo ===================================================
echo.
echo Gerekli kutuphaneler kontrol ediliyor...
pip install -r requirements.txt > nul 2>&1

echo.
echo Uygulama aciliyor...
echo Lutfen tarayici penceresini kapatmayiniz.
echo.
streamlit run app.py
pause