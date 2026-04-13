import streamlit as st
import pandas as pd
from sqlalchemy import text

from logic.data_fetcher import (
    get_hierarchy_flat
)
from logic.cache_manager import clear_personnel_cache
from logic.sync_handler import render_sync_button

def _get_lokasyon_tipleri(engine):
    """DB'den tipleri çeker. Hata olursa Anayasa gereği fallback listesine döner."""
    try:
        t_df = pd.read_sql("SELECT tip_adi FROM lokasyon_tipleri WHERE aktif = 1 ORDER BY sira_no", engine)
        if not t_df.empty:
            return t_df['tip_adi'].tolist()
    except Exception:
        pass
    return ["Kat", "Bölüm", "Hat", "Ekipman"]

def _render_lokasyon_form(engine, lok_df, lst_bolumler, lok_tipleri):
    """Yeni Lokasyon Ekleme Formu"""
    with st.expander("➕ Yeni Lokasyon Ekle"):
        col1, col2 = st.columns(2)
        new_lok_tip = col1.selectbox("Lokasyon Tipi", lok_tipleri, key="new_lok_tip_ui")
        new_lok_ad = col2.text_input("Lokasyon Adı", key="new_lok_ad_ui")
        new_lok_dept = col1.selectbox("Sorumlu Departman", ["(Seçiniz)"] + lst_bolumler, key="new_lok_dept_ui")

        def _get_path(row_id):
            path = []
            curr = lok_df[lok_df['id'] == row_id]
            while not curr.empty:
                r = curr.iloc[0]
                icon = '🏢' if r['tip']=='Kat' else '🏭' if r['tip']=='Bölüm' else '🛤️' if r['tip']=='Hat' else '⚙️'
                path.insert(0, f"{icon} {r['ad']}")
                if pd.notna(r.get('parent_id')) and r['parent_id']:
                    curr = lok_df[lok_df['id'] == int(r['parent_id'])]
                else:
                    break
            return " › ".join(path)

        parent_options = {0: "- Ana Lokasyon -"}
        if not lok_df.empty:
            parents = pd.DataFrame()
            idx = lok_tipleri.index(new_lok_tip) if new_lok_tip in lok_tipleri else -1
            if idx > 0:
                parents = lok_df[lok_df['tip'] == lok_tipleri[idx-1]]
            elif idx == 0:
                parents = pd.DataFrame()
            else:
                parents = lok_df
            
            for _, row in parents.iterrows():
                parent_options[row['id']] = _get_path(row['id'])

        new_parent = st.selectbox("Üst Lokasyon", options=list(parent_options.keys()), format_func=lambda x: parent_options[x], key="new_parent_ui")

        if st.button("💾 Lokasyonu Ekle", use_container_width=True):
            if new_lok_ad:
                try:
                    # --- ANAYASA v4.0: ATOMIK TRANSACTION ---
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO lokasyonlar (ad, tip, parent_id, sorumlu_departman) VALUES (:a, :t, :p, :d)"),
                                   {"a": new_lok_ad, "t": new_lok_tip, "p": None if new_parent == 0 else new_parent, "d": new_lok_dept if new_lok_dept != "(Seçiniz)" else None})
                        
                        # Madde 6: Audit Log Zırhı (Artık aynı transaksiyonun parçası)
                        try:
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('LOKASYON_EKLE', :d)"), {"d": f"{new_lok_ad} ({new_lok_tip}) eklendi."})
                        except: pass
                        
                    clear_personnel_cache(); st.toast("✅ Fabrika Lokasyonu başarıyla eklendi!"); st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Ekleme başarısız (İşlem Geri Alındı): {e}")

_LOK_ICONS = {'Kat': '🏢', 'Bölüm': '🏭', 'Hat': '🛤️', 'Ekipman': '⚙️'}

def _lok_icon(tip):
    return _LOK_ICONS.get(str(tip), '📍')

def _pid_eslesir(x, hedef):
    try:
        return pd.notna(x) and int(x) == int(hedef)
    except Exception:
        return False

def _render_lok_satir(row, depth=0):
    pad = "&nbsp;" * (depth * 6)
    icon = _lok_icon(row['tip'])
    dept_val = row['sorumlu_departman'] if 'sorumlu_departman' in row.index and pd.notna(row['sorumlu_departman']) else ""
    dept = f" <small style='color:#888'>({dept_val})</small>" if dept_val else ""
    aktif_val = row['aktif'] if 'aktif' in row.index else 1
    aktif = "" if aktif_val in [True, 1, 'True', '1'] else " 🔴"
    st.markdown(f"{pad}{icon} **{row['ad']}**{dept}{aktif}", unsafe_allow_html=True)

