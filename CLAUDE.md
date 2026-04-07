# CLAUDE.md - EKLERİSTAN QMS (v5.0.0)

## Ajan Sistemi ve Çalışma Prensipleri

Bu proje **Antigravity Pipeline (v5.0)** mimarisi ile yönetilmektedir. Ajan rolleri, yetki matrisi ve akış detayları için → [AGENTS.md](AGENTS.md)

### 🚀 HIZLI AKIŞ KURALI (Anayasa v5.0 Uyumlu)

Her yeni görevde veya oturumda ajan şu hiyerarşiyi izler:

1.  **Hafıza ve Kurallar:** `.antigravity/musbet/hafiza/hafiza_ozeti.md` ve `.antigravity/rules/anayasa.md` (30 Madde) okunur.
2.  **Adım 0 (Planner):** Emre Bey'e 7-15 soru sorulur, kapsam onaylanır.
3.  **8'li Döngü:** `builder_db` -> `builder_backend` -> `builder_frontend` -> `tester` -> `validator` -> `guardian` -> `auditor` -> `sync_master`.
4.  **Onay:** Geliştirme bittikten sonra "Bulut Tarayıcı Doğrulaması" (Madde 15) yapılır.

### 🛠️ Komutlar ve Çalıştırma

*   **Uygulamayı Başlat:** `streamlit run app.py` (veya `baslat.bat`)
*   **Testleri Çalıştır:** `python -m pytest tests/`
*   **Derleme Kontrolü:** `python -m py_compile [dosya_yolu]`
*   **Sistem Haritası:** `.antigravity/musbet/hafiza/sistem_haritasi.md`

### ⚖️ Temel Yasalar (Özet)
*   **Snake Case:** Tüm isimler Türkçe `snake_case` (Örn: `personel_getir`).
*   **Max 30 Satır:** Fonksiyonlar 30 satırı geçemez.
*   **Sıfır Hardcode:** Tüm sabitler `constants.py` veya DB'den gelir.
*   **UPSERT:** Üretim verisinde `DELETE` yasaktır, `UPSERT` esastır.

---
*EKLERİSTAN A.Ş. Kolektif Zeka Sistemi*
