# 📝 DERS KAVANOZU (Lessons Learned)

Bu döküman, teknik hatalardan ve krizlerden çıkarılan hayati dersleri içerir.

### 📍 Ders 1: SQLite "Replace" Tuzağı (VAKA-022)
**Hata:** `INSERT OR REPLACE` komutunun SQLite'ta eski satırı tamamen silip (Zone dahil) yeni satır eklemesi.
**Ders:** SQLite'ta metadata (Zone, created_at vb.) sütunlarını korumak için `INSERT OR REPLACE` yerine `ON CONFLICT DO UPDATE` kullanılmalı ve korunacak kolonlar açıkça `COALESCE` veya `CASE` ile belirtilmelidir.

### 📍 Ders 2: Etiket vs Anahtar (Label vs Key) (VAKA-020/021)
**Hata:** Arayüzdeki (UI) modül etiketlerinin (`📦 MAP Üretim`) veritabanındaki yetki tablosuna yazılması, ancak koddaki `JOIN`lerin teknik anahtar (`map_uretim`) araması.
**Ders:** Veritabanındaki yetki tabloları KESİNLİKLE teknik anahtarlara (Slugs) dayalı olmalıdır. UI ve Kod arasında bir "Bridge" (Köprü) fonksiyonu bulunmalıdır.

### 📍 Ders 3: Fail-Closed Prensibi (VAKA-018)
**Hata:** Oturum kapatıldığında veya kullanıcı değiştirildiğinde `st.session_state` temizlenirken navigasyon callback'lerinin (sync_from_sidebar) `AttributeError` vermesi.
**Ders:** Tüm navigasyon ve oturum bazlı erişimler `try-except` bariyeri ile korunmalı ve `st.session_state.get()` varsayılan değerlerle kullanılmalıdır.

### 📍 Ders 4: Zırhlı Tahliye (Logout Persistence) (VAKA-017)
**Hata:** Tarayıcıdaki "Beni Hatırla" çerezinin, kullanıcı çıkış yapsa bile sistemi tekrar otomatik login döngüsüne sokması.
**Ders:** Güvenli çıkış (Logout) işlemi, URL parametreleri (`?logout=1`) üzerinden önceliklendirilmiş bir temizlik tetiklemelidir.

---
*Mühürleyen: Antigravity | Tarih: 30.03.2026*