def _cocuklar(lok_df, tip, parent_id):
    """Belirli tip ve parent_id'ye sahip lokasyonları döner."""
    mask = (lok_df['tip'] == tip) & lok_df['parent_id'].apply(lambda x: _pid_eslesir(x, parent_id))
    return lok_df[mask]

def _render_lok_agac(lok_df, lok_tipleri):
    """4 seviyeli hiyerarşik ağaç."""
    if lok_df.empty or not lok_tipleri:
        return
    for _, l1 in lok_df[lok_df['tip'] == lok_tipleri[0]].iterrows():
        with st.container(border=True):
            _render_lok_satir(l1, 0)
            if len(lok_tipleri) < 2:
                continue
            for _, l2 in _cocuklar(lok_df, lok_tipleri[1], l1['id']).iterrows():
                _render_lok_satir(l2, 1)
                if len(lok_tipleri) < 3:
                    continue
                for _, l3 in _cocuklar(lok_df, lok_tipleri[2], l2['id']).iterrows():
                    _render_lok_satir(l3, 2)
                    if len(lok_tipleri) < 4:
                        continue
                    for _, l4 in _cocuklar(lok_df, lok_tipleri[3], l3['id']).iterrows():
                        _render_lok_satir(l4, 3)

def _lok_duzenle_kaydet(engine, data):
    """Lokasyon güncelleme işlemi."""
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE lokasyonlar SET ad=:ad, tip=:tip, parent_id=:pid, "
            "sorumlu_departman=:dept, aktif=:aktif, sira_no=:sira WHERE id=:id"
        ), data)
        try:
            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('LOKASYON_GUNCELLE',:d)"),
                         {"d": f"{data['ad']} ({data['tip']}) güncellendi."})
        except Exception:
            pass
    clear_personnel_cache()

def _render_lok_duzenle_form(engine, lok_df, lok_tipleri, lst_bolumler):
    """Seçilen lokasyonu güncelleme formu."""
    def _get_path(row_id):
        path = []
        curr = lok_df[lok_df['id'] == row_id]
        while not curr.empty:
            r = curr.iloc[0]
            path.insert(0, f"{_lok_icon(r['tip'])} {r['ad']}")
            if pd.notna(r.get('parent_id')) and r['parent_id']:
                curr = lok_df[lok_df['id'] == int(r['parent_id'])]
            else:
                break
        return " › ".join(path)

    opts = {f"{_get_path(r['id'])} [{r['tip']}]": r['id'] for _, r in lok_df.iterrows()}
    secim = st.selectbox("Düzenlenecek Lokasyon", list(opts.keys()), key="lok_ed_sec_ui")
    if not secim:
        return
    sel_id = opts[secim]
    sel = lok_df[lok_df['id'] == sel_id].iloc[0]
    c1, c2 = st.columns(2)
    new_ad  = c1.text_input("📛 Ad", value=str(sel['ad']), key=f"lok_ed_ad_{sel_id}")
    tip_idx = lok_tipleri.index(sel['tip']) if sel['tip'] in lok_tipleri else 0
    new_tip = c1.selectbox("🏷️ Tip", lok_tipleri, index=tip_idx, key=f"lok_ed_tip_{sel_id}")
    par_opts = {0: "— Ana Lokasyon —"}
    t_idx = lok_tipleri.index(new_tip) if new_tip in lok_tipleri else -1
    if t_idx > 0:
        for _, p in lok_df[lok_df['tip'] == lok_tipleri[t_idx - 1]].iterrows():
            par_opts[int(p['id'])] = _get_path(p['id'])
    cur_par  = int(sel['parent_id']) if 'parent_id' in sel.index and pd.notna(sel['parent_id']) and sel['parent_id'] else 0
    par_keys = list(par_opts.keys())
    new_par  = c2.selectbox("🔗 Üst Lokasyon", par_keys, format_func=lambda x: par_opts[x],
                             index=par_keys.index(cur_par) if cur_par in par_keys else 0,
                             key=f"lok_ed_par_{sel_id}")
    dept_opts = ["(Departman Yok)"] + lst_bolumler
    cur_dept  = (sel['sorumlu_departman'] if 'sorumlu_departman' in sel.index and pd.notna(sel['sorumlu_departman']) else None) or "(Departman Yok)"
    new_dept  = c2.selectbox("🏛️ Sorumlu Departman", dept_opts,
                              index=dept_opts.index(cur_dept) if cur_dept in dept_opts else 0,
                              key=f"lok_ed_dept_{sel_id}")
    c3, c4   = st.columns(2)
    aktif_val = sel['aktif'] if 'aktif' in sel.index else 1
    new_aktif = c3.checkbox("✅ Aktif", value=aktif_val in [True, 1, 'True', '1'], key=f"lok_ed_aktif_{sel_id}")
    sira_val  = sel['sira_no'] if 'sira_no' in sel.index and pd.notna(sel['sira_no']) else 0
    new_sira  = c4.number_input("🔢 Sıra No", value=int(sira_val), min_value=0, step=1, key=f"lok_ed_sira_{sel_id}")
    if st.button("💾 Lokasyonu Güncelle", use_container_width=True, key=f"lok_ed_kaydet_{sel_id}"):
        try:
            _lok_duzenle_kaydet(engine, {
                "ad": new_ad, "tip": new_tip,
                "pid": None if new_par == 0 else new_par,
                "dept": None if "(Departman Yok)" in new_dept else new_dept,
                "aktif": 1 if new_aktif else 0, "sira": new_sira, "id": int(sel_id)
            })
            st.toast(f"✅ {new_ad} güncellendi!"); st.rerun()
        except Exception as e:
            st.error(f"⚠️ Güncelleme başarısız: {e}")

