# DOC_CONTEXT — BUILDER_BACKEND
Oluşturma: 2026-03-30 05:06
İlgili kütüphaneler: python, sqlalchemy, supabase, reportlab
============================================================

## PYTHON — v3.12.9
### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Tüm dosya yolları için pathlib.Path kullanımı zorunludur.
- ⚠️ Tip ipuçları (type hints) tüm fonksiyon imzalarında bulunmalıdır.

## SQLALCHEMY — v2.0.38
### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Anayasa Madde 16: Yazma işlemlerinde 'with engine.begin() as conn:' zorunludur (Atomic Pattern).
- ❌ 1.4 sürümündeki 'engine.execute()' 2.0'da kaldırılmıştır; mutlaka 'conn.execute()' kullanılmalıdır.

## REPORTLAB — v4.4.10
### Kritik Özellikler
- Platypus: Yüksek seviye layout (Paragraph, Table)
- TTFont: Türkçe karakter destekli font yükleme
- Color / HexColor: Kurumsal renk kodları (#8B0000)

### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Kurumsal QMS döküman standartları (EKL-XXX-YYY) kullanılmalıdır.
- ⚠️ UTF-8 Türkçe karakter sorunu için static/fonts/ altından yükleme zorunludur.

### Hallüsinasyon Tuzakları (Kaçınılacaklar)
- ❌ ReportLab 4.x ile 3.x arasındaki import yapıları değişmiştir (RL_Config). 
