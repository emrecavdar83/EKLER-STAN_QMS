# EKLERISTAN QMS - SOSTS Modülü - Yardımcı Fonksiyonlar

import sqlite3
import qrcode
import uuid
import io
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

DB_PATH = 'ekleristan_local.db'

# -----------------------------------------------------------------------------
# 1. QR YÖNETİMİ
# -----------------------------------------------------------------------------

def qr_uret(oda_id):
    """
    Belirli bir oda için UUID token tabanlı QR üretir. 
    Token yoksa üretir ve DB'ye kaydeder.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Oda bilgisini çek
        cursor.execute("SELECT * FROM soguk_odalar WHERE id = ?", (oda_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        token = row['qr_token']
        # Eğer token yoksa üret ve DB'ye işle
        if not token:
            token = str(uuid.uuid4())
            cursor.execute("UPDATE soguk_odalar SET qr_token = ?, qr_uretim_tarihi = ? WHERE id = ?", 
                           (token, datetime.now(), oda_id))
            conn.commit()
            
        # QR Kod İçeriği (Standart URL Yapısı - Anayasa Madde 10)
        # Yerel ağ üzerinden erişim için IP tabanlı URL kullanıyoruz.
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "localhost"
            
        base_url = f"http://{local_ip}:8501"
        qr_content = f"{base_url}/?scanned_qr={token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        width, height = qr_img.size
        
        # 1. Font ve Metin ölçümü için geçici canvas
        dummy_img = Image.new('RGB', (1, 1), 'white')
        draw = ImageDraw.Draw(dummy_img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            
        text = f"{row['oda_adi']} ({row['oda_kodu']})"
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = right - left, bottom - top

        # 2. Dinamik Genişlik ve Yükseklik Hesaplama
        padding_x = 40
        final_width = max(width, text_w + padding_x)
        final_height = height + 80 # Alt bant yüksekliği

        # 3. Nihai Canvas Oluşturma
        new_img = Image.new('RGB', (final_width, final_height), 'white')
        
        # 4. QR Kodu Ortalayarak Yapıştır
        qr_x = (final_width - width) // 2
        new_img.paste(qr_img, (qr_x, 0))
        
        # 5. Metni Ortalayarak Yaz
        draw = ImageDraw.Draw(new_img)
        text_x = (final_width - text_w) // 2
        draw.text((text_x, height + 15), text, fill="black", font=font)
        
        # BytesIO olarak döndür
        img_byte_arr = io.BytesIO()
        new_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

def qr_toplu_yazdir(oda_id_listesi):
    """Seçilen odaların QR kodlarını bir ZIP arşivinde toplar."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for oda_id in oda_id_listesi:
            img_data = qr_uret(oda_id)
            if img_data:
                # Oda adını dosya ismi yap
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT oda_kodu FROM soguk_odalar WHERE id = ?", (oda_id,))
                    code = cursor.fetchone()[0]
                    zip_file.writestr(f"QR_{code}.png", img_data.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# -----------------------------------------------------------------------------
# 2. ZAMANLAMA VE PLANLAMA (Lazy Evaluation)
# -----------------------------------------------------------------------------

def plan_uret(gun_sayisi=7):
    """Aktif odalar için ölçüm planı (slotları) üretir."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM soguk_odalar WHERE aktif = 1")
        odalar = cursor.fetchall()
        
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for oda in odalar:
            siklik = oda['olcum_sikligi'] # Saat
            for d in range(gun_sayisi):
                current_day = start_date + timedelta(days=d)
                # Mesai saatleri: 06:00 - 22:00
                for h in range(6, 23, siklik):
                    beklenen_zaman = current_day.replace(hour=h)
                    # INSERT OR IGNORE: Aynı oda ve zaman için mükerrer planı önler (unique constraint eklenmeli)
                    # Not: soguk_oda_schema'da unique eklenmediyse burada manuel kontrol:
                    cursor.execute("SELECT id FROM olcum_plani WHERE oda_id = ? AND beklenen_zaman = ?", 
                                   (oda['id'], beklenen_zaman))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum) VALUES (?, ?, 'BEKLIYOR')",
                                       (oda['id'], beklenen_zaman))
        conn.commit()

def kontrol_geciken_olcumler():
    """Zamanı geçen ve hâlâ BEKLIYOR olan slotları GECIKTI'ye çeker."""
    with sqlite3.connect(DB_PATH) as conn:
        now = datetime.now()
        conn.execute("""
            UPDATE olcum_plani 
            SET durum = 'GECIKTI', guncelleme_zamani = ? 
            WHERE durum = 'BEKLIYOR' AND beklenen_zaman < ?
        """, (now, now))
        conn.commit()

# -----------------------------------------------------------------------------
# 3. VERİ ERİŞİM (CRUD)
# -----------------------------------------------------------------------------

def get_personnel_roles():
    # Mevcut sistemin kullanıcı rolleriyle entegrasyon için taslak
    return ["Admin", "Kalite", "Operatör"]

def kaydet_olcum(oda_id, sicaklik, kullanici, plan_id=None, qr_mi=1, takip_suresi=None):
    """
    Sıcaklık ölçümünü kaydeder, planı günceller ve sapma durumunda 
    Admin'in belirlediği süreye göre yeni takip görevi oluşturur (Madde 7: İşlem Yolu).
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Limitleri kontrol et
        cursor.execute("SELECT min_sicaklik, max_sicaklik FROM soguk_odalar WHERE id = ?", (oda_id,))
        limit = cursor.fetchone()
        
        sapma = 0
        if sicaklik < limit['min_sicaklik'] or sicaklik > limit['max_sicaklik']:
            sapma = 1
            
        # 1. Ölçümü Kaydet
        cursor.execute("""
            INSERT INTO sicaklik_olcumleri (oda_id, sicaklik_degeri, kaydeden_kullanici, sapma_var_mi, qr_ile_girildi, planlanan_zaman)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (oda_id, sicaklik, kullanici, sapma, qr_mi, datetime.now()))
        
        olcum_id = cursor.lastrowid
        
        # 2. Planı Güncelle (Eğer bir slota binaen yapılıyorsa)
        if plan_id:
            cursor.execute("""
                UPDATE olcum_plani 
                SET gerceklesen_olcum_id = ?, durum = 'TAMAMLANDI', guncelleme_zamani = ?
                WHERE id = ?
            """, (olcum_id, datetime.now(), plan_id))
        
        # 3. OTOMATİK SAPMA TAKİBİ (Dinamiklik & Hiyerarşi İlkesi)
        if sapma and takip_suresi:
            yeni_zaman = datetime.now() + timedelta(minutes=takip_suresi)
            cursor.execute("""
                INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum) 
                VALUES (?, ?, 'BEKLIYOR')
            """, (oda_id, yeni_zaman.strftime('%Y-%m-%d %H:%M:%S')))
            
        conn.commit()
        return sapma
