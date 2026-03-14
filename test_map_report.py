import os
import traceback
from database.connection import get_engine
from ui.map_uretim import map_db, map_rapor_pdf

def test_rapor():
    engine = get_engine()
    
    try:
        # Son vardiyayı bul
        with engine.connect() as conn:
            son_vardiya = map_db.get_son_kapatilan_vardiya(engine)
            if not son_vardiya:
                print("Veritabanında kapatılmış vardiya bulunamadı, aktif vardiyalara bakılıyor...")
                df_aktif = map_db.get_tum_aktif_vardiyalar(engine)
                if not df_aktif.empty:
                    son_vardiya = df_aktif.iloc[-1].to_dict()
                    
            if not son_vardiya:
                print("Hiç vardiya yok, test edilemedi.")
                return

        v_id = int(son_vardiya['id'])
        print(f"Test edilen Vardiya ID: {v_id} (Makine: {son_vardiya.get('makina_no')})")
        
        related = map_db.get_related_vardiya_ids(engine, v_id)
        print(f"Birlikte Raporlanacak Vardiyalar (13. Adam - Çoklu Makine): {related}")
        
        html = map_rapor_pdf.uret_is_raporu_html(engine, v_id)
        
        if html:
            print("✅ HTML Raporu başarıyla üretildi! Uzunluk:", len(html))
            with open("tmp_test_map_rapor.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Dosya 'tmp_test_map_rapor.html' olarak kaydedildi.")
        else:
            print("❌ HTML Raporu boş döndü.")
    except Exception as e:
        print("CRASH DETECTED!")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_rapor()
