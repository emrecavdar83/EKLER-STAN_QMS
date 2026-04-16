# EKLERİSTAN QMS - SİSTEM MİMARİ HARİTASI (v6.2.0)

Bu doküman, Anayasa Madde 7 ve v5.0 standartları uyarınca sistemin modüler yapısını, L1-L5 katmanlaşmasını ve veri akışını haritalandırır.

---

## 🏗️ 1. L1 - L5 KATMANLI MİMARİ MİMARİ (Grand Unification)

Sistem, monolitik yapıdan kurtarılarak 5 temel katmanda reorganize edilmiştir:

| Katman | Seviye | Dosyalar | Temel Görev |
| :--- | :--- | :--- | :--- |
| **L1: Giriş & Runtime** | Entry | `app.py`, `logic/app_bootstrap.py` | Uygulama başlangıcı, CSS ve DB Engine init. |
| **L2: Auth & Session** | Session | `logic/app_auth_flow.py`, `logic/security/password.py` | Giriş akışı, Bcrypt zırhı ve Cookie persistence. |
| **L3: Nav & Registry** | Orchestration | `ui/app_navigation.py`, `ui/app_module_registry.py` | Modül kaydı, Dispatcher ve Dinamik Menü. |
| **L4: Operasyonel UI** | Logic | `modules/*`, `ui/*_ui.py` | İş mantığı ve modül arayüzleri. (Anayasa Madde 3: Max 30 satır). |
| **L5: Persistence** | Data | `database/`, `logic/db_writer.py` | Supabase (Primary) ve SQLite (Fallback) katmanları. |

---

## 🔁 2. REFACTORING DURUMU (AŞAMA 3: Grand Unification)

| Adım | Kapsam | Durum | Açıklama |
| :--- | :--- | :--- | :--- |
| **C1** | Dependency Pin | ✅ Tamamlandı | Pandas/SQLAlchemy TypeError giderildi, monkey patch silindi. |
| **C2** | Entry Point Split | ✅ Tamamlandı | `app.py` orkestratör görevine odaklandı (57 satır). |
| **C3** | Logic Extraction | ✅ Tamamlandı | Bootstrap, Auth ve Admin araçları bağımsız modüllere taşındı. |
| **C4** | UI Registry | ✅ Tamamlandı | Modül yönlendirmesi Registry pattern ile dinamikleştirildi. |

---

## 🧠 3. GÜVENLİK VE ERİŞİM (RBAC)

- **Zero-Trust Logic**: Yetkiler `zone_yetki.py` üzerinden her session başında RAM'e yüklenir.
- **Kriptografik İzolasyon**: Şifreleme işlemleri `logic/security/password.py` içinde kapsüllenmiştir.
- **RLS (Supabase)**: Veri seviyesinde güvenlik Supabase RLS politikaları ile sağlanır.

---

## 🚨 4. ANAYASA (V5.0) SEÇİLMİŞ MADDELER

- **Madde 3 (30 Satır)**: Fonksiyonlar 30 satırı geçemez. Geçenler L4 alt-helper'lara bölünür.
- **Madde 5 (Page Config)**: `st.set_page_config` her zaman `app.py`'nin ilk Streamlit çağrısı olmalıdır.
- **Madde 7 (Cloud Primary)**: Otorite daima Supabase'dir. SQLite sadece acil durum yedeğidir.
- **Madde 28 (Devr-ü Teslim)**: Ajanlar arası iş akışı raporlama ve mühürleme ile yürütülür.

---
**Son Güncelleme:** 2026-04-16 15:30 (Istanbul)
**Otorite:** Anayasa v5.0 (v6.2.0 Stabilization)
