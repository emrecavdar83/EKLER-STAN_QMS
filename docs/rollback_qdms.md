# QDMS Modülü Geri Dönüş (Rollback) Prosedürü

Bu doküman, QDMS modülü deploy edildikten sonra beklenmedik bir hata veya sistem kararsızlığı oluşması durumunda sistemin bir önceki kararlı haline (v3.1.0) nasıl döndürüleceğini açıklar.

## 1. Kod Seviyesinde Geri Dönüş
Eğer Git kullanılıyorsa:
```bash
# Deploy tamamlandığında `git log --oneline -1` çıktısı buraya yapıştırılacak.
git revert [HASH]
git push origin [BRANCH]
```

Eğer manuel dosya değişikliği yapıldıysa:
- `app.py` dosyasındaki QDMS navigasyon bloklarını (`elif secim == "..."`) yorum satırına getirin veya silin.
- `modules/qdms/` dizini ve `pages/qdms_*.py` dosyaları kalsa bile navigasyon kapalı olduğu için sistem etkilenmeyecektir.

## 2. Bağımlılıkların Temizlenmesi
`requirements.txt` dosyasından aşağıdaki paketleri kaldırın ve ortamı yeniden kurun:
- `reportlab`
- `qrcode`

```bash
pip uninstall reportlab qrcode
```

### 3. Veritabanı Durumu (Symmetric Twin)
QDMS tabloları (`qdms_*`) `CREATE TABLE IF NOT EXISTS` ile oluşturulduğu için silinmesine gerek yoktur; veriler arşivde kalabilir. Ancak modülün navigasyondan kaldırılması için aşağıdaki komut **hem Lokal SQLite hem de Supabase PostgreSQL** tarafında çalıştırılmalıdır:
```sql
UPDATE ayarlar_moduller SET aktif = 0 WHERE modul_anahtari IN ('dokuman_merkezi', 'belge_yonetimi', 'talimatlar', 'uyumluluk');
```

## 4. Doğrulama
Rollback sonrası aşağıdaki "Smoke Test" adımlarını uygulayın:
- [ ] Uygulama hatasız başlıyor mu?
- [ ] Soğuk Oda ve Üretim Girişi sayfaları aktif mi?
- [ ] Navigasyonda QDMS öğeleri gizlendi mi?
