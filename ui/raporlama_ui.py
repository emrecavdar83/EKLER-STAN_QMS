import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta, date
import io
import time, pytz, os
import plotly.express as px

from database.connection import get_engine
from logic.data_fetcher import (
    run_query, veri_getir, get_user_roles, 
    get_all_sub_department_ids, get_personnel_hierarchy
)
from logic.auth_logic import kullanici_yetkisi_var_mi
from constants import (
    VARDIYA_LISTESI, 
    get_position_name, 
    get_position_icon, 
    get_position_color
)
from soguk_oda_utils import get_matrix_data, get_trend_data

engine = get_engine()

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

# --- HELPERS ---

def _rapor_excel_export(df_display, urun_ozet, bas_tarih, bit_tarih):
    """Excel indirme butonu oluşturur."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Detaylı Kayıtlar')
            if urun_ozet is not None:
                urun_ozet.to_excel(writer, index=False, sheet_name='Ürün Özeti')
        excel_data = output.getvalue()
        st.download_button(label="📥 Excel Olarak İndir", data=excel_data, file_name=f"uretim_raporu_{bas_tarih}_{bit_tarih}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.caption(f"ℹ️ Excel indirme: openpyxl kütüphanesi gereklidir (pip install openpyxl)")

# --- MODÜL 1: ÜRETİM VE VERİMLİLİK ---
def _render_uretim_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarihler arasında üretim kaydı bulunamadı.")
        return
    df.columns = [c.lower() for c in df.columns]
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam Üretim (Adet)", f"{df['miktar'].sum():,}")
    k2.metric("Toplam Fire", f"{df['fire'].sum():,}")
    fire_oran = (df['fire'].sum() / df['miktar'].sum()) * 100 if df['miktar'].sum() > 0 else 0
    k3.metric("Ortalama Fire Oranı", f"%{fire_oran:.2f}")

    st.subheader("📦 Ürün Bazında Özet")
    urun_ozet = df.groupby('urun').agg({'miktar': 'sum', 'fire': 'sum', 'lot_no': 'count'}).reset_index()
    urun_ozet.columns = ['Ürün Adı', 'Toplam Üretim', 'Toplam Fire', 'Lot Sayısı']
    urun_ozet['Fire Oranı (%)'] = (urun_ozet['Toplam Fire'] / urun_ozet['Toplam Üretim'] * 100).round(2)
    st.dataframe(urun_ozet.sort_values('Toplam Üretim', ascending=False), use_container_width=True, hide_index=True)

    st.subheader("📋 Detaylı Kayıtlar")
    cols = ['tarih', 'saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    rename_map = {'tarih': 'Tarih', 'saat': 'Saat', 'vardiya': 'Vardiya', 'urun': 'Ürün Adı', 'lot_no': 'Lot No', 'miktar': 'Miktar', 'fire': 'Fire', 'kullanici': 'Kaydeden Kullanıcı', 'notlar': 'Notlar'}
    df_display.columns = [rename_map.get(c, c) for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    _rapor_excel_export(df_display, urun_ozet, bas_tarih, bit_tarih)

# --- MODÜL 2: KALİTE (KPI) ANALİZİ ---
def _render_kpi_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Kalite kaydı bulunamadı.")
        return
    k1, k2 = st.columns(2)
    onay_sayisi = len(df[df['karar'] == 'ONAY'])
    red_sayisi = len(df[df['karar'] == 'RED'])
    k1.success(f"✅ Onaylanan: {onay_sayisi}"); k2.error(f"❌ Reddedilen: {red_sayisi}")
    red_df = df[df['karar'] == 'RED'].groupby('urun').size().reset_index(name='Red Adeti')
    if not red_df.empty:
        st.write("🔔 **En Çok Red Alan Ürünler**")
        st.table(red_df)
    st.dataframe(df, use_container_width=True)

# --- MODÜL 3: GÜNLÜK OPERASYONEL RAPOR ---
def _render_gunluk_operasyonel_rapor(bas_tarih):
    st.info("💡 Bu rapor belirlediğiniz tarihteki işlemleri özetler.")
    t_str = str(bas_tarih)
    kpi_df = run_query(f"SELECT tarih, saat, urun, karar, notlar, vardiya FROM urun_kpi_kontrol WHERE tarih='{t_str}'")
    uretim_df = run_query(f"SELECT tarih, saat, urun, miktar, vardiya FROM depo_giris_kayitlari WHERE tarih='{t_str}'")
    hijyen_df = run_query(f"SELECT tarih, saat, personel, durum, sebep, aksiyon, vardiya, bolum FROM hijyen_kontrol_kayitlari WHERE tarih='{t_str}'")
    temizlik_df = run_query(f"SELECT tarih, saat, bolum, islem, durum FROM temizlik_kayitlari WHERE tarih='{t_str}'")
    
    # SOSTS Verisi (SQLite/Postgres Uyumlu Tarih Filtresi - Range Query)
    s_dt = datetime.combine(bas_tarih, datetime.min.time())
    e_dt = s_dt + timedelta(days=1)
    s_str = s_dt.strftime('%Y-%m-%d %H:%M:%S')
    e_str = e_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    sosts_query = f"SELECT o.oda_adi, m.sicaklik_degeri, m.sapma_var_mi, m.olcum_zamani FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id WHERE m.olcum_zamani >= '{s_str}' AND m.olcum_zamani < '{e_str}'"
    sosts_df = run_query(sosts_query)

    v_secim = st.multiselect("Vardiya Seçimi", VARDIYA_LISTESI, default=VARDIYA_LISTESI)
    depts = hijyen_df['bolum'].dropna().unique().tolist() if not hijyen_df.empty else []
    d_secim = st.multiselect("Departman Seçimi", ["Tümü"] + depts, default=["Tümü"])

    if not kpi_df.empty: kpi_df = kpi_df[kpi_df['vardiya'].isin(v_secim)] if 'vardiya' in kpi_df.columns else kpi_df
    if not uretim_df.empty: uretim_df = uretim_df[uretim_df['vardiya'].isin(v_secim)]
    if not hijyen_df.empty:
        hijyen_df = hijyen_df[hijyen_df['vardiya'].isin(v_secim)]
        if "Tümü" not in d_secim: hijyen_df = hijyen_df[hijyen_df['bolum'].isin(d_secim)]

    red_s = len(kpi_df[kpi_df['karar'] == 'RED']) if not kpi_df.empty else 0
    uyg_h = len(hijyen_df[hijyen_df['durum'] != 'Sorun Yok']) if not hijyen_df.empty else 0
    maz_s = len(hijyen_df[hijyen_df['durum'] == 'Gelmedi']) if not hijyen_df.empty else 0
    sapma_s = len(sosts_df[sosts_df['sapma_var_mi'] == 1]) if not sosts_df.empty else 0
    
    if (red_s + uyg_h + maz_s + sapma_s) > 0:
        st.error(f"🔴 DİKKAT: {red_s} RED | {maz_s} Gelmedi | {uyg_h} Hijyen | {sapma_s} Oda Sapması")
    else: st.success("🟢 NORMAL ŞARTLAR")

    with st.expander("🕔 Detaylı Akış"):
        if not kpi_df.empty: st.write("**KPI:**", kpi_df)
        if not uretim_df.empty: st.write("**Üretim:**", uretim_df)
        if not sosts_df.empty: st.write("**Soğuk Oda:**", sosts_df)
        if not hijyen_df.empty: st.write("**Hijyen:**", hijyen_df)
        if not temizlik_df.empty: st.write("**Temizlik:**", temizlik_df)

# --- MODÜL 4: PERSONEL HİJYEN ÖZETİ ---
def _render_hijyen_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM hijyen_kontrol_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("⚠️ Kayıt bulunamadı."); return
    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
    if not uygunsuzluk.empty:
        st.error(f"⚠️ {len(uygunsuzluk)} Uygunsuzluk / Devamsızlık")
        st.dataframe(uygunsuzluk, use_container_width=True, hide_index=True)
        st.bar_chart(uygunsuzluk['durum'].value_counts())
    else: st.success("✅ Sorunsuz")
    with st.expander("📋 Tüm Kayıtlar"): st.dataframe(df, use_container_width=True, hide_index=True)

# --- MODÜL 5: TEMİZLİK TAKİP RAPORU ---
def _render_temizlik_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if not df.empty:
        st.success(f"✅ {len(df)} görev tamamlandı.")
        st.bar_chart(df.groupby('bolum').size()); st.dataframe(df, use_container_width=True)
    else: st.warning("Kayıt yok")

# --- MODÜL 6: LOKASYON & PROSES HARİTASI ---
def _render_interactive_location(loc_id, loc_df, tree, proses_map, level=0):
    try: loc_row = loc_df[loc_df['id'] == loc_id].iloc[0]
    except: return
    l_ad, l_tip = loc_row['ad'], loc_row['tip']
    icon = {"Kat": "🏢", "Bölüm": "🏭", "Hat": "🛤️", "Ekipman": "⚙️"}.get(l_tip, "📍")
    p_badges = ""
    if not proses_map.empty:
        p_list = proses_map[proses_map['lokasyon_id'] == loc_id]
        for _, p in p_list.iterrows():
            if pd.notna(p['proses_adi']): p_badges += f" <span style='background:#E8F8F5; color:#117864; padding:2px 6px; border-radius:4px; font-size:0.8em;'>{p.get('ikon','🔧')} {p['proses_adi']}</span>"
    children = tree.get(loc_id, [])
    if children:
        with st.expander(f"{icon} {l_ad} ({len(children)}) {l_tip}", expanded=(l_tip == 'Kat')):
            if p_badges: st.markdown(p_badges, unsafe_allow_html=True)
            for cid in children: _render_interactive_location(cid, loc_df, tree, proses_map, level + 1)
    else: st.markdown(f'<div style="margin-left:20px; border-left:4px solid #FF4B4B; padding:5px;">{icon} <b>{l_ad}</b> {p_badges}</div>', unsafe_allow_html=True)

def _render_graphviz_map(loc_df, tree, roots, proses_map):
    dot = 'digraph FactoryMap { rankdir=LR; node [shape=box, style=filled, fontname=Arial, fontsize=10];\n'
    def add_dot_recursive(loc_id):
        try: row = loc_df[loc_df['id'] == loc_id].iloc[0]
        except: return ""
        ad, tip = row['ad'], row['tip']
        children = tree.get(loc_id, [])
        out = ""
        if children:
            out += f'subgraph cluster_{loc_id} {{ label="{ad}"; style=filled; fillcolor=ivory; '
            for cid in children: out += add_dot_recursive(cid)
            out += '} '
        else: out += f'node_{loc_id} [label="{ad}\\n({tip})", fillcolor=lightgrey]; '
        return out
    for rid in roots: dot += add_dot_recursive(rid)
    dot += '}'
    st.graphviz_chart(dot, use_container_width=True)

def _render_lokasyon_haritasi():
    st.info("Kurumsal Lokasyon Haritası")
    loc_df = run_query("SELECT * FROM lokasyonlar WHERE aktif IS TRUE")
    try: proses_map = run_query("SELECT lpa.lokasyon_id, pt.ad as proses_adi, pt.ikon FROM lokasyon_proses_atama lpa JOIN proses_tipleri pt ON lpa.proses_tip_id = pt.id WHERE lpa.aktif IS TRUE")
    except: proses_map = pd.DataFrame()
    if loc_df.empty: st.warning("Veri yok"); return
    tree, roots = {}, []
    ids = set(loc_df['id'].unique())
    for _, r in loc_df.iterrows():
        lid, pid = int(r['id']), r['parent_id']
        if pd.isna(pid) or pid == 0 or int(pid) not in ids: roots.append(lid)
        else: tree.setdefault(int(pid), []).append(lid)
    tip = st.radio("Görünüm:", ["İnteraktif", "Şematik"], horizontal=True)
    if tip == "İnteraktif":
        for rid in roots: _render_interactive_location(rid, loc_df, tree, proses_map)
    else: _render_graphviz_map(loc_df, tree, roots, proses_map)

# --- MODÜL 7: PERSONEL ORGANİZASYON ŞEMASI ---
def _render_dept_recursive(dept_id, dept_name, all_depts, pers_df, is_expanded=True):
    sub = all_depts[all_depts['ana_departman_id'] == dept_id]
    staff = pers_df[pers_df['departman_id'] == dept_id].sort_values('pozisyon_seviye')
    all_sub_ids = get_all_sub_department_ids(dept_id)
    tree_total = len(pers_df[pers_df['departman_id'].isin(all_sub_ids)])
    
    with st.expander(f"🏢 {dept_name} | Toplam: {tree_total}", expanded=is_expanded):
        if not staff.empty:
            for _, p in staff.iterrows():
                st.markdown(f"• {get_position_icon(p['pozisyon_seviye'])} **{p['ad_soyad']}** ({p['gorev'] or p['rol']})")
        for _, s in sub.iterrows(): _render_dept_recursive(s['id'], s['bolum_adi'], all_depts, pers_df, False)

def _render_organizasyon_semasi():
    pers_df = get_personnel_hierarchy()
    if pers_df.empty: st.warning("Veri yok"); return
    all_depts = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = TRUE")
    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    for _, d in top.iterrows():
        if d['id'] != 1: _render_dept_recursive(d['id'], d['bolum_adi'], all_depts, pers_df)

# --- PLACEHOLDERS ---
def _render_soguk_oda_izleme(bas_tarih, bit_tarih):
    """📊 Ölçüm matrisi görünümü (Tarih Aralığı Destekli)."""
    st.subheader("❄️ Sıcaklık İzleme Raporu")
    if not engine:
        st.error("Veritabanı bağlantısı yok.")
        return
    df_matris = get_matrix_data(engine, bas_tarih, bit_tarih)
    if not df_matris.empty:
        # 'beklenen_zaman' yerine 'zaman' kullanılıyor (soguk_oda_utils.py güncellemesine uygun)
        # Tarih ve Saati ayrı ayrı göster
        df_matris['zaman'] = pd.to_datetime(df_matris['zaman'])
        df_matris['tarih'] = df_matris['zaman'].dt.strftime('%Y-%m-%d')
        df_matris['saat'] = df_matris['zaman'].dt.strftime('%H:%M')
        status_icons = {'BEKLIYOR': '⚪', 'TAMAMLANDI': '✅', 'GECIKTI': '⏰', 'ATILDI': '❌', 'MANUEL': '📝'}
        df_matris['display'] = df_matris['durum'].map(status_icons).fillna('📝') + " " + df_matris['sicaklik_degeri'].astype(str).replace('nan', '')
        
        # ODA ADI + TARİH bazında satırlar, SAAT bazında sütunlar
        df_matris['oda_tarih'] = df_matris['oda_adi'] + " (" + df_matris['tarih'] + ")"
        df_matris = df_matris.drop_duplicates(subset=['oda_tarih', 'saat'], keep='last')
        pivot = df_matris.pivot(index='oda_tarih', columns='saat', values='display').fillna('—')
        st.dataframe(pivot, use_container_width=True)
    else:
        st.info("Bu tarih aralığı için henüz planlanmış ölçüm bulunmuyor.")

def _render_soguk_oda_trend():
    """📈 Sıcaklık trend analizi."""
    st.subheader("📈 Sıcaklık Trend Analizi")
    if not engine: return
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE aktif = 1")
    if rooms.empty:
        st.info("Kayıtlı oda bulunamadı.")
        return
    target = st.selectbox("Oda Seçiniz:", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])
    df = get_trend_data(engine, target)
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="Sıcaklık Değişim Trendi")
        fig.add_hline(y=float(df['min_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        fig.add_hline(y=float(df['max_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kayıtlı veri bulunamadı.")

# --- ANA ORKESTRATÖR ---
def render_raporlama_module(engine_param):
    global engine; engine = engine_param
    if not kullanici_yetkisi_var_mi("📊 Kurumsal Raporlama", "Görüntüle"):
        st.error("🚫 Yetki yok."); st.stop()
    st.title("📊 Kurumsal Raporlar")
    c1, c2, c3 = st.columns(3)
    bas_tarih = c1.date_input("Başlangıç", get_istanbul_time() - timedelta(days=7))
    bit_tarih = c2.date_input("Bitiş", get_istanbul_time())
    rapor_tipi = c3.selectbox("Kategori", [
        "🏭 Üretim ve Verimlilik", 
        "🍩 Kalite (KPI) Analizi", 
        "📅 Günlük Operasyonel Rapor", 
        "🧼 Personel Hijyen Özeti", 
        "🧹 Temizlik Takip Raporu", 
        "📍 Kurumsal Lokasyon & Proses Haritası", 
        "👥 Personel Organizasyon Şeması",
        "❄️ Soğuk Oda İzleme",
        "📈 Soğuk Oda Trend"
    ])
    
    # Rapor tetikleme butonu ve state yönetimi
    if st.button("Raporu Oluştur", use_container_width=True):
        st.session_state.report_triggered = True
        st.session_state.active_report_type = rapor_tipi

    if st.session_state.get("report_triggered"):
        # Seçilen rapor tipini state'den al (selectbox değişse bile butona basılana kadar eski rapor kalır)
        r_type = st.session_state.active_report_type
        
        if "Üretim" in r_type: _render_uretim_raporu(bas_tarih, bit_tarih)
        elif "KPI" in r_type: _render_kpi_raporu(bas_tarih, bit_tarih)
        elif "Operasyonel" in r_type: _render_gunluk_operasyonel_rapor(bas_tarih)
        elif "Hijyen" in r_type: _render_hijyen_raporu(bas_tarih, bit_tarih)
        elif "Temizlik" in r_type: _render_temizlik_raporu(bas_tarih, bit_tarih)
        elif "Lokasyon" in r_type: _render_lokasyon_haritasi()
        elif "Organizasyon" in r_type: _render_organizasyon_semasi()
        elif "İzleme" in r_type: _render_soguk_oda_izleme(bas_tarih, bit_tarih)
        elif "Trend" in r_type: _render_soguk_oda_trend()
