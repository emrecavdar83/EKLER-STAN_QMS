import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# --- VERİTABANI VE MODELLER (TEK DOSYADA ÇALIŞMASI İÇİN BURAYA ALDIM) ---
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import declarative_base

DB_URL = 'sqlite:///ekleristan_local.db'
engine = create_engine(DB_URL, connect_args={'check_same_thread': False})
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Tablo Tanımları (Veritabanındakiyle Birebir Aynı)
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String)
    department = Column(String)
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    shelf_life_days = Column(Integer, default=3)

class ControlParameter(Base):
    __tablename__ = 'control_parameters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    name = Column(String)
    control_type = Column(String) # 'SAYI', 'SECIM', 'EVET_HAYIR', 'FOTO'
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    is_ccp = Column(Boolean, default=False)

class CleaningSchedule(Base):
    __tablename__ = 'cleaning_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String)
    item_name = Column(String)
    frequency_text = Column(String)
    last_cleaned_at = Column(DateTime, nullable=True)

class ProductionBatch(Base):
    __tablename__ = 'production_batches'
    lot_code = Column(String, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    start_time = Column(DateTime, default=datetime.now)
    status = Column(String, default='URETIMDE')
    target_quantity = Column(Integer, default=0)
    actual_quantity = Column(Integer, default=0)
    waste_quantity = Column(Integer, default=0)
    waste_reason = Column(String, nullable=True)

class QualityRecord(Base):
    __tablename__ = 'quality_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_code = Column(String, ForeignKey('production_batches.lot_code'))
    parameter_id = Column(Integer, ForeignKey('control_parameters.id'))
    measured_value = Column(String)
    result = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.now)

class GMPLocation(Base):
    __tablename__ = 'gmp_lokasyonlar'
    id = Column(Integer, primary_key=True, autoincrement=True)
    lokasyon_adi = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('gmp_lokasyonlar.id'))

class GMPQuestion(Base):
    __tablename__ = 'gmp_soru_havuzu'
    id = Column(Integer, primary_key=True, autoincrement=True)
    kategori = Column(String, nullable=False)
    soru_metni = Column(String, nullable=False)
    risk_puani = Column(Integer, default=1)
    brc_ref = Column(String)
    frekans = Column(String, default='GÜNLÜK')
    aktif = Column(Boolean, default=True)

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="Ekleristan Yönetim Paneli", layout="wide")

