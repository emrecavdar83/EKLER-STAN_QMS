import streamlit as st
import pandas as pd
from sqlalchemy import text

from logic.data_fetcher import (
    run_query, get_qms_department_tree, get_qms_department_options_hierarchical
)
from logic.dept_logic import bolum_kodu_uret, miras_tip_guncelle, pasife_al_ve_aktar, hiyerarşi_kural_dogrula
from logic.cache_manager import clear_personnel_cache, clear_department_cache
from logic.sync_handler import render_sync_button

def render_rol_tab(engine):
    """Rol Yönetimi Sekmesi."""
    st.subheader("🎭 Rol Yönetimi")
    with st.expander("➕ Yeni Rol Ekle"):
        with st.form("new_role_form_ui"):
            new_rol = st.text_input("Rol Adı"); new_desc = st.text_area("Açıklama")
            if st.form_submit_button("Rolü Ekle") and new_rol:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES (:r, :a)"), {"r": new_rol, "a": new_desc})
                    st.toast("✅ Yeni rol eklendi!"); st.rerun()
                except Exception as e: st.error(f"⚠️ Hata: {e}")

    df = run_query("SELECT * FROM ayarlar_roller ORDER BY id")
    ed = st.data_editor(df, width="stretch", hide_index=True, num_rows="dynamic", key="editor_roller_ui")
    if st.button("💾 Rolleri Kaydet"):
        try:
            with engine.begin() as conn:
                for _, row in ed.iterrows():
                    act = 1 if row['aktif'] in [True, 1, 'True', '1'] else 0
                    if pd.notna(row['id']): conn.execute(text("UPDATE ayarlar_roller SET rol_adi=:r, aciklama=:a, aktif=:act WHERE id=:id"), {"r":row['rol_adi'], "a":row['aciklama'], "act":act, "id":row['id']})
                    else: conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES (:r, :a, :act)"), {"r":row['rol_adi'], "a":row['aciklama'], "act":act})
            clear_personnel_cache(); st.toast("✅ Güncellendi!"); st.rerun()
        except Exception as e: st.error(f"⚠️ Hata: {e}")
    render_sync_button(key_prefix="roller_ui")

def render_yetki_tab(engine):
    """Yetki Matrisi Sekmesi."""
    st.subheader("🔑 Zone & Modül Yetki Matrisi")
    roles = run_query("SELECT rol_adi, aktif FROM ayarlar_roller")
    if not roles.empty:
        active_roles = roles[roles['aktif'].isin([True, 1, '1', 'True'])]
        sel_rol = st.selectbox("🎭 Rol Seçin", active_roles['rol_adi'].tolist(), key="select_rol_yetki_ui")
        zone_map = {"ops": "🏭 Operasyon (ops)", "mgt": "📊 Yönetim (mgt)", "sys": "⚙️ Sistem (sys)"}
        sel_zone = st.radio("📍 Zone", options=["ops", "mgt", "sys"], format_func=lambda x: zone_map[x], horizontal=True)
        
        from logic.auth_logic import sistem_modullerini_ve_anahtarlarini_getir
        from logic.zone_yetki import yetki_haritasi_yukle
        mod_dict = sistem_modullerini_ve_anahtarlarini_getir()
        mod_info = run_query("SELECT modul_anahtari, zone FROM ayarlar_moduller")
        m2z = dict(zip(mod_info['modul_anahtari'], mod_info['zone']))
        prev_auth = run_query("SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = :r", params={"r": sel_rol})
        
        y_data = [{"Modül": k, "Anahtar": v, "Yetki": prev_auth[prev_auth['modul_adi']==v].iloc[0]['erisim_turu'] if not prev_auth[prev_auth['modul_adi']==v].empty else "Yok"} for k,v in mod_dict.items() if m2z.get(v)==sel_zone]
        if not y_data: st.warning("Bölgede modül yok."); return
        
        ed = st.data_editor(pd.DataFrame(y_data), width="stretch", hide_index=True, key=f"ed_y_{sel_rol}_{sel_zone}", column_config={"Anahtar": None, "Modül": st.column_config.TextColumn("Modül", disabled=True), "Yetki": st.column_config.SelectboxColumn("Yetki", options=["Yok", "Görüntüle", "Düzenle"])})
        if st.button(f"💾 {sel_rol} ({sel_zone}) Yetkilerini Kaydet"):
            try:
                with engine.begin() as conn:
                    target = [r['Anahtar'] for r in y_data]
                    p = {f"m{i}": k for i, k in enumerate(target)}; p['r'] = sel_rol
                    conn.execute(text(f"DELETE FROM ayarlar_yetkiler WHERE rol_adi=:r AND modul_adi IN ({', '.join([':m'+str(i) for i in range(len(target))])})"), p)
                    for _, r in ed.iterrows(): conn.execute(text("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"), {"r": sel_rol, "m": r['Anahtar'], "e": r['Yetki']})
                yetki_haritasi_yukle(engine, sel_rol, force_refresh=True); st.toast("✅ Güncellendi!"); st.rerun()
            except Exception as e: st.error(f"⚠️ Hata: {e}")
    render_sync_button(key_prefix="yetki_ui")

