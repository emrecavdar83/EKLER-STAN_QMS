# EKLERİSTAN QMS — Uluslararası Standart Uyum Planı
# Oluşturma: 2026-04-12 | Kaynak: Claude Sonnet 4.6 Analizi

---

## TAMAMLANDI ✅

| # | İş | Standart | Commit |
|---|---|---|---|
| 1 | st.spinner kaldırıldı | ISO 25010 Perf | 85aeddb |
| 2 | 9 DB index eklendi | ISO 25010 Perf | 85aeddb |
| 3 | Cache temizleme düzeltildi | ISO 25010 | 112e59a |
| 4 | handle_exception SQL detayı gizliyor | OWASP A05 | 96e7a6c |
| 5 | audit_log_kaydet dosyaya fallback | ISO 9001 | 96e7a6c |
| 6 | QDMS GK denetim kaydı | ISO 9001 | 96e7a6c |
| 7 | 12x st.error(str(e)) → handle_exception | OWASP A05 | 96e7a6c |
| 8 | 16x time.sleep(0.5) kaldırıldı | ISO 25010 Perf | 4bb08f6 |
| 9 | belge_kayit.py denetim kaydı | ISO 9001 | 4bb08f6 |
| 10 | talimat_yonetici.py denetim kaydı | ISO 9001 | 4bb08f6 |
| 11 | QDMS except:pass → loglamalı | ISO 25010 | 4bb08f6 |
| 12 | gunluk_gorev batch hatası loglanıyor | ISO 25010 | 4bb08f6 |
| 13 | Mock tabanlı unit testler | IEEE 730 | 7e0ac4f |

---

## SIRADAKI — DÜŞÜK RİSK 🟢 (Şu an çalışılan)

| # | İş | Standart | Risk | Etki |
|---|---|---|---|---|
| 14 | Orphaned `import time` temizle (4 dosya) | PEP 8 | Sıfır | Temizlik |
| 15 | Login sorgusu cache'lendi | ISO 25010 Perf | Çok düşük | Hız |
| 16 | get_personnel_shift tek bağlantıya indirildi | ISO 25010 Perf | Çok düşük | Hız |
| 17 | context_manager except:pass → log | ISO 25010 | Düşük | Güvenilirlik |
| 18 | soguk_oda_utils except:pass → log | ISO 25010 | Düşük | Güvenilirlik |
| 19 | Form alanlarına max_chars validasyonu | OWASP A03 | Düşük | Güvenlik |
| 20 | belge_listele except:return[] → log | ISO 25010 | Düşük | Güvenilirlik |
| 21 | auth_logic kritik test eklendi | IEEE 730 | Düşük | QA |

---

## ORTA RİSK 🟠 (Sonraki aşama — onay gerekli)

| # | İş | Standart | Risk | Not |
|---|---|---|---|---|
| 22 | app.py modüllere bölünmesi | ISO 25010 Maintain. | Orta | 489 satır → 5-6 dosya |
| 23 | personel_ui.py bölünmesi | ISO 25010 Maintain. | Orta | 450 satır |
| 24 | Type hints eklenmesi | PEP 8 / Google | Orta | Tüm logic/ |
| 25 | Token rotation (session güvenlik) | OWASP A07 | Orta | Auth yeniden yazım |
| 26 | CI/CD pipeline (GitHub Actions) | ISO/IEC 12207 | Orta | Otomasyon |

---

## YÜKSEK RİSK 🔴 (Şimdilik yapılmayacak)

| # | İş | Standart | Risk | Sebep |
|---|---|---|---|---|
| 27 | Türkçe → İngilizce değişken isimleri | PEP 8 | Çok yüksek | 500+ fonksiyon, uygulama kırılabilir |
| 28 | Full dosya yapısı yeniden düzeni | ISO/IEC 12207 | Yüksek | Test olmadan yapılamaz |
| 29 | SQLite tam olarak kaldırılması | — | Yüksek | Offline kullanım kaybedilir |

---

## MEVCUT UYUMLULUK SKORU

| Standart | Başlangıç | Şu An | Hedef |
|---|---|---|---|
| OWASP Top 10 | %55 | %80 | %90 |
| ISO 9001 (denetim izi) | %40 | %75 | %90 |
| ISO 25010 Perf | %50 | %75 | %85 |
| ISO 25010 Maintain. | %45 | %55 | %70 |
| PEP 8 (stil) | %30 | %35 | %50* |
| IEEE 730 (test) | %10 | %20 | %50 |

*Türkçe isimlendirme korunuyor

---
*EKLERİSTAN A.Ş. | Standart Uyum Yol Haritası | v1.0*
