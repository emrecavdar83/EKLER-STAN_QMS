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

class GMPQuestion(Base):
    __tablename__ = 'gmp_questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String)
    question_text = Column(String)
    criticality = Column(String, default='NORMAL')

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
    
    menu = st.sidebar.radio("Menü", ["🏠 Ana Sayfa", "📦 Ürün Yönetimi", "📋 Soru & Limitler (Ayarlar)", "👥 Personel", "🧹 Temizlik Planı", "⚠️ GMP Soruları"])

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

    elif menu == "⚠️ GMP Soruları":
        st.header("⚠️ GMP Denetim Formu Oluştur")
        with st.form("gmp_add"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Kategori", ["PERSONEL HIJYENI", "ALTYAPI", "CAM KIRIGI", "ENVANTER"])
            q_text = c2.text_input("Soru (Örn: Bone takılı mı?)")
            crit = st.selectbox("Önem Derecesi", ["NORMAL", "KRITIK"])
            
            if st.form_submit_button("Soru Ekle"):
                session.add(GMPQuestion(category=cat, question_text=q_text, criticality=crit))
                session.commit()
                st.success("Soru havuza eklendi.")
        
        qs = session.query(GMPQuestion).all()
        if qs:
            st.dataframe(pd.DataFrame([{"Kategori": q.category, "Soru": q.question_text, "Önem": q.criticality} for q in qs]))

if __name__ == "__main__":
    main()