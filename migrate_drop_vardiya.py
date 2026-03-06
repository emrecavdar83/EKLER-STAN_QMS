import sys
import os
import toml
from sqlalchemy import create_engine, text

def migrate_drop_vardiya():
    print("--- VARDİYA SÜTUNUNU KALDIRMA MİGRASYONU ---")

    # 1. Cloud Database (PostgreSQL)
    st_secrets = {}
    try:
        with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
            st_secrets = toml.load(f)
        
        db_url = st_secrets.get("database", {}).get("DB_URL")
        if db_url:
            print("\nCloud Veritabanı (PostgreSQL) İşleniyor...")
            engine_cloud = create_engine(db_url)
            with engine_cloud.begin() as conn:
                # PostgreSQL makes dropping columns very easy
                try:
                    conn.execute(text("ALTER TABLE personel DROP COLUMN IF EXISTS vardiya"))
                    print("✅ Cloud: 'vardiya' sütunu başarıyla silindi.")
                except Exception as e:
                    print(f"⚠️ Cloud Hata (Önemsiz olabilir): {e}")
        else:
            print("\nCloud Veritabanı URL'si bulunamadı, atlanıyor.")
    except Exception as e:
        print(f"\nCloud bağlantı hatası: {e}")


    # 2. Local Database (SQLite)
    print("\nLokal Veritabanı (SQLite) İşleniyor...")
    engine_local = create_engine('sqlite:///ekleristan_local.db')
    
    with engine_local.begin() as conn:
        try:
            # SQLite newer versions support DROP COLUMN
            conn.execute(text("ALTER TABLE personel DROP COLUMN vardiya"))
            print("✅ Lokal: 'vardiya' sütunu DROP COLUMN ile başarıyla silindi.")
        except Exception as e:
            if 'no such column' in str(e).lower():
                print("✅ Lokal: 'vardiya' sütunu zaten yok.")
            else:
                print(f"⚠️ Lokal: DROP COLUMN desteklenmiyor olabilir veya hata: {e}")
                print("Lokalde 'CREATE TABLE AS' yöntemiyle güvenli kopyalama deneniyor...")
                # Güvenli SQLite sütun silme yöntemi (13. Adam - Veri Bütünlüğü)
                conn.execute(text("""
                    CREATE TABLE personel_temp AS 
                    SELECT id, ad_soyad, sifre, role_assigned, kullanici_adi, rol, bolum, departman_id, yonetici_id, gorev, gorusme, ozel_notlar, durum, tc_kimlik, dogum_tarihi, dogum_yeri, cinsiyet, sgk_no, is_kur_kaydi_var_mi, bes_kesinti_durumu, ozel_saglik_sigortasi_durumu, vergi_dilimi, asgari_gecim_indirimi_durumu, kan_grubu, egitim_durumu, mezun_olunan_okul, bolum_ad, medeni_hal, cocuk_sayisi, es_calisma_durumu, engellilik_durumu, engel_orani, acil_durum_kisi, acil_durum_tel, adres, il, ilce, cep_tel, ev_tel, mail, e_devlet_sifresi, banka_adi, iban, ise_giris_tarihi, is_cikis_tarihi, ayrilma_sebebi, ihbar_tazminati, kidem_tazminati, arabulucu, maas_tipi, net_maas, brut_maas, gunluk_brut, calisma_saati, fazla_mesai_ucreti, prim_sistemi, yol_ucreti_durumu, yemek_durumu, avans_durumu, icra_kesintisi, diger_kesintiler, ihtar_sayisi, savumnalar, terfi_durumu, performans_puani, zimmetler, yillik_izin_hakedisi, kullanilan_yillik_izin, kalan_yillik_izin, rapor_gun_sayisi, ucretsiz_izin_gun_sayisi, ayakkabi_numarasi, kiyafet_bedeni, is_basvurusu_formu, saglik_raporu, is_guvenligi_egitimi, sabika_kaydi, nufus_cuzdani_fotokopisi, ikametgah, diploma_fotokopisi, kan_grubu_karti, adli_sicil_kaydi, vesikalik_fotograf, pozisyon_seviye, servis_duragi, telefon_no
                    FROM personel
                """))
                conn.execute(text("DROP TABLE personel"))
                conn.execute(text("ALTER TABLE personel_temp RENAME TO personel"))
                print("✅ Lokal: Tablo yeniden oluşturularak sütun başarıyla silindi.")

    print("\n--- MİGRASYON TAMAMLANDI ---")

if __name__ == "__main__":
    migrate_drop_vardiya()
