# EKLERİSTAN QMS - v4.0.0 Dinamik Sistem Mimarisi (Güncelleme Eki)

Bu belge, `TEKNIK_DOKUMANTASYON.pdf` (v1.5) ile sistemin şu anki **Cloud-Primary & Otonom İş Akış Motoru (v4.0.0+)** arasındaki yapısal farkları, yeni "beyin" tablolarını ve senkronizasyon protokollerini içerir.

## 1. Yeni Sistem "Beyin" Tabloları

EKLERİSTAN QMS, v3.x güncellemelerinden itibaren yalnızca statik kayıtları (`depo_giris_kayitlari`, vb.) saklamakla kalmayıp, personelin günlük ve anlık iş yükünü takip eden proaktif bir sisteme evrilmiştir.

### 1.1 `gunluk_gorev_katalogu` (Görev Bankası)

Tüm manuel veya rutin atanabilecek işlerin standartlaştırıldığı tanımlama tablosudur.

*   **id:** (INTEGER/SERIAL) Primary Key
*   **kod:** (VARCHAR 50) Eşsiz standart referans kodu (Örn: TEST_01, HIG_05). QMS v4.0.0 ile eklenmiştir.
*   **ad:** (TEXT) Sorumluluk veya iş tanımı
*   **kategori:** (TEXT) Operasyonel, Temizlik, Hijyen, Sistem
*   **aktif_mi:** (INTEGER/BOOLEAN) 1/0
*   **aciklama:** (TEXT) Detaylı görev yönergesi
*   **olusturma_tarihi:** (TIMESTAMP)

### 1.2 `birlesik_gorev_havuzu` (Dinamik İş Akış Motoru)

Sistemin kalbidir. Kullanıcıların portalında gördüğü tüm tamamlanması gereken işler (periyodik görevler, ad-hoc tanımlar, kalite red aksiyonları) bu havuzda toplanır.

*   **id:** Primary Key
*   **personel_id:** (INTEGER) Görevin atandığı personel (FK: personel.id)
*   **bolum_id:** (INTEGER) Eğer görev bölüm bazlı takipse (FK: ayarlar_bolumler.id)
*   **gorev_kaynagi:** (VARCHAR 50) İşlem motorunun kaynağı (`PERIYODIK`, `KATALOG`, `AD-HOC`, `QDMS` vb.)
*   **kaynak_id:** (INTEGER) Kaynağa göre bağlanan ID (Eğer kaynak KATALOG ise `katalog_id`)
*   **gorev_adi:** (VARCHAR 200) Görevin açık adı. (*v4.0 Onarım ekiyle dahil olmuştur*)
*   **ad_ozel:** (VARCHAR 200) `AD-HOC` görevler için manuel belirlenen isim.
*   **v_tipi:** (VARCHAR 50) İşin tipi (Örn: KATALOG veya AD-HOC)
*   **atanma_tarihi:** (DATE) Sisteme girildiği gün
*   **hedef_tarih:** (DATE) Tamamlanması beklenen gün
*   **durum:** (TEXT) `BEKLIYOR`, `TAMAMLANDI`, `IPTAL`
*   **oncelik:** (VARCHAR 50) `NORMAL`, `KRITIK`, `DUSUK`
*   **sapma_notu:** (TEXT) Zamanında bitmeyen işin gerekçesi
*   **tamamlanma_tarihi:** (TIMESTAMP) Tamamlandığı kesin an
*   **atayan_id:** (INTEGER) Ad-Hoc atamayı yapan yöneticinin ID'si
*   **iptal_notu / iptal_eden_id:** (TEXT / INTEGER) Eğer görev iptal edilirse işlem detayları.

### 1.3 `gunluk_periyodik_kurallar` (Cron Mimarisinin Veritabanı Yansıması)

Periyodik (Günlük/Haftalık vb.) görevlerin her açılışta `birlesik_gorev_havuzu`na enjektör tarafından basılmasını sağlayan şablonlardır.

## 2. Navigasyon ve Otonomi Mimarisi (VAKA-008 Çözümü)

**Sorun:** Streamlit Cloud ortamında Dropdown (Selectbox) ve Sidebar Radio arasında "Session State" yönetiminde çıkan uyuşmazlıklar "Navigation/Refresh Loop" oluşturuyordu.

**Çözüm:** Tüm navigasyon bileşenleri (`🏠 ANA MENÜ` ve `HIZLI ERİŞİM`) doğrudan değişken atamak yerine `on_change` **Callback Mimarisi**ne geçirildi.

```python
def on_nav_change(source):
    new_label = st.session_state[source]
    st.session_state.active_module_key = LABEL_TO_SLUG.get(...)
```

Bu yöntem sayesinde menü durumu (State Sync) garanti edilmiş olup, `app.py` yeniden çalıştırıldığında (rerun) arayüz stabilitesi korunmaktadır.

## 3. Bulut-Öncelikli (Cloud-Primary) İşleyiş

Eskiden `ekleristan_local.db`'ye kaydedilip Sync Agent ile buluta yansıtılan "Symmetric Twin" mimarisi, DDL (CREATE/ALTER) hatalarını yuttuğu (v3.2.7 kaosu) için feshedilmiştir.
Sistem %100 doğrudan `aws-1-ap-south-1.pooler.supabase.com:6543` veritabanına sorgu atar.

### 3.1 DDL (Tablo Değiştirme) Kuralları

SQLAlchemy 2.0+ standartlarına göre tüm yazma (INSERT, UPDATE) ve şema (ALTER, CREATE) komutları **ZORUNLU** olarak şu şekilde yapılır:

```python
# YANLIŞ/SESSİZ HATA
with engine.connect() as conn:
    conn.execute(sql) # Autocommit kapalıysa Supabase'de veri yutulur!

# DOĞRU VE ATOMİK
with engine.begin() as conn:
    conn.execute(sql) # Hata çıkmazsa commit eder, çıkarsa rollback yapar.
```

## 4. Anayasa Madde 19 - Yasal UX Standardı Yönergesi

Mevcut tüm modüllerin QDMS stili 10-bölümlük standarta geçirilmesi zorunludur.

1.  **Güvenlik:** `@st.cache_data` yerine dinamik Session sorguları (RBAC).
2.  **Veri Katmanı:** `with engine.begin()` kuralı.
3.  **UI:** `st.header`, 3 Sütunlu Matrix, `st.tabs` kullanımı.
4.  **Error Handling:** "Fail-Silent" mekanizması, try-except kapsüllemeleri.
