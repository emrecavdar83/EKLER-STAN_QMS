# 13. ADAM PROTOKOLÜ
**EKLERİSTAN QMS v4.1.6 | Her T işleminde bu dosya okunacak.**

---

## Ne Zaman Uygulanır?

| Kod | İşlem | Tetikleyen Durum |
|---|---|---|
| **T1** | Veri sync | SQLite ↔ Supabase sync öncesi |
| **T2** | Kod / mimari değişikliği | Mevcut modül değişimi, refactor |
| **T3** | Yeni modül ekleme | modules/ veya ui/ altına yeni dosya |

---

## Protokol Adımları

T1, T2 veya T3 işlemi başlamadan önce şu 4 soru **sırayla** yanıtlanacak:

### Soru 1 — Veri Kaybı Riski
> Bu işlem herhangi bir veriyi silmez mi, üstüne yazmaz mı, bozar mı?

- Evet → **DUR**, alternatif yol bul
- Hayır → devam

### Soru 2 — Standart İhlali
> BRC v9 / IFS v8 / FSSC v6 / ISO 9001 / AIB standartlarına aykırı bir durum oluşur mu?

- Evet → **DUR**, Auditor'a gönder
- Hayır → devam

### Soru 3 — Geri Alma Planı
> Bu işlem nasıl geri alınır? Rollback adımları neler?

- Plan yoksa → **REVIZE ET**, önce geri alma planı yaz
- Plan varsa → devam

### Soru 4 — En Kötü Senaryo
> Bu işlem tam tersine giderse ne olur? Maksimum hasar nedir?

- Kabul edilemez hasar → **DUR**
- Kabul edilebilir → devam

---

## Karar Matrisi

| Sonuç | Aksiyon |
|---|---|
| ✅ **Devam** | 4 soru geçildi, işleme başla |
| ✋ **Dur** | İnsan onayı olmadan ilerleme |
| 🔄 **Revize** | Planı düzelt, protokolü tekrar çalıştır |

---

## Önemli Notlar

- Claude Opus kullanılıyorsa (mimari karar) → protokol **Opus** ile çalıştırılır
- Zincirde max **3 iterasyon** — 3'te çözüm yoksa dur ve raporla
- Builder bu protokolü atlamaya **yetkili değil**

---

## Örnek: T3 — Yeni Modül Ekleme

```
GÖREV: modules/gunluk_gorev/ modülü eklenecek

13. Adam Kontrolü:
  S1: Mevcut qdms_belgeler tablosu etkilenir mi? → Hayır ✅
  S2: BRC v9 Md.1.1.2 uyumlu mu? → Evet ✅
  S3: Rollback: dosyaları sil, migration geri al ✅
  S4: En kötü senaryo: Streamlit crash → sadece bu modül etkilenir ✅

KARAR: Devam ✅
```
