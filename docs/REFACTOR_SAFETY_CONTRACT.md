# 🛡️ REFAKTÖR GÜVENLİK SÖZLEŞMESİ (ZARAR GÖRMEME İLKESİ)

**Tarih:** 2026-04-28  
**Sürüm:** v6.3.8 → v6.4.0 Refaktör  
**Hazırlayan:** Ajan 0 (Planner) + Emre Bey Onayı  
**Durum:** AKTİF — Bu sözleşme refaktör tamamlanana kadar geçerlidir.

---

## 📸 BAŞLANGIÇ FOTOĞRAFı (BASELINE)

| Metrik | Mevcut Değer | Tarih |
|--------|:---:|:---:|
| **Git Branch** | `main` | 2026-04-28 |
| **Son Commit** | `23ac851` (v6.3.8) | 2026-04-28 |
| **Toplam Test Sayısı** | 217 (collected) | 2026-04-28 |
| **Unit Test Sonucu** | 58 passed, 1 failed, 3 skipped | 2026-04-28 |
| **Integration Test Sonucu** | 77 passed (toplam), 1 failed | 2026-04-28 |
| **Halihazırda Başarısız Testler** | 2 (refaktör öncesi mevcut) | 2026-04-28 |

### Refaktör ÖNCESİ Başarısız Testler (Bizim Sorumluluğumuz DEĞİL)

Bu testler refaktör başlamadan önce zaten başarısızdı:

1. **`test_app_refactor.py::TestModuleRegistry::test_module_registry_has_minimum_modules`**
   - Sebep: Dispatcher branch sayma regex'i güncel mimariyi yakalamıyor (1 branch buluyor, 15 bekliyor)
   - **Mevcut bug — refaktör hedefi dışında**

2. **`test_e2e_organizasyon.py::test_qms_matrix_validation[chromium]`**
   - Sebep: `localhost:8501` — Streamlit sunucusu çalışmıyor, E2E test ortam gereksinimi
   - **Ortam sorunu — refaktör hedefi dışında**

---

## 🚫 ZARAR GÖRMEME İLKELERİ (7 MADDE)

### Madde 1: TEST REGRESYONU YASAK
> Refaktör sonunda mevcut **58 başarılı unit test** ve **77 başarılı integration test** tam olarak aynı sonucu verecektir. **Tek bir yeşil test bile kırmızıya dönerse → tüm değişiklikler geri alınır (rollback).**

### Madde 2: API CONTRACT DOKUNULMAZ
> Hiçbir public fonksiyonun **adı**, **parametreleri** veya **dönüş tipi** değiştirilmeyecektir. İç yapı sadeleşir ama dış arayüz aynı kalır. Kullanıcı hiçbir fark görmez.

### Madde 3: KULLANICI DENEYİMİ BOZULMAZ
> - Login akışı değişmez
> - Form kayıt akışları değişmez
> - Raporlama çıktıları değişmez
> - Menü/navigasyon yapısı değişmez
> - Veritabanındaki mevcut veriye dokunulmaz

### Madde 4: VERİTABANI İÇERİĞİ KORUNUR
> - Mevcut tablolara **DROP**, **ALTER COLUMN**, **DELETE** işlemi uygulanmaz
> - Sadece **CREATE INDEX** (yeni index ekleme) gibi non-destructive DDL izinlidir
> - Mevcut veriye INSERT/UPDATE/DELETE yapılmaz

### Madde 5: GERİ DÖNÜLEBİLİRLİK GARANTİSİ
> Her faz ayrı branch'te yapılır. Sorun olursa:
> ```bash
> git checkout main                    # Ana dalda hiçbir şey olmadı
> git branch -D refactor/faz1-logic   # Sorunlu branch silinir
> ```
> **5 saniyede eski haline dönüş garantisi.**

### Madde 6: DOSYA SİLME YASAĞI
> Scratch arşivleme dahil **hiçbir dosya silinmez**. Sadece `git mv` ile taşınır (geçmiş korunur). Arşivlenen dosyalar `scratch/_archive/` altında kalır.

### Madde 7: ANAYASA UYUMU
> Tüm değişiklikler 8 Katmanlı Antigravity Anayasası'na uygun olacaktır:
> - Madde 3: 30 satır kuralı
> - Madde 4: Cache TTL kuralı  
> - Madde 28: Devr-ü teslim kuralı (ajan arası)

---

## 🔑 ROLLBACK PROSEDÜRÜ

Herhangi bir adımda sorun çıkması halinde:

```bash
# Adım 1: Aktif branch'tan çık
git stash
git checkout main

# Adım 2: Sorunlu branch'ı sil (isteğe bağlı)
git branch -D refactor/fazN-xxx

# Sonuç: Sistem v6.3.8 (23ac851) haline geri döndü
# Toplam süre: <10 saniye
```

---

## ✅ DOĞRULAMA KOMUTU (Her Görev Sonrası Çalıştırılacak)

```bash
# Bu komutu her görev sonrası çalıştır:
python -m pytest tests/ -q --ignore=tests/integration -k "not test_qms_matrix_validation"

# BEKLENEN SONUÇ:
# 58+ passed, <=1 failed, 3 skipped
# (1 failed = test_module_registry_has_minimum_modules — ÖNCEKİ bug)

# KABUL EDİLEMEZ SONUÇ:
# Herhangi bir yeni failed → ROLLBACK
```

---

## 📋 ONAY

| Taraf | İmza | Tarih |
|-------|:---:|:---:|
| Emre Bey (Proje Sahibi) | Onaylandı | 2026-04-28 |
| Ajan 0 (Planner) | Taahhüt edildi | 2026-04-28 |

> **Bu sözleşme, refaktör v6.4.0 etiket commit'ine kadar geçerlidir.**
