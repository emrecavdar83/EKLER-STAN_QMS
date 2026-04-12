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
        st.dataframe(odalar.drop(columns=['qr_token'], errors='ignore'), use_container_width=True)
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
            sorumlu = c2.text_input("Dolap Sorumlusu (Ad Soyad/Unvan):", value="", placeholder="Örn: Ali Veli (Üretim Şefi)")
            durum_tip = st.selectbox("Cihaz Durumu:", ["AKTİF", "ARIZALI", "KULLANIM DIŞI"])
            ozel_saatler = st.text_input("Özel Ölçüm Saatleri (Opsiyonel):", placeholder="Örn: 07, 15, 23 (Virgülle ayırın)")
            apply_defaults = st.checkbox("Varsayılan Dinamik Kuralları Uygula (07-15: 2s, 15-23: 3s, 23-07: 4s)", value=True)
            
            if st.form_submit_button("Ekle"):
                if k and a:
                    try:
                        import uuid
                        token = str(uuid.uuid4())
                        with engine.begin() as conn:
                            conn.execute(text("""
                                INSERT INTO soguk_odalar (oda_kodu, oda_adi, min_sicaklik, max_sicaklik, olcum_sikligi, qr_token, sorumlu_personel, ozel_olcum_saatleri, durum) 
                                VALUES (:k, :a, :mn, :mx, :s, :t, :sp, :osaat, :durum)
                            """), {"k": k, "a": a, "mn": mn, "mx": mx, "s": siklik, "t": token, "sp": sorumlu, "osaat": ozel_saatler, "durum": durum_tip})
                            
                            # Yeni eklenen oda ID'sini al
                            new_id = conn.execute(text("SELECT id FROM soguk_odalar WHERE oda_kodu = :k"), {"k": k}).scalar()
                            
                            if apply_defaults and new_id:
                                # Varsayılan Kuralları Ekle
                                defaults = [
                                    (new_id, 'Gündüz', 7, 15, 2),
                                    (new_id, 'Akşam', 15, 23, 3),
                                    (new_id, 'Gece', 23, 7, 4)
                                ]
                                for oid, ad, bas, bit, s in defaults:
                                    conn.execute(text("""
                                        INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik)
                                        VALUES (:oid, :ad, :bas, :bit, :s)
                                    """), {"oid": oid, "ad": ad, "bas": bas, "bit": bit, "s": s})
                        
                        # 13. ADAM: Planı anında oluştur
                        import soguk_oda_utils
                        soguk_oda_utils.plan_uret(engine)
                        
                        st.success("Oda eklendi ve ölçüm planı oluşturuldu.")
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
                    new_sorumlu = c1.text_input("Dolap Sorumlusu (Ad Soyad/Unvan):", value=str(duzenle_oda.get('sorumlu_personel', 'Atanmadı')))
                    
                    st_durum = str(duzenle_oda.get('durum', 'AKTİF'))
                    durum_opts = ["AKTİF", "ARIZALI", "KULLANIM DIŞI"]
                    new_durum = st.selectbox("Cihaz Durumu:", durum_opts, index=durum_opts.index(st_durum) if st_durum in durum_opts else 0)
                    
                    new_ozel_saatler = c2.text_input("Özel Ölçüm Saatleri:", value=str(duzenle_oda.get('ozel_olcum_saatleri', '') or ''), placeholder="Örn: 08, 16, 00")

                    if st.form_submit_button("Değişiklikleri Kaydet"):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("""
                                    UPDATE soguk_odalar
                                    SET oda_adi=:a, oda_kodu=:k, min_sicaklik=:mn, max_sicaklik=:mx, sapma_takip_dakika=:t, olcum_sikligi=:s, sorumlu_personel=:sp, ozel_olcum_saatleri=:osaat, durum=:durum
                                    WHERE id=:id
                                """), {"a": new_adi, "k": new_kodu, "mn": new_min, "mx": new_max, "t": new_takip, "s": new_siklik, "sp": new_sorumlu, "osaat": new_ozel_saatler, "durum": new_durum, "id": duzenle_oda.get('id')})
                            
                            # 13. ADAM: Değişiklik sonrası planı tazele
                            import soguk_oda_utils
                            soguk_oda_utils.plan_uret(engine)
                            
                            st.toast("✅ Oda ayarları güncellendi ve plan yenilendi!"); st.rerun()
                        except IntegrityError:
                            st.error(f"❌ HATA: '{new_kodu}' kodu başka bir oda tarafından kullanılıyor.")
                        except Exception as e:
                            st.error(f"❌ Güncelleme sırasında hata: {str(e)}")
                
                # --- DİNAMİK KURAL EDİTÖRÜ ---
                st.divider()
                _render_kural_editor(duzenle_oda.get('id'), duzenle_oda.get('oda_adi'))
        else:
            st.info("Kayıtlı aktif oda bulunamadı.")

