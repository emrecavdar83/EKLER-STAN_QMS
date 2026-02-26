
import os
import sys
import logging
from sqlalchemy import text
import time

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sync_manager import SyncManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QueueTest")

def test_queue_system():
    logger.info("=== Symmetric Twin: Kuyruk Sistemi Testi Balyor ===")
    
    with SyncManager() as manager:
        # Test verisi
        test_data = {"ad": "KUYRUK_TEST_LOKASYON", "aktif": 1}
        tablo = "lokasyonlar"
        
        # 1. ADIM: nternet yokken (veya manuel olarak) kuyrua ekle
        logger.info("1. ADIM: Veri kuyrua ekleniyor (Simulation)...")
        manager.kuyruga_ekle(tablo, "INSERT", test_data)
        
        # 2. ADIM: Kuyrukta olduunu dorula
        with manager.local_engine.connect() as conn:
            res = conn.execute(text("SELECT * FROM sync_queue WHERE tablo_adi = :t AND durum = 'bekliyor'"), {"t": tablo}).fetchone()
            if res:
                logger.info(f"DORULAMA: Veri kuyrukta 'bekliyor' durumunda (ID: {res[0]})")
            else:
                logger.error("HATA: Veri kuyrua dmedi!")
                return

        # 3. ADIM: Kuyruu ile (Balantnn olduunu varsayyoruz)
        logger.info("2. ADIM: Kuyruk ileniyor...")
        if manager.baglanti_var_mi():
            manager.kuyrugu_isle()
            
            # 4. ADIM: Durumun 'tamamlandi' olduunu dorula
            with manager.local_engine.connect() as conn:
                res = conn.execute(text("SELECT durum FROM sync_queue WHERE tablo_adi = :t ORDER BY id DESC LIMIT 1"), {"t": tablo}).scalar()
                if res == 'tamamlandi':
                    logger.info("DORULAMA: Kuyruk esi 'tamamlandi' olarak iaretlendi.")
                else:
                    logger.error(f"HATA: Kuyruk esi ilenemedi! Durum: {res}")
        else:
            logger.warning("Bulut balants yok, kuyruk ileme adm atland. Ltfen interneti kontrol edip tekrar deneyin.")

if __name__ == "__main__":
    test_queue_system()