def _render_lokasyon_table(engine, lok_df, lok_tipleri, lst_bolumler):
    """Hiyerarşi görünümü + düzenleme formu."""
    if lok_df.empty:
        st.info("Henüz lokasyon eklenmemiş.")
        return
    st.caption("📋 Mevcut Lokasyon Hiyerarşisi")
    _render_lok_agac(lok_df, lok_tipleri)
    with st.expander("📝 Lokasyonu Düzenle"):
        _render_lok_duzenle_form(engine, lok_df, lok_tipleri, lst_bolumler)

def render_lokasyon_tab(engine):
    st.subheader("📍 Lokasyon Yönetimi (Hiyerarşik)")
    st.caption("Fabrika lokasyon hiyerarşisini ve sorumlu departmanları buradan yönetebilirsiniz")

    lst_bolumler = []
    try:
        b_df = pd.read_sql("SELECT id, ad as bolum_adi, ust_id as ana_departman_id, aktif FROM qms_departmanlar WHERE aktif = 1", engine)
        lst_bolumler = get_hierarchy_flat(b_df)
    except Exception:
        lst_bolumler = ["Üretim", "Depo", "Kalite", "Bakım"]

    try:
        lok_df = pd.read_sql("SELECT * FROM lokasyonlar ORDER BY tip, sira_no, ad", engine)
    except Exception:
        lok_df = pd.DataFrame()

    lok_tipleri = _get_lokasyon_tipleri(engine)

    try:
        _render_lokasyon_form(engine, lok_df, lst_bolumler, lok_tipleri)
    except Exception as e:
        st.error("Lokasyon ekleme formunda beklenmeyen bir hata oluştu.")
        
    try:
        _render_lokasyon_table(engine, lok_df, lok_tipleri, lst_bolumler)
    except Exception as e:
        st.error(f"Lokasyon tablosunda beklenmeyen bir hata oluştu: {e}")
        
    render_sync_button(key_prefix="lokasyonlar_ui")

def render_proses_tab(engine):
    st.subheader("🔧 Modüler Proses Yönetimi")
    t_proses1, t_proses2 = st.tabs(["📋 Proses Tipleri", "🔗 Lokasyon-Proses Ataması"])
    with t_proses1:
        proses_df = pd.read_sql("SELECT * FROM proses_tipleri ORDER BY id", engine)
        with st.expander("➕ Yeni Proses Tipi Ekle"):
            with st.form("new_proses_form_ui"):
                p_kod = st.text_input("Kod").upper()
                p_ad = st.text_input("Ad")
                if st.form_submit_button("Ekle") and p_kod and p_ad:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO proses_tipleri (kod, ad) VALUES (:k, :a)"), {"k": p_kod, "a": p_ad})
                        clear_personnel_cache(); st.toast("✅ Proses Tipi Eklendi!"); st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Ekleme hatası: {e}")
        st.dataframe(proses_df, use_container_width=True, hide_index=True)
    render_sync_button(key_prefix="proses_ui")
