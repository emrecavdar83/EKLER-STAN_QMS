# STATE MACHINE — QDMS Durum Makinesi
**EKLERİSTAN QMS v3.2 | Bu sıra DEĞİŞTİRİLEMEZ.**

---

## Durum Akışı

```
taslak → incelemede → aktif → arsiv
```

### Geçerli Geçişler

| Kaynak | Hedef | Tetikleyen |
|---|---|---|
| `taslak` | `incelemede` | Yazar gönderir |
| `incelemede` | `aktif` | Yetkili onaylar |
| `incelemede` | `taslak` | Revizyon gerekli |
| `aktif` | `arsiv` | Yeni versiyon yayınlanır |

### Yasak Geçişler ❌

```
arsiv     → aktif       (yasak — geri alma yok)
aktif     → taslak      (yasak — revize için yeni versiyon)
arsiv     → taslak      (yasak)
taslak    → aktif       (yasak — inceleme atlanamaz)
```

---

## Builder İçin Kod Şablonu

```python
from enum import Enum

class BelgeDurumu(Enum):
    TASLAK = "taslak"
    INCELEMEDE = "incelemede"
    AKTIF = "aktif"
    ARSIV = "arsiv"

GECERLI_GECISLER = {
    BelgeDurumu.TASLAK: [BelgeDurumu.INCELEMEDE],
    BelgeDurumu.INCELEMEDE: [BelgeDurumu.AKTIF, BelgeDurumu.TASLAK],
    BelgeDurumu.AKTIF: [BelgeDurumu.ARSIV],
    BelgeDurumu.ARSIV: [],  # Terminal durum
}

def durum_gec(mevcut: BelgeDurumu, yeni: BelgeDurumu) -> bool:
    if yeni not in GECERLI_GECISLER[mevcut]:
        raise ValueError(f"Geçersiz geçiş: {mevcut} → {yeni}")
    return True
```

---

## Önemli Notlar

- Bu state machine `qdms_belgeler` tablosundaki `durum` kolonunu yönetir
- Auditor (S3) bu kuralı **her kod reviewde** denetler
- Builder bu geçişleri **atlatacak kod yazamaz**
- `arsiv` terminal durumudur — geri dönüş yoktur

---

*Bu dosya T2 işlemi olmadan değiştirilemez.*
