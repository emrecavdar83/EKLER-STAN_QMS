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

### 📍 Ders 5: Atomik Modülerleşme (30 Satır Kuralı) (VAKA-036)
**Hata:** 200 satırı aşan UI fonksiyonlarının (monolitik yapı) hem bakımının zor olması hem de Streamlit rerun sırasında tüm modülü hantallaştırması.
**Ders:** Fonksiyonlar 30 satırın altına indirilip atomik helperlara bölündüğünde; kod hem BRCGS denetimlerine (Anayasa m.3) uyumlu hale gelir, hem de sadece değişen alt bileşen tetiklendiği için sistem gözle görülür şekilde hızlanır.

### 📍 Ders 6: Modül İzolasyon Zırhı (Ghosting Barrier) (v6.2.1)
**Hata:** Modüller arası geçişlerde eski modüle ait widget durumlarının (session_state) yeni modüle "hayalet" (shadow) olarak sızması ve sistemin kararsızlaşması.
**Ders:** `app.py` üzerinde merkezi bir `_prefix_map` izolasyon zırhı kurulmalıdır. Modül her değiştiğinde, önceki modüle ait prefix taşıyan tüm `session_state` anahtarları otomatik olarak temizlenmelidir.

### 📍 Ders 7: Sessiz Duplikat Fonksiyon Tuzağı (GP-01 Bulgusu)
**Hata:** `logic/auth_logic.py` içinde `_get_dinamik_modul_anahtari` fonksiyonu iki kez tanımlandı (satır 68 ve satır 164). Python ikinci tanımı kullanır. DB-driven emoji-safe kompleks versiyon (satır 68) ölü kod haline geldi. Sistem statik dict lookup'a düştü.
**Ders:** Her büyük refaktörden sonra `grep -c "^def [fonksiyon_adi]" [dosya]` ile duplikat kontrol yapılmalı. CI'ya AST-tabanlı duplikat def testi eklenmeli.

### 📍 Ders 8: Monolitik Stabilizasyon Paradoksu (Kök Neden 1)
**Hata:** Tek commit'te 519 satır değişimi (Grand Unification) ve ardından 32 dosya (Bcrypt), her seferinde 4-6 acil fix commit'i gerektirdi. Stabilizasyon kendisi destabilize etti.
**Ders:** Stabilizasyon commit'leri en fazla 3 dosya ve tek sorumluluk içermelidir. "Grand X" isimli commit açıldığında Guardian durdurmalı: kapsam büyüklüğü = regresyon riski.

### 📍 Ders 9: RLS Kademeli Uygulama Zorunluluğu
**Hata:** v6.0.0'da 35+ tabloya tek seferde RLS uygulandı. Uygulama kendi yazdığı verileri okuyamaz hale geldi. Hemen ardından MAP ve core modüller kayboldu.
**Ders:** RLS tablo tablo uygulanmalı. Her tablo için: uygula → test et → onraki. Toplu RLS değişikliği Guardian blokajına tabi olmalı.

---
*Mühürleyen: Sistem Mimarı | Düzeltme Planı v1.0 | Tarih: 20.04.2026*