def _org_render_visuals():
    """Organizasyon şeması (Mermaid) ve liste görünümü."""
    c1, c2 = st.columns([2, 1])
    with c1:
        with st.expander("📊 Organizasyon Şeması (Grafik)", expanded=True):
            df = run_query("SELECT id, ad, ust_id FROM qms_departmanlar WHERE durum = 'AKTİF'")
            m_str = "graph TD\n"
            for _, r in df.iterrows():
                if r['ust_id']:
                    p_name = df[df['id']==r['ust_id']]['ad'].iloc[0] if not df[df['id']==r['ust_id']].empty else "KÖK"
                    m_str += f'    ID{r["ust_id"]}["{p_name}"] --> ID{r["id"]}["{r["ad"]}"]\n'
            st.markdown(f"```mermaid\n{m_str}\n```")
    with c2:
        with st.expander("🌳 Liste Görünümü"):
            for item in get_qms_department_tree(): st.markdown(f"• {item}")

def _org_render_types_editor(engine):
    """Bölüm türlerini yöneten data_editor."""
    with st.expander("🏷️ Bölüm Türlerini Yönet", expanded=False):
        df = run_query("SELECT id, tur_adi, renk_kodu, kurallar_json, durum FROM qms_departman_turleri")
        ed = st.data_editor(df, width="stretch", hide_index=True, num_rows="dynamic", key="ed_dept_types", column_config={"kurallar_json": st.column_config.TextColumn("📜 Kurallar (JSON)")})
        if st.button("💾 Tür Değişikliklerini Kaydet"):
            try:
                with engine.begin() as conn:
                    for _, r in ed.iterrows():
                        k = r['kurallar_json'] if pd.notna(r['kurallar_json']) else None
                        if pd.isna(r['id']): conn.execute(text("INSERT INTO qms_departman_turleri (tur_adi, renk_kodu, kurallar_json, durum) VALUES (:n, :c, :k, :s)"), {"n": r['tur_adi'], "c": r['renk_kodu'], "k": k, "s": r['durum']})
                        else: conn.execute(text("UPDATE qms_departman_turleri SET tur_adi=:n, renk_kodu=:c, kurallar_json=:k, durum=:s WHERE id=:id"), {"n": r['tur_adi'], "c": r['renk_kodu'], "k": k, "s": r['durum'], "id": r['id']})
                st.toast("✅ Güncellendi!"); st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

def _org_render_add_form(engine):
    """Yeni departman ekleme formu."""
    with st.expander("➕ Yeni Bölüm / Departman Tanımla"):
        opts = get_qms_department_options_hierarchical()
        tdf = run_query("SELECT id, tur_adi FROM qms_departman_turleri")
        tmap = {r['id']: r['tur_adi'] for _, r in tdf.iterrows()}
        pdf = run_query("SELECT id, ad_soyad FROM ayarlar_kullanicilar WHERE durum IN ('AKTİF', 'AKTIF') ORDER BY ad_soyad")
        pmap = {0: "- Atanmamış -", **{r['id']: r['ad_soyad'] for _, r in pdf.iterrows()}}
        with st.form("new_dept_form"):
            c1, c2 = st.columns(2)
            with c1:
                ad = st.text_input("🏠 Bölüm Adı"); ust = st.selectbox("📂 Üst Birim", options=list(opts.keys()), format_func=lambda x: opts.get(x), index=0)
                kod = st.text_input("🆔 Kod", value=bolum_kodu_uret(engine, ust))
            with c2:
                tur = st.selectbox("🏷️ Tür", options=list(tmap.keys()), format_func=lambda x: tmap.get(x), index=0)
                mngr = st.selectbox("👤 Sorumlu", options=list(pmap.keys()), format_func=lambda x: pmap.get(x), index=0)
                sira = st.number_input("🔢 Sıra", min_value=0, value=100)
            if st.form_submit_button("Kaydet", width="stretch", type="primary") and ad:
                ok, msg = hiyerarşi_kural_dogrula(engine, tur, ust)
                if not ok: st.error(msg); return
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO qms_departmanlar (ad, kod, ust_id, tur_id, yonetici_id, sira_no, durum) VALUES (:ad, :kod, :u, :t, :y, :s, 'AKTİF')"), {"ad": str(ad).upper(), "kod": kod, "u": ust if ust > 0 else None, "t": tur, "y": mngr if mngr > 0 else None, "s": sira})
                    clear_department_cache(); st.toast("✅ Eklendi!"); st.rerun()
                except Exception as e: st.error(f"❌ Hata: {e}")

