# TEST PLANI: Günlük Görev Matrisi
## 1. Happy Path
- `gorev_katalogu_getir`: Aktif görevlerin listelendiği test.
- `periyodik_gorev_ata`: Normal atama listesi ile başarılı atama.
- `personel_gorev_getir`: Atanan görevin ilgili tarihte çekilmesi.
- `gorev_tamamla`: Atanmış görevin "TAMAMLANDI" durumuna geçmesi.
- `yonetici_matris_getir`: Yönetici matrisinin başarılı şekilde getirilmesi.

## 2. Edge Case
- `periyodik_gorev_ata`: Boş atama listesi gönderimi.
- `personel_gorev_getir`: Olmayan personel ID ile sorgu.
- Mükerrer atama yapılması durumunda fail-silent çalışması.

## 3. Negatif
- Eksik anahtarlı dictionary ile atama yapılmak istendiğinde KeyError/Exception fırlatması.
- `gorev_tamamla` metodunda olmayan havuz ID ile güncelleme yapılmaya çalışılması (hata vermese de etkilenen satır sayısını kontrol etmeyebilir, ancak Exception atıp atmadığı kontrol edilmeli).

## 4. DB/Symmetric Twin
- Testler SQLite in-memory veya test veritabanı ile çalıştırılacak.
