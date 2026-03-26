# EKLERİSTAN QMS — TEKNİK HATA KAYIT DEFTERİ (TECH-LEDGER)
**Sürüm:** 1.0 | **Sorumlu:** S6-Protector (Antigravity)

Bu belge, QDMS geliştirme sürecinde yaşanan "Sistemsel Blokaj" (ImportError / IndentationError) krizinden sonra, bu hataların bir daha asla tekrarlanmaması için oluşturulmuştur.

---

## 1. AJAN ÖZELEŞTİRİ RAPORU (POST-MORTEM)

| Ajan | Başarısızlık Nedeni | Alınan Ders |
|---|---|---|
| **S1 Builder** | Windows yerel ortamdaki venv başarısını "Canlı Onayı" saydı. | Linux/Cloud ortamı farklılıklarını (Pathing) varsayma, simüle et. |
| **S2 Tester** | Syntax check (py_compile) yapıp "Logic" onayını atladı. | Sadece derleme değil, runtime bağımlılık testlerini de yap. |
| **S3 Auditor** | Stadart madde uyumuna (BRCGS) daldı, sistem mimarisini unuttu. | Mimari (Init files) denetimi olmadan kod onayı verme. |
| **S4 Guardian** | Veri riskine odaklandı, "Servis Kesintisi" riskini göremedi. | Sistemin %100 "Up" kalması iş sürekliliği kuralıdır. |
| **S5 Sync Master** | Git Push'u "Başarı" saydı, canlı logu görmedi. | Kullanıcıdan "Hatasız Açıldı" teyidi gelmeden turn bitirme. |

---

## 2. TEKNİK KARA LİSTE & ÇÖZÜM MATRİSİ

### TRC-001: Truncation (Kesik Satır) Hatası
- **Belirti:** Traceback'te kod satırının yarım kalması (`...belge`).
- **Neden:** Bazı Cloud IDE/Server'ların uzun import satırlarını taşırken kesmesi.
- **KURAL:** Tüm importlar `from x import (...)` şeklinde çok satırlı (multi-line) yazılmalıdır.

### IND-001: Indentation (Girinti) Karışıklığı
- **Belirti:** `IndentationError: unexpected indent`.
- **Neden:** Windows/Linux arası boşluk (space) ve tab karakterlerinin çatışması.
- **KURAL:** Dosyalar her zaman UTF-8 yazılmalı ve her düzenlemeden sonra `.venv\python -m py_compile` ile denetlenmelidir.

### PKG-001: Package Discovery (Paket Tanımlama)
- **Belirti:** `ImportError: No module named 'modules'`.
- **Neden:** `modules/` ve alt klasörlerde `__init__.py` eksikliği.
- **KURAL:** Her klasörde boş dahi olsa `__init__.py` bulunması zorunludur.

### PTH-001: Path Resolution (Yol Çözümleme)
- **Belirti:** Import hatası (Module not found).
- **Neden:** Mounted src (/mount/src/...) yapısında Python'ın root'u görmemesi.
- **KURAL:** `app.py` dışındaki derin UI dosyalarına `sys.path.append(os.path.join(os.path.dirname(__file__), '..'))` eklenmelidir.

### DRI-001: Architecture Drift (Mimari Sapma)
- **Belirti:** 10 bölümlü Görev Kartı yapısının 3-4 bölüme düşmesi.
- **Neden:** Acil hata onarımı (v4.0.6) sırasında girinti kompleksitesini azaltmak için basitleştirme yapılması.
- **KURAL:** Acil onarımlar sırasında ana mimari (Anayasa m.5) asla terk edilemez.

### REG-001: UI Regression (Arayüz Regresyonu)
- **Belirti:** PDF butonlarının tek tık yerine menü altına gizlenmesi.
- **Neden:** Kullanıcı deneyimi test edilmeden yapılan UI sadeleştirmesi.
- **KURAL:** Mevcut "One-Click" fonksiyonlar asla daha derin menülere taşınamaz.

### VER-002: Version Desync (Versiyon Uyumsuzluğu)
- **Belirti:** AGENTS.md sürümü ile PDF footer sürümünün çelişmesi.
- **Neden:** Global versiyonun (v3.2) güncellenmeden bırakılması ve footer'ın statik bir stringe bağlanması.
- **KURAL:** Versiyon güncellemeleri tüm dökümanlarda (PDF/MD) atomik olarak eş zamanlı yapılmalıdır.

---

## 3. S6-PROTECTOR KONTROL LİSTESİ (PRE-PUSH)
- [ ] Multi-line importlar kontrol edildi mi? (TRC-001)
- [ ] `__init__.py` dosyaları tam mı? (PKG-001)
- [ ] `sys.path` manuel append edildi mi? (PTH-001)
- [ ] Anayasa m.5 (10 Bölüm) korunuyor mu? (DRI-001)
- [ ] Kritik butonlar (PDF) yerinde mi? (REG-001)
- [ ] Global/Local versiyonlar tutarlı mı? (VER-002)
- [ ] venv syntax-check yapıldı mı? (IND-001)

*Son Güncelleme: 2026-03-27 | Denetçi: S6-Protector*
