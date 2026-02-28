import streamlit as st
import pandas as pd
from sqlalchemy import text
from soguk_oda_utils import (
    qr_uret, qr_toplu_yazdir, init_sosts_tables
)
from database.connection import get_engine
from sqlalchemy.exc import IntegrityError
import time

engine = get_engine()

def _soguk_oda_oda_listesi():
    """Mevcut odaları tablo olarak gösterir."""
    from logic.data_fetcher import cached_veri_getir
    odalar = cached_veri_getir("soguk_odalar")
    
    if not odalar.empty:
        st.dataframe(odalar.drop(columns=['qr_token']), use_container_width=True)
    else:
        st.info("Kayıtlı oda bulunamadı.")

def _soguk_oda_oda_ekle():
    """Yeni oda ekleme formu."""
    with st.expander("🆕 Yeni Oda Ekle"):
        with st.form("admin_oda_ekle"):
            c1, c2 = st.columns(2)
            k = c1.text_input("Kod:")
            a = c2.text_input("Ad:")
            mn = c1.number_input("Min Sıcaklık:", value=0.0)
            mx = c2.number_input("Max Sıcaklık:", value=4.0)
            siklik = c1.number_input("Ölçüm Sıklığı (Saat):", value=2, min_value=1)
            if st.form_submit_button("Ekle"):
                if k and a:
                    try:
                        import uuid
                        token = str(uuid.uuid4())
                        with engine.begin() as conn:
                            conn.execute(text("""
                                INSERT INTO soguk_odalar (oda_kodu, oda_adi, min_sicaklik, max_sicaklik, olcum_sikligi, qr_token) 
                                VALUES (:k, :a, :mn, :mx, :s, :t)
                            """), {"k": k, "a": a, "mn": mn, "mx": mx, "s": siklik, "t": token})
                        st.success("Oda eklendi.")
                        st.cache_data.clear() # Cache'i temizle
                        st.rerun()
                    except IntegrityError:
                        st.error(f"❌ HATA: '{k}' koduyla zaten bir oda kayıtlı veya zorunlu veri eksiği var.")
                    except Exception as e:
                        st.error(f"❌ Bir hata oluştu: {str(e)}")

def _soguk_oda_oda_duzenle():
    """Mevcut oda düzenleme ve silme."""
    with st.expander("📝 Mevcut Odaları Düzenle"):
        from logic.data_fetcher import cached_veri_getir
        odalar_df = cached_veri_getir("soguk_odalar")
        
        odalar_list = []
        if not odalar_df.empty:
            # Sadece aktif odaları filtrele
            active_df = odalar_df[odalar_df['aktif'].astype(str).str.contains('1|True|true', regex=True)]
            odalar_list = active_df.to_dict('records')

        if len(odalar_list) > 0:
            def format_room(room):
                return f"{room.get('oda_adi', 'Bilinmeyen')} ({room.get('oda_kodu', 'ERR')})"
            
            duzenle_oda = st.selectbox("Düzenlenecek Oda:", odalar_list, format_func=format_room)
            if duzenle_oda:
                with st.form(f"edit_form_{duzenle_oda.get('id')}"):
                    c1, c2 = st.columns(2)
                    new_adi = c1.text_input("Oda Adı:", value=str(duzenle_oda.get('oda_adi', "")))
                    new_kodu = c2.text_input("Oda Kodu:", value=str(duzenle_oda.get('oda_kodu', "")))
                    new_min = c1.number_input("Min Sıcaklık:", value=float(duzenle_oda.get('min_sicaklik', 0.0)))
                    new_max = c2.number_input("Max Sıcaklık:", value=float(duzenle_oda.get('max_sicaklik', 4.0)))
                    new_takip = c1.number_input("Sapma Takip Süresi (Dk):", value=int(duzenle_oda.get('sapma_takip_dakika', 30)), min_value=5)
                    new_siklik = c2.number_input("Ölçüm Sıklığı (Saat):", value=int(duzenle_oda.get('olcum_sikligi', 2)), min_value=1)

                    if st.form_submit_button("Değişiklikleri Kaydet"):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("""
                                    UPDATE soguk_odalar
                                    SET oda_adi=:a, oda_kodu=:k, min_sicaklik=:mn, max_sicaklik=:mx, sapma_takip_dakika=:t, olcum_sikligi=:s
                                    WHERE id=:id
                                """), {"a": new_adi, "k": new_kodu, "mn": new_min, "mx": new_max, "t": new_takip, "s": new_siklik, "id": duzenle_oda.get('id')})
                            st.success("Oda ayarları güncellendi.")
                            st.cache_data.clear() # Cache'i temizle
                            time.sleep(1)
                            st.rerun()
                        except IntegrityError:
                            st.error(f"❌ HATA: '{new_kodu}' kodu başka bir oda tarafından kullanılıyor.")
                        except Exception as e:
                            st.error(f"❌ Güncelleme sırasında hata: {str(e)}")
        else:
            st.info("Kayıtlı aktif oda bulunamadı.")

def _soguk_oda_qr_indir():
    """Toplu QR ZIP indirme butonu."""
    st.divider()
    from logic.data_fetcher import cached_veri_getir
    odalar_df = cached_veri_getir("soguk_odalar")
    
    if not odalar_df.empty:
        odalar = odalar_df[odalar_df['aktif'].astype(str).str.contains('1|True|true', regex=True)]
        # Defansif ID ve İsim Çekme
        def get_room_name(rid):
            try:
                match = odalar[odalar['id'] == rid]
                if not match.empty:
                    return f"{match['oda_adi'].iloc[0]} ({match['oda_kodu'].iloc[0]})"
            except Exception:
                pass
            return f"Bilinmeyen Oda (ID: {rid})"

        sel_rooms = st.multiselect("QR Basılacaklar:", odalar['id'].tolist(), format_func=get_room_name)
        if sel_rooms and st.button("📦 QR ZIP İNDİR"):
            st.download_button("İndir", data=qr_toplu_yazdir(engine, sel_rooms), file_name="qr.zip")

def render_soguk_oda_ayarlari():
    """Ana orkestratör."""
    user_role = str(st.session_state.get("user_rol", "Personel")).upper()
    if user_role not in ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]:
        st.warning("Bu bölüme sadece yöneticiler erişebilir.")
        return

    st.subheader("❄️ Soğuk Oda Yönetimi")
    _soguk_oda_oda_listesi()
    _soguk_oda_oda_ekle()
    _soguk_oda_oda_duzenle()
    _soguk_oda_qr_indir()