st.markdown("""
<style>
/* 1. Header Branding Temizliği */
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0) !important;
}

.stAppDeployButton,
.stActionButton,
footer {
    display: none !important;
    visibility: hidden !important;
}

/* 2. Menü Butonunu (Hamburger) Her Koşulda Göster */
button[data-testid="stSidebarCollapseButton"], 
button[aria-label="Open sidebar"], 
button[aria-label="Close sidebar"] {
    visibility: visible !important;
    display: flex !important;
    background-color: #007bff !important; /* Yönetim için Mavi */
    color: white !important;
    border-radius: 8px !important;
    z-index: 9999999 !important;
    opacity: 1 !important;
}

/* Mobil için Konum Sabitleme */
@media screen and (max-width: 768px) {
    button[data-testid="stSidebarCollapseButton"],
    button[aria-label="Open sidebar"] {
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        scale: 1.1;
    }
}

#MainMenu {
    visibility: visible !important;
    display: block !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("🏭 EKLERİSTAN QMS")
    st.sidebar.info("Yönetici Paneli (v1.0)")
    
    menu = st.sidebar.radio("Menü", [
        "🏠 Ana Sayfa", 
        "📦 Ürün Yönetimi", 
        "📋 Soru & Limitler (Ayarlar)", 
        "👥 Personel", 
        "🧹 Temizlik Planı", 
        "🛡️ GMP DENETİMİ (Sorular)",
        "📍 GMP Lokasyonları"
    ])

    if menu == "🏠 Ana Sayfa":
        st.title("Yönetici Kokpiti")
        st.write("Sisteme hoş geldiniz. Sol menüden tanımlamaları yapabilirsiniz.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            try:
                prod_count = session.query(Product).count()
                st.metric("Toplam Ürün", prod_count)
            except: st.error("Veritabanı bağlanamadı.")
        with c2:
            user_count = session.query(User).count()
            st.metric("Kayıtlı Personel", user_count)
        with c3:
            batch_count = session.query(ProductionBatch).count()
            st.metric("Aktif Üretim", batch_count)

    elif menu == "📦 Ürün Yönetimi":
        st.header("📦 Ürün Tanımlama")
        
        with st.form("new_product"):
            c1, c2 = st.columns(2)
            u_ad = c1.text_input("Ürün Adı (Örn: Ekler)")
            u_raf = c2.number_input("Raf Ömrü (Gün)", value=3)
            if st.form_submit_button("Ürünü Kaydet"):
                try:
                    session.add(Product(name=u_ad, shelf_life_days=u_raf))
                    session.commit()
                    st.success(f"{u_ad} başarıyla eklendi!")
                except:
                    session.rollback()
                    st.error("Bu ürün zaten var!")

        st.subheader("Mevcut Ürünler")
        products = session.query(Product).all()
        if products:
            data = [{"ID": p.id, "Ürün": p.name, "Raf Ömrü": p.shelf_life_days} for p in products]
            st.table(data)

    elif menu == "📋 Soru & Limitler (Ayarlar)":
        st.header("📋 Kontrol Parametreleri (Limitler)")
        st.info("Burada ürünler için kontrol soruları ve KIRMIZI EKRAN limitlerini belirlersiniz.")
        
        products = session.query(Product).all()
        if not products:
            st.warning("Önce 'Ürün Yönetimi'nden ürün ekleyin.")
        else:
            prod_names = {p.id: p.name for p in products}
            sel_prod_name = st.selectbox("Hangi Ürün İçin?", ["Genel (Tüm Ürünler)"] + list(prod_names.values()))
            
            sel_prod_id = None
            for pid, pname in prod_names.items():
                if pname == sel_prod_name:
                    sel_prod_id = pid
            
            with st.form("new_param"):
                p_ad = st.text_input("Soru / Parametre Adı (Örn: Pişirme Sıcaklığı)")
                c1, c2 = st.columns(2)
                p_tip = c1.selectbox("Veri Tipi", ["SAYI", "EVET_HAYIR", "FOTO", "SECIM"])
                is_ccp = c2.checkbox("Bu bir CCP (Kritik Kontrol) mü?", help="İşaretlenirse hata durumunda üretim kilitlenir.")
                
                c3, c4 = st.columns(2)
                min_v = c3.number_input("Min Değer (Opsiyonel)", value=0.0)
                max_v = c4.number_input("Max Değer (Opsiyonel)", value=0.0)
                
                if st.form_submit_button("Parametreyi Ekle"):
                    session.add(ControlParameter(
                        product_id=sel_prod_id,
                        name=p_ad,
                        control_type=p_tip,
                        min_value=min_v if p_tip=="SAYI" else None,
                        max_value=max_v if p_tip=="SAYI" else None,
                        is_ccp=is_ccp
                    ))
                    session.commit()
                    st.success("Parametre eklendi.")

            # Listeleme
            st.divider()
            if sel_prod_id:
                st.write(f"**{sel_prod_name} İçin Tanımlı Kontroller:**")
                params = session.query(ControlParameter).filter_by(product_id=sel_prod_id).all()
            else:
                st.write("**Genel Kontroller:**")
                params = session.query(ControlParameter).filter(ControlParameter.product_id == None).all()

            if params:
                df = pd.DataFrame([{
                    "Soru": p.name, 
                    "Tip": p.control_type, 
                    "Min": p.min_value, 
                    "Max": p.max_value,
                    "Kritik (CCP)": "EVET" if p.is_ccp else "HAYIR"
                } for p in params])
                st.table(df)

    elif menu == "👥 Personel":
        st.header("👥 Personel Listesi")
        with st.form("add_user"):
            c1, c2 = st.columns(2)
            u_user = c1.text_input("Kullanıcı Adı (Giriş İçin)")
            u_pass = c2.text_input("Şifre", type="password")
            c3, c4 = st.columns(2)
            u_full = c3.text_input("Ad Soyad")
            u_role = c4.selectbox("Rol", ["OPERATOR", "YONETICI", "KALITE"])
            
            if st.form_submit_button("Personel Ekle"):
                try:
                    session.add(User(username=u_user, password=u_pass, full_name=u_full, role=u_role))
                    session.commit()
                    st.success("Personel eklendi.")
                except:
                    session.rollback()
                    st.error("Kullanıcı adı kullanımda.")
        
        users = session.query(User).all()
        st.dataframe(pd.DataFrame([{"Ad Soyad": u.full_name, "Kullanıcı Adı": u.username, "Rol": u.role} for u in users]))

    elif menu == "🧹 Temizlik Planı":
        st.header("🧹 Temizlik Zamanlayıcısı")
        with st.form("clean_plan"):
            c1, c2 = st.columns(2)
            dept = c1.text_input("Bölüm (Örn: Bomba Hattı)")
            item = c2.text_input("Temizlenecek Yer (Örn: Tezgah Altı)")
            freq = st.selectbox("Sıklık / Zaman", ["Her gün 18:00", "Her gün 08:00", "Haftalık", "Ayda 1"])
            
            if st.form_submit_button("Görevi Ekle"):
                session.add(CleaningSchedule(department=dept, item_name=item, frequency_text=freq))
                session.commit()
                st.success("Temizlik görevi eklendi.")
        
        plans = session.query(CleaningSchedule).all()
        if plans:
            st.table(pd.DataFrame([{"Bölüm": p.department, "Yer": p.item_name, "Zaman": p.frequency_text} for p in plans]))

    elif menu == "🛡️ GMP DENETİMİ (Sorular)":
        st.header("🛡️ GMP DENETİMİ (Soru Bankası)")
        
        tab_list, tab_manual, tab_import = st.tabs(["📋 Soru Listesi", "➕ Tekil Soru Ekle", "📤 Excel/CSV İçe Aktar"])
        
        with tab_manual:
            st.subheader("Yeni GMP Sorusu Ekle")
            with st.form("single_gmp_q_form"):
                q_kat = st.selectbox("Kategori", ["Hijyen", "Gıda Savunma", "Operasyon", "Gıda Sahteciliği", "Bina/Altyapı", "Genel"])
                q_txt = st.text_area("Soru Metni")
                col_r, col_f, col_b = st.columns(3)
                q_risk = col_r.selectbox("Risk Puanı", [1, 2, 3], help="3: Kritik bulgu, fotoğraf zorunludur.")
                q_freq = col_f.selectbox("Frekans", ["GÜNLÜK", "HAFTALIK", "AYLIK"])
                q_brc = col_b.text_input("BRC Referans No", placeholder="Örn: 4.10.1")
                
                if st.form_submit_button("Sorumu Kaydet"):
                    if q_txt:
                        new_q = GMPQuestion(
                            kategori=q_kat,
                            soru_metni=q_txt,
                            risk_puani=q_risk,
                            brc_ref=q_brc,
                            frekans=q_freq
                        )
                        session.add(new_q)
                        session.commit()
                        st.success("✅ Soru başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.error("Lütfen soru metnini boş bırakmayın.")

        with tab_import:
            st.subheader("Excel'den Toplu Soru Yükleme")
            st.info("""
                **Dosya Formatı Şöyle Olmalı:**
                - `KATEGORİ`: (Örn: Gıda Savunma, Operasyon)
                - `SORU METNİ`: (Örn: Un eleği sağlam mı?)
                - `RİSK PUANI`: (1, 2 veya 3)
                - `BRC REF`: (Örn: 4.10.1)
                - `FREKANS`: (GÜNLÜK, HAFTALIK, AYLIK)
            """)
            
            uploaded_file = st.file_uploader("Soru Listesini Seçin", type=['xlsx', 'csv'])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)
                    
                    st.write("Önizleme:", df.head())
                    
                    if st.button("Veritabanına İşle"):
                        count = 0
                        for _, row in df.iterrows():
                            # Sütun isimlerini normalize et (küçük/büyük harf duyarlılığı için)
                            row_dict = {str(k).upper().strip(): v for k, v in row.to_dict().items()}
                            
                            new_q = GMPQuestion(
                                kategori=row_dict.get('KATEGORİ', row_dict.get('KATEGORI', 'Genel')),
                                soru_metni=row_dict.get('SORU METNİ', row_dict.get('SORU_METNI', '')),
                                risk_puani=int(row_dict.get('RİSK PUANI', row_dict.get('RISK_PUANI', 1))),
                                brc_ref=str(row_dict.get('BRC REF', row_dict.get('BRC_REF', ''))),
                                frekans=str(row_dict.get('FREKANS', 'GÜNLÜK')).upper()
                            )
                            session.add(new_q)
                            count += 1
                        session.commit()
                        st.success(f"✅ {count} adet soru başarıyla yüklendi!")
                except Exception as e:
                    st.error(f"Hata oluştu: {e}")

        with tab_list:
            st.subheader("Mevcut Soru Bankası")
            questions = session.query(GMPQuestion).all()
            if questions:
                q_data = [{
                    "ID": q.id,
                    "Kategori": q.kategori,
                    "Soru": q.soru_metni,
                    "Risk": q.risk_puani,
                    "BRC": q.brc_ref,
                    "Frekans": q.frekans
                } for q in questions]
                st.dataframe(pd.DataFrame(q_data), use_container_width=True)
                
                if st.button("Tüm Soruları Temizle"):
                    session.query(GMPQuestion).delete()
                    session.commit()
                    st.warning("Tüm sorular silindi.")
                    st.rerun()

    elif menu == "📍 GMP Lokasyonları":
        st.header("📍 Denetim Lokasyonları (Fabrika Hiyerarşisi)")
        
        with st.form("new_location"):
            col1, col2 = st.columns(2)
            loc_name = col1.text_input("Lokasyon/Bölüm Adı", placeholder="Örn: 3. KAT KEK")
            
            # Üst lokasyon seçimi
            parents = session.query(GMPLocation).all()
            parent_options = {p.id: p.lokasyon_adi for p in parents}
            parent_options[0] = "--- Ana Bölüm ---"
            
            sel_parent_id = col2.selectbox("Üst Bölüm", options=sorted(parent_options.keys()), 
                                           format_func=lambda x: parent_options[x])
            
            if st.form_submit_button("Lokasyonu Ekle"):
                new_loc = GMPLocation(
                    lokasyon_adi=loc_name,
                    parent_id=None if sel_parent_id == 0 else sel_parent_id
                )
                session.add(new_loc)
                session.commit()
                st.success(f"✅ {loc_name} eklendi.")
                st.rerun()

        st.divider()
        st.subheader("Bölüm Ağacı")
        locations = session.query(GMPLocation).all()
        if locations:
            l_data = []
            for l in locations:
                p_name = parent_options.get(l.parent_id, "-") if l.parent_id else "ANA BÖLÜM"
                l_data.append({"ID": l.id, "Bölüm": l.lokasyon_adi, "Bağlı Olduğu": p_name})
            st.table(l_data)

if __name__ == "__main__":
    main()