def _org_process_matrix_save(engine, ed_df, d_df, m_t, m_d, m_p):
    """Matrix kayıt işlemlerini ve zırhlı kontrolleri yönetir."""
    try:
        with engine.begin() as conn:
            for idx, r in ed_df.iterrows():
                old = d_df.iloc[idx]; u_id = m_d.get(str(r.get('ust_ad','')).strip()); iu_id = m_d.get(str(r.get('ikincil_ust_ad','')).strip()); t_id = m_t.get(str(r.get('tur_ad', '')).strip()); y_id = m_p.get(str(r.get('yonetici_adi', '')).strip())
                if u_id == r['id']: st.warning(f"⚠️ {r['ad']} kendi üstü olamaz."); continue
                ok, msg = hiyerarşi_kural_dogrula(engine, t_id, u_id)
                if not ok: st.error(f"{r['ad']}: {msg}"); continue
                if t_id != old['tur_id']: miras_tip_guncelle(engine, r['id'], t_id)
                if r['durum'] == 'PASİF' and old['durum'] == 'AKTİF':
                    ok2, msg2 = pasife_al_ve_aktar(engine, r['id'])
                    if not ok2: st.error(msg2); continue
                conn.execute(text("UPDATE qms_departmanlar SET ad=:ad, kod=:kod, ust_id=:u, ikincil_ust_id=:iu, tur_id=:t, yonetici_id=:y, dil_anahtari=:l, sira_no=:s, durum=:s_durum, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id"), {"ad": str(r['ad']).upper(), "kod": r['kod'], "u": u_id if u_id and u_id > 0 else None, "iu": iu_id if iu_id and iu_id > 0 else None, "t": t_id, "y": y_id if y_id and y_id > 0 else None, "l": r['dil_anahtari'], "s": r['sira_no'], "s_durum": r['durum'], "id": r['id']})
        clear_department_cache(); st.success("✅ Güncellendi!"); st.rerun()
    except Exception as e: st.error(f"❌ Hata: {e}")

def _org_render_edit_matrix(engine):
    """Mevcut departmanları düzenleyen matrix editörü."""
    st.markdown("### 📝 Mevcut Departman & Matrix Düzenle")
    dept_df = run_query("SELECT id, ad, ust_id, ikincil_ust_id, tur_id, yonetici_id, kod, dil_anahtari, sira_no, durum FROM qms_departmanlar ORDER BY sira_no")
    t_df = run_query("SELECT id, tur_adi FROM qms_departman_turleri"); t_map = dict(zip(t_df['id'], t_df['tur_adi']))
    d_opts = get_qms_department_options_hierarchical()
    p_df = run_query("SELECT id, ad_soyad FROM ayarlar_kullanicilar WHERE durum IN ('AKTİF', 'AKTIF') ORDER BY ad_soyad")
    p_map = {0: "- Atanmamış -", **{r['id']: r['ad_soyad'] for _, r in p_df.iterrows()}}
    
    dept_df['ust_ad'] = dept_df['ust_id'].fillna(0).astype(int).map(d_opts).fillna("- Kök -")
    dept_df['ikincil_ust_ad'] = dept_df['ikincil_ust_id'].fillna(0).astype(int).map(d_opts).fillna("- Yok -")
    dept_df['tur_ad'] = dept_df['tur_id'].fillna(0).astype(int).map(t_map).fillna("-")
    dept_df['yonetici_adi'] = dept_df['yonetici_id'].fillna(0).astype(int).map(p_map).fillna("-")

    ed = st.data_editor(dept_df, width="stretch", hide_index=True, column_config={"id": None, "ust_id": None, "tur_id": None, "ikincil_ust_id": None, "yonetici_id": None, "ad": st.column_config.TextColumn("🏠 Birim Adı", width="large", required=True), "kod": st.column_config.TextColumn("🆔 Kod", width="small"), "ust_ad": st.column_config.SelectboxColumn("📂 Üst", options=list(d_opts.values())), "ikincil_ust_ad": st.column_config.SelectboxColumn("🔗 Matrix", options=list(d_opts.values())), "tur_ad": st.column_config.SelectboxColumn("🏷️ Tür", options=list(t_map.values())), "yonetici_adi": st.column_config.SelectboxColumn("👤 Sorumlu", options=list(p_map.values())), "dil_anahtari": st.column_config.TextColumn("🌐 Dil Key"), "sira_no": st.column_config.NumberColumn("🔢 Sıra", min_value=0), "durum": st.column_config.SelectboxColumn("🚦 Durum", options=["AKTİF", "PASİF"])})
    if st.button("💾 Matrix Değişikliklerini Kaydet", width="stretch", type="primary"):
        m_d = {v: k for k, v in d_opts.items()}; m_t = {v: k for k, v in t_map.items()}; m_p = {v: k for k, v in p_map.items()}
        _org_process_matrix_save(engine, ed, dept_df, m_t, m_d, m_p)

def render_bolum_tab(engine):
    """QMS Departman Hiyerarşisi & Matrix Yönetimi Orkestratörü."""
    st.subheader("🏭 QMS Departman Hiyerarşisi & Matrix Yönetimi")
    st.info("BRC/IFS Standartları: 20 katman derinlik ve Matrix desteği aktiftir.")
    _org_render_visuals()
    _org_render_types_editor(engine)
    st.divider()
    _org_render_add_form(engine)
    _org_render_edit_matrix(engine)
    render_sync_button(key_prefix="bolumler_ui")
