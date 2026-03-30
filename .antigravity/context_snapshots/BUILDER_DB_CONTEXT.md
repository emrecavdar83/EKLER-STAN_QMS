# DOC_CONTEXT — BUILDER_DB
Oluşturma: 2026-03-30 05:06
İlgili kütüphaneler: python, sqlalchemy, sqlite, supabase
============================================================

## PYTHON — v3.12.9
### Kritik Özellikler
- f-strings (advanced): f'{expr=:}' format desteği
- pathlib.Path: Dosya yolu işlemleri için standart
- enum.Enum / StrEnum: Sabit tanımları

### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Tüm dosya yolları için pathlib.Path kullanımı zorunludur.
- ⚠️ Tip ipuçları (type hints) tüm fonksiyon imzalarında bulunmalıdır.

## SQLALCHEMY — v2.0.38
### Kritik Özellikler
- text(): Ham SQL sorgularının güvenli çalıştırılması
- engine.begin(): Context manager tabanlı atomic transaction
- Connection.execute(): Sorgu yürütme

### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Anayasa Madde 16: Yazma işlemlerinde 'with engine.begin() as conn:' zorunludur.
- ⚠️ SQLite için 'PRAGMA journal_mode=WAL' zorunludur.

### Hallüsinasyon Tuzakları (Kaçınılacaklar)
- ❌ 1.4 sürümündeki 'engine.execute()' 2.0'da kaldırılmıştır; mutlaka 'conn.execute()' kullanılmalıdır.
- ❌ Sorgularda ':param' syntax'ı kullanılmalı, SQL injection riski oluşturulmamalıdır.
