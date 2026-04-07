# /13-adam-check — T1/T2/T3 Kontrol Komutu
**Kullanım:** Herhangi bir T işleminden önce bu komutu çalıştır.**

---

## ŞABLON

```
13. ADAM PROTOKOLÜ — [T1 / T2 / T3] işlemi
İşlem: [ne yapılacak - tek cümle]
Model: Claude Opus 4.6

Aşağıdaki 4 soruyu sırayla yanıtla:

SORU 1 — VERİ KAYBI RİSKİ
Bu işlem herhangi bir veriyi siler mi, üstüne yazar mı, bozar mı?
→ Evet / Hayır + açıklama

SORU 2 — STANDART İHLALİ
BRC v9 / IFS v8 / FSSC v6 / ISO 9001 / AIB standartlarına
aykırı bir durum oluşur mu?
→ Evet / Hayır + etkilenen madde numaraları

SORU 3 — GERİ ALMA PLANI
Bu işlem tersine giderse rollback adımları neler?
→ Adım adım yaz

SORU 4 — EN KÖTÜ SENARYO
Maksimum hasar nedir? Hangi tablolar/modüller etkilenir?
→ Açıkla

KARAR: Devam / Dur / Revize
```

---

## T İşlemi Rehberi

| Sen Ne Yapacaksın | T Kodu |
|---|---|
| SQLite ↔ Supabase sync | T1 |
| Mevcut modül/fonksiyon değiştirme | T2 |
| AGENTS.md veya Anayasa değiştirme | T2 |
| Yeni modül ekleme | T3 |
| Yeni tablo oluşturma | T3 |
| Refactor (mevcut kodu yeniden yazma) | T2 |

---

## Önemli Not

- T2 ve T3 için tercihen **Claude Opus** kullan
- Guardian RED verdikten sonra bu protokol işletilir
- Protokol geçilmeden işleme başlanamaz
