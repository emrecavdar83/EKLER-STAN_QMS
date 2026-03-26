# ANAYASA — Değiştirilemez Kurallar
**EKLERİSTAN QMS v3.2 | Bu dosya T2 işlemi olmadan değiştirilemez.**

---

## KURAL 1 — İsimlendirme
Tüm değişken ve fonksiyon adları **Turkish snake_case** olacak.

```python
# ✅ DOĞRU
belge_id = 1
kullanici_adi = "emre"
def belge_kaydet():

# ❌ YANLIŞ
documentId = 1
userName = "emre"
def saveDocument():
```

---

## KURAL 2 — Zero Hardcode
Hardcode **kesinlikle yasak.** Tüm sabitler ya `CONSTANTS.py`'den ya da `ayarlar_moduller` tablosundan gelecek.

```python
# ✅ DOĞRU
from constants import CONSTANTS
bolum_id = CONSTANTS.SOS_BIRIM_ID  # 18

# ❌ YANLIŞ
bolum_id = 18  # GUARDIAN RED verir
```

**İstisna yok. Guardian bunu her commit'te denetler.**

---

## KURAL 3 — Fonksiyon Boyutu
Her fonksiyon **maksimum 30 satır** olacak.  
30 satırı aşan fonksiyon → yardımcı fonksiyonlara böl.

---

## KURAL 4 — Şirket Adı
Şirket adı her zaman **EKLERİSTAN A.Ş.**  
- ❌ `Ege Hazır Yiyecek San. Tic. A.Ş.` — yasak
- ❌ `Mezzet` — yasak
- ❌ `ekleristan` (küçük harf, A.Ş. yok) — yasak

---

## KURAL 5 — 13. Adam Protokolü
T1 / T2 / T3 işlemlerinden önce **13. Adam Protokolü** zorunlu.  
→ Bkz. `.antigravity/rules/13-adam.md`

---

## KURAL 6 — Guardian Onayı
Guardian **RED** verdiğinde otomatik devam edilmeyecek.  
**İnsan onayı zorunlu.** Onay sonrası Builder'a geri dönülür.

---

## KURAL 7 — Sync Dry Run
Sync Master, Dry Run yapmadan **gerçek sync yapamaz.**  
`sync_log_preview.txt` üretilmeden sync başlatılamaz.

---

## KURAL 8 — Protected Tablolar
Aşağıdaki tablolara dokunmadan önce **ekstra insan onayı** alınacak:

| Tablo | Sebep |
|---|---|
| `personel` | 358 kayıt, kritik |
| `ayarlar_yetkiler` | RBAC, güvenlik kritik |
| `sistem_parametreleri` | Grace Period, oturum ayarları |
| `qdms_belgeler` | Aktif belgeler |

---
 
## KURAL 9 — Teknik Uyumluluk
Her `git push` öncesinde **S6-Protector** tarafından `tech-ledger.md` denetimi yapılır. 
Hata kayıt defterindeki ("TRC", "IND", "PKG", "PTH", "DRI", "REG", "VER") kriterlerine uymayan hiçbir kod canlıya çıkamaz.

---

*Bu kuralları ihlal eden her çıktı → Auditor veya Guardian tarafından durdurulur.*
