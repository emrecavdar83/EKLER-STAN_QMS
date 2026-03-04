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
    """Excel indirme butonu olu┼şturur."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Detayl─▒ Kay─▒tlar')
            if urun_ozet is not None:
                urun_ozet.to_excel(writer, index=False, sheet_name='├£r├╝n ├ûzeti')
        excel_data = output.getvalue()
        st.download_button(label="­şôÑ Excel Olarak ─░ndir", data=excel_data, file_name=f"uretim_raporu_{bas_tarih}_{bit_tarih}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.caption(f"Ôä╣´©Å Excel indirme: openpyxl k├╝t├╝phanesi gereklidir (pip install openpyxl)")

# --- MOD├£L 1: ├£RET─░M VE VER─░ML─░L─░K ---
def _render_uretim_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarihler aras─▒nda ├╝retim kayd─▒ bulunamad─▒.")
        return
    df.columns = [c.lower() for c in df.columns]
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam ├£retim (Adet)", f"{df['miktar'].sum():,}")
    k2.metric("Toplam Fire", f"{df['fire'].sum():,}")
    fire_oran = (df['fire'].sum() / df['miktar'].sum()) * 100 if df['miktar'].sum() > 0 else 0
    k3.metric("Ortalama Fire Oran─▒", f"%{fire_oran:.2f}")

    st.subheader("­şôĞ ├£r├╝n Baz─▒nda ├ûzet")
    urun_ozet = df.groupby('urun').agg({'miktar': 'sum', 'fire': 'sum', 'lot_no': 'count'}).reset_index()
    urun_ozet.columns = ['├£r├╝n Ad─▒', 'Toplam ├£retim', 'Toplam Fire', 'Lot Say─▒s─▒']
    urun_ozet['Fire Oran─▒ (%)'] = (urun_ozet['Toplam Fire'] / urun_ozet['Toplam ├£retim'] * 100).round(2)
    st.dataframe(urun_ozet.sort_values('Toplam ├£retim', ascending=False), use_container_width=True, hide_index=True)

    st.subheader("­şôï Detayl─▒ Kay─▒tlar")
    cols = ['tarih', 'saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    rename_map = {'tarih': 'Tarih', 'saat': 'Saat', 'vardiya': 'Vardiya', 'urun': '├£r├╝n Ad─▒', 'lot_no': 'Lot No', 'miktar': 'Miktar', 'fire': 'Fire', 'kullanici': 'Kaydeden Kullan─▒c─▒', 'notlar': 'Notlar'}
    df_display.columns = [rename_map.get(c, c) for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    _rapor_excel_export(df_display, urun_ozet, bas_tarih, bit_tarih)

# --- MOD├£L 2: KAL─░TE (KPI) ANAL─░Z─░ ---
def _render_kpi_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Kalite kayd─▒ bulunamad─▒.")
        return
    k1, k2 = st.columns(2)
    onay_sayisi = len(df[df['karar'] == 'ONAY'])
    red_sayisi = len(df[df['karar'] == 'RED'])
    k1.success(f"Ô£à Onaylanan: {onay_sayisi}"); k2.error(f"ÔØî Reddedilen: {red_sayisi}")
    red_df = df[df['karar'] == 'RED'].groupby('urun').size().reset_index(name='Red Adeti')
    if not red_df.empty:
        st.write("­şöö **En ├çok Red Alan ├£r├╝nler**")
        st.table(red_df)
    st.dataframe(df, use_container_width=True)

# --- MOD├£L 3: G├£NL├£K OPERASYONEL RAPOR ---
def _render_gunluk_operasyonel_rapor(bas_tarih):
    st.info("­şÆí Bu rapor belirledi─şiniz tarihteki i┼şlemleri ├Âzetler.")
    t_str = str(bas_tarih)
    kpi_df = run_query(f"SELECT tarih, saat, urun, karar, notlar, vardiya FROM urun_kpi_kontrol WHERE tarih='{t_str}'")
    uretim_df = run_query(f"SELECT tarih, saat, urun, miktar, vardiya FROM depo_giris_kayitlari WHERE tarih='{t_str}'")
    hijyen_df = run_query(f"SELECT tarih, saat, personel, durum, sebep, aksiyon, vardiya, bolum FROM hijyen_kontrol_kayitlari WHERE tarih='{t_str}'")
    temizlik_df = run_query(f"SELECT tarih, saat, bolum, islem, durum FROM temizlik_kayitlari WHERE tarih='{t_str}'")
    
    # SOSTS Verisi (SQLite/Postgres Uyumlu Tarih Filtresi)
    sosts_query = f"SELECT o.oda_adi, m.sicaklik_degeri, m.sapma_var_mi, m.olcum_zamani FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id WHERE {'DATE(m.olcum_zamani)' if 'sqlite' in str(engine.url) else 'm.olcum_zamani::date'} = '{t_str}'"
    sosts_df = run_query(sosts_query)

    v_secim = st.multiselect("Vardiya Se├ğimi", VARDIYA_LISTESI, default=VARDIYA_LISTESI)
    depts = hijyen_df['bolum'].dropna().unique().tolist() if not hijyen_df.empty else []
    d_secim = st.multiselect("Departman Se├ğimi", ["T├╝m├╝"] + depts, default=["T├╝m├╝"])

    if not kpi_df.empty: kpi_df = kpi_df[kpi_df['vardiya'].isin(v_secim)] if 'vardiya' in kpi_df.columns else kpi_df
    if not uretim_df.empty: uretim_df = uretim_df[uretim_df['vardiya'].isin(v_secim)]
    if not hijyen_df.empty:
        hijyen_df = hijyen_df[hijyen_df['vardiya'].isin(v_secim)]
        if "T├╝m├╝" not in d_secim: hijyen_df = hijyen_df[hijyen_df['bolum'].isin(d_secim)]

    red_s = len(kpi_df[kpi_df['karar'] == 'RED']) if not kpi_df.empty else 0
    uyg_h = len(hijyen_df[hijyen_df['durum'] != 'Sorun Yok']) if not hijyen_df.empty else 0
    maz_s = len(hijyen_df[hijyen_df['durum'] == 'Gelmedi']) if not hijyen_df.empty else 0
    sapma_s = len(sosts_df[sosts_df['sapma_var_mi'] == 1]) if not sosts_df.empty else 0
    
    if (red_s + uyg_h + maz_s + sapma_s) > 0:
        st.error(f"­şö┤ D─░KKAT: {red_s} RED | {maz_s} Gelmedi | {uyg_h} Hijyen | {sapma_s} Oda Sapmas─▒")
    else: st.success("­şşó NORMAL ┼ŞARTLAR")

    with st.expander("­şòö Detayl─▒ Ak─▒┼ş"):
        if not kpi_df.empty: st.write("**KPI:**", kpi_df)
        if not uretim_df.empty: st.write("**├£retim:**", uretim_df)
        if not sosts_df.empty: st.write("**So─şuk Oda:**", sosts_df)
        if not hijyen_df.empty: st.write("**Hijyen:**", hijyen_df)
        if not temizlik_df.empty: st.write("**Temizlik:**", temizlik_df)

# --- MOD├£L 4: PERSONEL H─░JYEN ├ûZET─░ ---
def _render_hijyen_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM hijyen_kontrol_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("ÔÜá´©Å Kay─▒t bulunamad─▒."); return
    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
    if not uygunsuzluk.empty:
        st.error(f"ÔÜá´©Å {len(uygunsuzluk)} Uygunsuzluk / Devams─▒zl─▒k")
        st.dataframe(uygunsuzluk, use_container_width=True, hide_index=True)
        st.bar_chart(uygunsuzluk['durum'].value_counts())
    else: st.success("Ô£à Sorunsuz")
    with st.expander("­şôï T├╝m Kay─▒tlar"): st.dataframe(df, use_container_width=True, hide_index=True)

# --- MOD├£L 5: TEM─░ZL─░K TAK─░P RAPORU ---
def _render_temizlik_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if not df.empty:
        st.success(f"Ô£à {len(df)} g├Ârev tamamland─▒.")
        st.bar_chart(df.groupby('bolum').size()); st.dataframe(df, use_container_width=True)
    else: st.warning("Kay─▒t yok")

# --- MOD├£L 6: LOKASYON & PROSES HAR─░TASI ---
def _render_interactive_location(loc_id, loc_df, tree, proses_map, level=0):
    try: loc_row = loc_df[loc_df['id'] == loc_id].iloc[0]
    except: return
    l_ad, l_tip = loc_row['ad'], loc_row['tip']
    icon = {"Kat": "­şÅó", "B├Âl├╝m": "­şÅ¡", "Hat": "­şøñ´©Å", "Ekipman": "ÔÜÖ´©Å"}.get(l_tip, "­şôı")
    p_badges = ""
    if not proses_map.empty:
        p_list = proses_map[proses_map['lokasyon_id'] == loc_id]
        for _, p in p_list.iterrows():
            if pd.notna(p['proses_adi']): p_badges += f" <span style='background:#E8F8F5; color:#117864; padding:2px 6px; border-radius:4px; font-size:0.8em;'>{p.get('ikon','­şöğ')} {p['proses_adi']}</span>"
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
    st.info("Kurumsal Lokasyon Haritas─▒")
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
    tip = st.radio("G├Âr├╝n├╝m:", ["─░nteraktif", "┼Şematik"], horizontal=True)
    if tip == "─░nteraktif":
        for rid in roots: _render_interactive_location(rid, loc_df, tree, proses_map)
    else: _render_graphviz_map(loc_df, tree, roots, proses_map)

# --- MOD├£L 7: PERSONEL ORGAN─░ZASYON ┼ŞEMASI ---
def _render_dept_recursive(dept_id, dept_name, all_depts, pers_df, is_expanded=True):
    sub = all_depts[all_depts['ana_departman_id'] == dept_id]
    staff = pers_df[pers_df['departman_id'] == dept_id].sort_values('pozisyon_seviye')
    all_sub_ids = get_all_sub_department_ids(dept_id)
    tree_total = len(pers_df[pers_df['departman_id'].isin(all_sub_ids)])
    
    with st.expander(f"­şÅó {dept_name} | Toplam: {tree_total}", expanded=is_expanded):
        if not staff.empty:
            for _, p in staff.iterrows():
                st.markdown(f"ÔÇó {get_position_icon(p['pozisyon_seviye'])} **{p['ad_soyad']}** ({p['gorev'] or p['rol']})")
        for _, s in sub.iterrows(): _render_dept_recursive(s['id'], s['bolum_adi'], all_depts, pers_df, False)

def _render_organizasyon_semasi():
    pers_df = get_personnel_hierarchy()
    if pers_df.empty: st.warning("Veri yok"); return
    all_depts = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = TRUE")
    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    for _, d in top.iterrows():
        if d['id'] != 1: _render_dept_recursive(d['id'], d['bolum_adi'], all_depts, pers_df)

# --- PLACEHOLDERS ---
def _render_soguk_oda_izleme(sel_date):
    """­şôè G├╝nl├╝k ├Âl├ğ├╝m matrisi g├Âr├╝n├╝m├╝."""
    st.subheader("ÔØä´©Å G├╝nl├╝k S─▒cakl─▒k ─░zleme")
    if not engine:
        st.error("Veritaban─▒ ba─şlant─▒s─▒ yok.")
        return
    df_matris = get_matrix_data(str(engine.url), sel_date)
    if not df_matris.empty:
        # 'beklenen_zaman' yerine 'zaman' kullan─▒l─▒yor (soguk_oda_utils.py g├╝ncellemesine uygun)
        df_matris['saat'] = pd.to_datetime(df_matris['zaman']).dt.strftime('%H:%M')
        status_icons = {'BEKLIYOR': 'ÔÜ¬', 'TAMAMLANDI': 'Ô£à', 'GECIKTI': 'ÔÅ░', 'ATILDI': 'ÔØî'}
        df_matris['display'] = df_matris['durum'].map(status_icons) + " " + df_matris['sicaklik_degeri'].astype(str).replace('nan', '')
        pivot = df_matris.pivot(index='oda_adi', columns='saat', values='display').fillna('ÔÇö')
        st.dataframe(pivot, use_container_width=True)
    else:
        st.info("Bu tarih i├ğin hen├╝z planlanm─▒┼ş ├Âl├ğ├╝m bulunmuyor.")

def _render_soguk_oda_trend():
    """­şôê S─▒cakl─▒k trend analizi."""
    st.subheader("­şôê S─▒cakl─▒k Trend Analizi")
    if not engine: return
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE aktif = 1")
    if rooms.empty:
        st.info("Kay─▒tl─▒ oda bulunamad─▒.")
        return
    target = st.selectbox("Oda Se├ğiniz:", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])
    df = get_trend_data(str(engine.url), target)
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="S─▒cakl─▒k De─şi┼şim Trendi")
        fig.add_hline(y=float(df['min_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        fig.add_hline(y=float(df['max_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kay─▒tl─▒ veri bulunamad─▒.")

# --- ANA ORKESTRAT├ûR ---
def render_raporlama_module(engine_param):
    global engine; engine = engine_param
    if not kullanici_yetkisi_var_mi("­şôè Kurumsal Raporlama", "G├Âr├╝nt├╝le"):
        st.error("­şÜ½ Yetki yok."); st.stop()
    st.title("­şôè Kurumsal Raporlar")
    c1, c2, c3 = st.columns(3)
    bas_tarih = c1.date_input("Ba┼şlang─▒├ğ", get_istanbul_time() - timedelta(days=7))
    bit_tarih = c2.date_input("Biti┼ş", get_istanbul_time())
    rapor_tipi = c3.selectbox("Kategori", [
        "­şÅ¡ ├£retim ve Verimlilik", 
        "­şı® Kalite (KPI) Analizi", 
        "­şôà G├╝nl├╝k Operasyonel Rapor", 
        "­şğ╝ Personel Hijyen ├ûzeti", 
        "­şğ╣ Temizlik Takip Raporu", 
        "­şôı Kurumsal Lokasyon & Proses Haritas─▒", 
        "­şæÑ Personel Organizasyon ┼Şemas─▒",
        "ÔØä´©Å So─şuk Oda ─░zleme",
        "­şôê So─şuk Oda Trend"
    ])
    
    if st.button("Raporu Olu┼ştur", use_container_width=True):
        if "├£retim" in rapor_tipi: _render_uretim_raporu(bas_tarih, bit_tarih)
        elif "KPI" in rapor_tipi: _render_kpi_raporu(bas_tarih, bit_tarih)
        elif "Operasyonel" in rapor_tipi: _render_gunluk_operasyonel_rapor(bas_tarih)
        elif "Hijyen" in rapor_tipi: _render_hijyen_raporu(bas_tarih, bit_tarih)
        elif "Temizlik" in rapor_tipi: _render_temizlik_raporu(bas_tarih, bit_tarih)
        elif "Lokasyon" in rapor_tipi: _render_lokasyon_haritasi()
        elif "Organizasyon" in rapor_tipi: _render_organizasyon_semasi()
        elif "─░zleme" in rapor_tipi: _render_soguk_oda_izleme(bas_tarih)
        elif "Trend" in rapor_tipi: _render_soguk_oda_trend()
