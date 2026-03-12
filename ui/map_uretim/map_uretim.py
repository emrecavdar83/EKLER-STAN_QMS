import streamlit as st
import pandas as pd
from datetime import datetime
import pytz, time

from database.connection import get_engine
from . import map_db as db
from . import map_hesap as hesap
from logic.auth_logic import kullanici_yetkisi_var_mi

# ─── Config (Anayasa: Zero Hardcode) ─────────────────────────────────────────
MAP_MAKINA_LISTESI = ["MAP-01", "MAP-02", "MAP-03"]
MAP_DURUS_NEDENLERI = [
    "Arıza / Bakım", "Film Değişimi", "Mola (Çay)",
    "Öğlen Molası", "Ürün Bekleme", "Setup / Ayar",
    "Temizlik / Sanitasyon", "Diğer",
]
MAP_FIRE_TIPLERI = [
    "Bobin Başı Fire", "Bobin Sonu Fire", "Film Değişimi Fire",
    "Sızdırmazlık / Kaçak", "Yırtık / Delik Film", "Gaz Hatası",
    "Besleme Hatası", "Operatör Hatası", "Diğer",
]
_TZ = pytz.timezone("Europe/Istanbul")


# ─── Session State Bootstrap ──────────────────────────────────────────────────
def _init_state():
    defaults = {
        "map_aktif_vardiya_id": None,
        "map_canli_mod": True,
        "map_son_durum": "CALISIYOR",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Tab 1 — Vardiya ──────────────────────────────────────────────────────────
def _tab_vardiya(engine):
    aktif = db.get_aktif_vardiya(engine)

    if aktif is None:
        st.info("📋 Bugün açık vardiya yok. Yeni vardiya başlatın.")
        with st.form("yeni_vardiya_form"):
            c1, c2 = st.columns(2)
            makina = c1.selectbox("🏭 Makina", MAP_MAKINA_LISTESI)
            vno = c2.selectbox("⏰ Vardiya No", [1, 2, 3])
            op = st.text_input("👷 Operatör Adı (Soyadı)")
            sef = st.text_input("👔 Vardiya Şefi (boş bırakılabilir)")
            c3, c4, c5 = st.columns(3)
            bes = c3.number_input("Besleme Kişi", 0, 20, 4)
            kas = c4.number_input("Kasalama Kişi", 0, 20, 1)
            hiz = c5.number_input("🎯 Hedef Hız (pk/dk)", 0.1, 20.0, 4.2, step=0.1)
            if st.form_submit_button("🟢 VARDİYAYI BAŞLAT", use_container_width=True, type="primary"):
                if not op.strip():
                    st.error("Operatör adı zorunludur!")
                    return
                try:
                    vid = db.aç_vardiya(engine, makina, vno, op.strip(), sef.strip(),
                                        int(bes), int(kas), float(hiz))
                    db.insert_zaman_kaydi(engine, vid, "CALISIYOR")
                    st.session_state.map_aktif_vardiya_id = vid
                    st.success(f"✅ Vardiya açıldı! ID: {vid}")
                    time.sleep(0.5)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.session_state.map_aktif_vardiya_id = int(aktif['id'])
        bas = aktif['baslangic_saati']
        st.success(f"✅ **{aktif['makina_no']}** | {aktif['vardiya_no']}. Vardiya | Başlangıç: **{bas}**")
        st.caption(f"👷 Operatör: **{aktif['operator_adi']}**")

        # Canlı Sayaç
        placeholder = st.empty()
        simdi = datetime.now(_TZ)
        try:
            bas_dt = datetime.strptime(f"{aktif['tarih']} {bas}:00", "%Y-%m-%d %H:%M:%S")
        except Exception:
            bas_dt = simdi.replace(tzinfo=None)
        
        simdi_naive = simdi.replace(tzinfo=None)
        gecen = simdi_naive - bas_dt
        h, rem = divmod(int(gecen.total_seconds()), 3600)
        m, s2 = divmod(rem, 60)
        placeholder.metric("⏱️ Geçen Süre", f"{h:02d}:{m:02d}:{s2:02d}")

        uretim = st.number_input("📦 Gerçekleşen Üretim (paket)", 0, 100000, int(aktif['gerceklesen_uretim']))
        notlar = st.text_area("📝 Vardiya Notu", value=aktif.get('notlar', '') or "")
        if st.button("🔴 VARDİYAYI KAPAT", use_container_width=True, type="primary"):
            db.kapat_vardiya(engine, int(aktif['id']), int(uretim))
            st.session_state.map_aktif_vardiya_id = None
            st.success("Vardiya kapatıldı!")
            time.sleep(0.5)
            st.rerun()


# ─── Tab 2 — Zaman Çizelgesi ─────────────────────────────────────────────────
def _tab_zaman(engine, vardiya_id):
    mod = "CANLI" if st.session_state.map_canli_mod else "MANUEL"
    col_a, col_b = st.columns(2)
    if col_a.button("⚡ CANLI MOD", type="primary" if mod == "CANLI" else "secondary"):
        st.session_state.map_canli_mod = True; st.rerun()
    if col_b.button("✏️ MANUEL MOD", type="primary" if mod == "MANUEL" else "secondary"):
        st.session_state.map_canli_mod = False; st.rerun()
    st.divider()

    if st.session_state.map_canli_mod:
        _canli_mod(engine, vardiya_id)
    else:
        _manuel_mod(engine, vardiya_id)

    st.divider()
    _zaman_tablosu(engine, vardiya_id)


def _canli_mod(engine, vardiya_id):
    son = db.get_son_zaman_kaydi(engine, vardiya_id)
    durum = son['durum'] if son else "CALISIYOR"

    if durum == "CALISIYOR":
        bas_ts = son['baslangic_ts'] if son else "-"
        st.success(f"🟢 **ÇALIŞIYOR** — {bas_ts[:16]} 'den beri")
        if st.button("⏸️ DURDUR", use_container_width=True):
            st.session_state.map_son_durum = "DURUS"
            st.rerun()
    else:
        neden = son.get('neden', '') if son else ''
        bas_ts = son['baslangic_ts'][:16] if son else "-"
        st.error(f"🔴 **DURDU** — {neden} ({bas_ts}'den beri)")
        if st.button("▶️ BAŞLAT", use_container_width=True, type="primary"):
            db.insert_zaman_kaydi(engine, vardiya_id, "CALISIYOR")
            st.session_state.map_son_durum = "CALISIYOR"
            st.rerun()

    # Neden seçim butonu (sadece DURUS geçişinde)
    if st.session_state.get("map_son_durum") == "DURUS" and durum == "CALISIYOR":
        st.caption("📋 Duruş nedeni seçin:")
        cols = st.columns(3)
        for i, ned in enumerate(MAP_DURUS_NEDENLERI):
            if cols[i % 3].button(ned, key=f"ned_{i}"):
                db.insert_zaman_kaydi(engine, vardiya_id, "DURUS", neden=ned)
                st.session_state.map_son_durum = "DURUS"
                st.rerun()


def _manuel_mod(engine, vardiya_id):
    tarih = datetime.now(_TZ).strftime("%Y-%m-%d")
    with st.form("manuel_zaman_form"):
        c1, c2 = st.columns(2)
        bas = c1.text_input("⏰ Başlangıç (SS:DD)", placeholder="08:30")
        bit = c2.text_input("⏰ Bitiş (SS:DD)", placeholder="08:45")
        durum = st.selectbox("Durum", ["CALISIYOR", "DURUS"])
        neden = st.selectbox("Neden", MAP_DURUS_NEDENLERI) if durum == "DURUS" else None
        acl = st.text_input("Açıklama")
        if st.form_submit_button("➕ EKLE", use_container_width=True):
            try:
                db.manuel_zaman_ekle(engine, vardiya_id, bas, bit, durum,
                                     neden, acl, tarih)
                st.success("Eklendi!"); st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")


def _zaman_tablosu(engine, vardiya_id):
    df = db.get_zaman_cizelgesi(engine, vardiya_id)
    if df.empty:
        st.info("Henüz kayıt yok."); return
    st.write("**📋 Zaman Çizelgesi**")

    def _renk(row):
        renk = "background-color: #d4edda" if row['durum'] == "CALISIYOR" else "background-color: #f8d7da"
        return [renk] * len(row)

    st.dataframe(df.style.apply(_renk, axis=1), use_container_width=True, hide_index=True)
    if st.button("🗑️ Son Kaydı Sil (Hata Düzeltme)"):
        db.sil_son_zaman_kaydi(engine, vardiya_id)
        st.rerun()


# ─── Tab 3 — Bobin ───────────────────────────────────────────────────────────
def _tab_bobin(engine, vardiya_id):
    st.subheader("🎞️ Bobin Değişim Kaydı")
    if st.button("⚡ ŞİMDİ BOBİN DEĞİŞTİRDİM", use_container_width=True, type="primary"):
        st.session_state["map_bobin_form"] = True

    if st.session_state.get("map_bobin_form"):
        with st.form("bobin_form"):
            lot = st.text_input("📦 LOT / Seri No", placeholder="PP-2603-002")
            c1, c2 = st.columns(2)
            bitis_m = c1.number_input("Kalan Metre (eski bobin)", 0.0, 1000.0, 0.0)
            bas_m = c2.number_input("Yeni Bobin Başlangıç (m)", 0.0, 1000.0, 300.0)
            acl = st.text_input("Açıklama")
            if st.form_submit_button("💾 KAYDET"):
                db.insert_bobin(engine, vardiya_id, lot, bitis_m or None, acl, bas_m)
                st.session_state["map_bobin_form"] = False
                st.success("Bobin kaydedildi!"); st.rerun()

    df = db.get_bobinler(engine, vardiya_id)
    if not df.empty:
        st.dataframe(df[['sira_no', 'degisim_ts', 'bobin_lot', 'baslangic_m',
                          'bitis_m', 'kullanilan_m', 'aciklama']],
                     use_container_width=True, hide_index=True)


# ─── Tab 4 — Fire ─────────────────────────────────────────────────────────────
def _tab_fire(engine, vardiya_id):
    st.subheader("🔥 Fire Kaydı")
    fire_df = db.get_fire_kayitlari(engine, vardiya_id)
    toplam = int(fire_df['miktar_adet'].sum()) if not fire_df.empty else 0
    st.metric("🔥 Vardiya Toplam Fire", f"{toplam} adet")
    st.divider()

    st.caption("🔖 Fire Tipi Seçin:")
    secilen_tip = st.session_state.get("map_fire_tip")
    cols = st.columns(3)
    for i, tip in enumerate(MAP_FIRE_TIPLERI):
        style = "primary" if secilen_tip == tip else "secondary"
        if cols[i % 3].button(tip, key=f"ft_{i}", type=style):
            st.session_state["map_fire_tip"] = tip
            st.rerun()

    if secilen_tip:
        with st.form("fire_form"):
            st.info(f"Seçilen: **{secilen_tip}**")
            bobinler = db.get_bobinler(engine, vardiya_id)
            bob_opts = ["-"] + [f"{r['sira_no']}. Bobin ({r['bobin_lot']})"
                                 for _, r in bobinler.iterrows()] if not bobinler.empty else ["-"]
            bref = st.selectbox("Bobin Referansı", bob_opts)
            miktar = st.number_input("Miktar (adet)", 0, 10000, 0)
            acl = st.text_input("Açıklama")
            if st.form_submit_button("💾 KAYDET", use_container_width=True):
                if miktar > 0:
                    db.insert_fire(engine, vardiya_id, secilen_tip, int(miktar),
                                   bref if bref != "-" else None, acl)
                    st.session_state["map_fire_tip"] = None
                    st.success("Fire kaydedildi!"); st.rerun()
                else:
                    st.warning("Miktar 0 olamaz.")

    if not fire_df.empty:
        st.dataframe(fire_df[['fire_tipi', 'miktar_adet', 'bobin_ref', 'aciklama']],
                     use_container_width=True, hide_index=True)


# ─── Tab 5 — Rapor ───────────────────────────────────────────────────────────
def _tab_rapor(engine, vardiya_id):
    st.subheader("📊 Vardiya Özet Raporu")
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id)
    uretim = hesap.hesapla_uretim(engine, vardiya_id)
    if not ozet:
        st.warning("Yeterli veri yok."); return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🟢 Çalışma", f"{ozet['toplam_calisma_dk']:.0f} dk",
              f"%{ozet['kullanilabilirlik_pct']}")
    c2.metric("🔴 Duruş", f"{ozet['toplam_durus_dk']:.0f} dk")
    c3.metric("📦 Üretim", f"{uretim.get('gerceklesen_uretim', 0)} pk",
              f"Hedef: {uretim.get('teorik_uretim', 0)}")
    c4.metric("🔥 Fire %", f"%{uretim.get('fire_pct', 0)}")

    st.divider()
    durus_oz = hesap.hesapla_durus_ozeti(engine, vardiya_id)
    if durus_oz:
        st.write("**⏱️ Duruş Analizi (Neden Bazında)**")
        st.dataframe(pd.DataFrame(durus_oz), use_container_width=True, hide_index=True)

    fire_oz = hesap.hesapla_fire_ozeti(engine, vardiya_id)
    if fire_oz:
        st.write("**🔥 Fire Analizi (Tip Bazında)**")
        st.dataframe(pd.DataFrame(fire_oz), use_container_width=True, hide_index=True)

    st.divider()
    try:
        from ui.map_uretim.map_rapor_pdf import uret_is_raporu
        import tempfile, os
        if st.button("📄 PDF RAPORU OLUŞTUR", use_container_width=True, type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                fpath = uret_is_raporu(engine, vardiya_id, tmp.name)
            with open(fpath, "rb") as f:
                st.download_button("⬇️ PDF İndir", f, file_name=f"MAP_Rapor_{vardiya_id}.pdf",
                                   mime="application/pdf")
            try:
                os.unlink(fpath)
            except Exception:
                pass
    except ImportError:
        st.info("ℹ️ PDF modülü (reportlab) henüz yüklü değil. `pip install reportlab` ile yükleyebilirsiniz.")


# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def render_map_module(engine=None):
    """MAP üretim takip modülünü render eder."""
    try:
        if not kullanici_yetkisi_var_mi("📦 MAP Üretim", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz yok."); st.stop()

        if engine is None:
            engine = get_engine()

        _init_state()
        st.title("📦 MAP Makinası Üretim Takip")
        st.caption("Anlık çalışma/duruş, bobin ve fire kayıtları | EKL-URT-F-MAP-001")

        tab_vrd, tab_zaman, tab_bob, tab_fire, tab_rpr = st.tabs([
            "🟢 Vardiya", "⏱️ Zaman", "🎞️ Bobin", "🔥 Fire", "📊 Rapor"
        ])

        aktif = db.get_aktif_vardiya(engine)
        vardiya_id = int(aktif['id']) if aktif else st.session_state.get("map_aktif_vardiya_id")

        with tab_vrd:
            _tab_vardiya(engine)

        for tab, fn in [(tab_zaman, _tab_zaman), (tab_bob, _tab_bobin),
                        (tab_fire, _tab_fire), (tab_rpr, _tab_rapor)]:
            with tab:
                if not vardiya_id:
                    st.warning("⚠️ Önce Tab 1'den aktif bir vardiya başlatın.")
                else:
                    fn(engine, int(vardiya_id))
    except Exception as e:
        st.error(f"🚨 **MODÜL HATASI (Teşhis Modu):** {str(e)}")
        if "ProgrammingError" in str(type(e)):
            st.warning("ℹ️ Bu genellikle tablo veya sütun eksikliğinden kaynaklanır. Sayfayı yenileyerek migration'ın tamamlanmasını bekleyin.")
        st.exception(e)