def _render_kural_editor(oda_id, oda_adi):
    """Oda bazlı dinamik kural yönetim arayüzü."""
    st.write(f"⚙️ **{oda_adi}** İçin Ölçüm Kuralları")
    
    # Mevcut kuralları çek
    try:
        with engine.connect() as conn:
            kurallar = pd.read_sql(text("SELECT * FROM soguk_oda_planlama_kurallari WHERE oda_id = :oid AND aktif = 1"), conn, params={"oid": oda_id})
    except:
        kurallar = pd.DataFrame()

    if not kurallar.empty:
        for _, row in kurallar.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            c1.write(f"🏷️ {row['kural_adi']}")
            c2.write(f"🕒 {row['baslangic_saati']}:00")
            c3.write(f"🛑 {row['bitis_saati']}:00")
            c4.write(f"🔄 {row['siklik']} Sa")
            if c5.button("🗑️ Sil", key=f"del_ks_{row['id']}"):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE soguk_oda_planlama_kurallari SET aktif = 0 WHERE id = :id"), {"id": row['id']})
                import soguk_oda_utils
                soguk_oda_utils.plan_uret(engine)
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Bu oda için tanımlanmış dinamik kural bulunmuyor. Sistem varsayılan sıklığı (üstteki ayar) kullanacaktır.")

    # Yeni kural ekleme
    with st.expander("➕ Yeni Kural Ekle"):
        with st.form(f"kural_ekle_{oda_id}"):
            ca, cb, cc, cd = st.columns(4)
            n_ad = ca.text_input("Kural Adı:", value="Vardiya")
            n_bas = cb.number_input("Başlangıç (Saat):", 0, 23, 7)
            n_bit = cc.number_input("Bitiş (Saat):", 0, 23, 15)
            n_sik = cd.number_input("Sıklık (Sa):", 1, 24, 2)
            
            if st.form_submit_button("Kuralı Kaydet"):
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik)
                        VALUES (:oid, :ad, :bas, :bit, :s)
                    """), {"oid": oda_id, "ad": n_ad, "bas": n_bas, "bit": n_bit, "s": n_sik})
                import soguk_oda_utils
                soguk_oda_utils.plan_uret(engine)
                st.success("Kural eklendi.")
                st.rerun()
    
    # Hızlı Şablon
    if st.button("🚀 Varsayılan Kuralları Uygula (07-15:2s, 15-23:3s, 23-07:4s)", key=f"def_rule_{oda_id}"):
        with engine.begin() as conn:
            # Öncekileri pasif yap
            conn.execute(text("UPDATE soguk_oda_planlama_kurallari SET aktif = 0 WHERE oda_id = :oid"), {"oid": oda_id})
            # Yeni şablonu ekle
            defaults = [('Sabah', 7, 15, 2), ('Akşam', 15, 23, 3), ('Gece', 23, 7, 4)]
            for ad, bas, bit, s in defaults:
                conn.execute(text("""
                    INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik)
                    VALUES (:oid, :ad, :bas, :bit, :s)
                """), {"oid": oda_id, "ad": ad, "bas": bas, "bit": bit, "s": s})
        import soguk_oda_utils
        soguk_oda_utils.plan_uret(engine)
        st.success("Varsayılan kurallar başarıyla uygulandı.")
        st.rerun()

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
