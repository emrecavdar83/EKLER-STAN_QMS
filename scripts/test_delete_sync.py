
import os
import sys
from sqlalchemy import text
import logging

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sync_manager import SyncManager

# Logger ayarı
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DeleteTest")

def test_delete_sync():
    logger.info("=== Symmetric Twin: DELETE Senkronizasyonu Testi Başlıyor ===")
    
    with SyncManager() as manager:
        # 1. Hazırlık: Test kaydı oluştur (Lokasyonlar tablosunu kullanalım)
        table = "lokasyonlar"
        test_key = "TEST_SYNC_LOC_999"
        
        logger.info(f"1. ADIM: Yerel veritabanında test kaydı oluşturuluyor: {test_key}")
        with manager.local_engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {table} WHERE ad = :k"), {"k": test_key}) # Varsa temizle
            conn.execute(text(f"INSERT INTO {table} (ad, aktif) VALUES (:k, 1)"), {"k": test_key})
        
        # 2. Kaydı Buluta Gönder (Normal Sync)
        logger.info("2. ADIM: Kayıt buluta gönderiliyor...")
        manager.sync_table(table)
        
        # 3. Bulutta oluştuğunu doğrula
        with manager.live_engine.connect() as conn:
            res = conn.execute(text(f"SELECT * FROM {table} WHERE ad = :k"), {"k": test_key}).fetchone()
            if res:
                logger.info("DOĞRULAMA: Kayıt bulutta başarıyla oluşturuldu.")
            else:
                logger.error("HATA: Kayıt buluta aktarılamadı!")
                return

        # 4. Kaydı Yerelden Sil (DELETE Senkronizasyonu Testi için)
        logger.info(f"3. ADIM: Kayıt YEREL veritabanından siliniyor: {test_key}")
        with manager.local_engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {table} WHERE ad = :k"), {"k": test_key})

        # 5. DRY RUN: Silme işlemini test et
        logger.info("4. ADIM: DRY RUN (Simülasyon) modunda SİLME testi...")
        manager.sync_table(table, dry_run=True)
        logger.info("İPUCU: Yukarıdaki loglarda 'DRY RUN: Would delete...' ifadesini görmelisiniz.")

        # 6. GERÇEK SİLME: Bulutu güncelle
        logger.info("5. ADIM: GERÇEK modda SİLME işlemi başlatılıyor...")
        manager.sync_table(table, dry_run=False)

        # 7. Final Doğrulama
        with manager.live_engine.connect() as conn:
            res = conn.execute(text(f"SELECT * FROM {table} WHERE ad = :k"), {"k": test_key}).fetchone()
            if not res:
                logger.info("FİNAL DOĞRULAMA BAŞARILI: Kayıt buluttan da silindi!")
            else:
                logger.error("HATA: Kayıt hala bulutta duruyor, silme başarısız!")

if __name__ == "__main__":
    test_delete_sync()
