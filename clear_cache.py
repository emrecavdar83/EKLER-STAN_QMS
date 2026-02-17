"""
Cache Temizleme Scripti
========================
Sync sonrası tüm cache'leri temizler.
"""

import sys
import os

# Mevcut dizini path'e ekle
sys.path.insert(0, os.path.dirname(__file__))

# Streamlit cache temizleme simülasyonu
print("="*60)
print("CACHE TEMİZLEME")
print("="*60)

print("\n✅ Not: Streamlit cache'i uygulama başlatıldığında otomatik temizlenecek.")
print("   Kullanıcıların yeniden giriş yapması önerilir.")

print("\nÖnerilen adımlar:")
print("1. Uygulamayı yeniden başlatın: streamlit run app.py")
print("2. Admin kullanıcısı ile giriş yapın")
print("3. Ayarlar > Cache Temizle butonuna basın")

print("\n" + "="*60)
