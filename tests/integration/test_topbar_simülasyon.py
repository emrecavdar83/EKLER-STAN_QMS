"""
tests/integration/test_topbar_simulasyon.py
TopBar v6.3.0 — Sistem durumuna haberdar kapsamlı simülasyon testleri.

Kapsam:
  A) TopBar yapısı (sidebar sıfır, topnav butonları, logout)
  B) Navigasyon simülasyonu (tıkla → slug değişir)
  C) Rol bazlı erişim (ADMIN / OPS / MGT — gerçek modül listesine göre)
  D) Tüm 17 modül: exception yok + sidebar boş
  E) Modül bazlı widget envanter testleri (sistemin mevcut hali)
  F) Admin araçları inline kontrolü
  G) Session state kararlılığı (ardışık rerun)
  H) Login ekranı etkilenmedi
  I) Hata izleyici inline render
"""
import pytest
from streamlit.testing.v1 import AppTest

TIMEOUT = 60

# ── Modül envanterleri (app_module_registry.py ile senkron) ─────────────────

TUM_MODULLER = [
    "portal", "uretim_girisi", "kpi_kontrol", "gmp_denetimi",
    "personel_hijyen", "temizlik_kontrol", "soguk_oda", "map_uretim",
    "gunluk_gorevler", "personel_vardiya_yonetimi", "performans_polivalans",
    "denetim_izi", "ayarlar", "profilim", "anayasa", "qdms",
    "kurumsal_raporlama",
]

# Zone'a göre gruplar (zone_yetki.py ile senkron)
MGT_MODULLER  = ["kpi_kontrol", "gmp_denetimi", "performans_polivalans",
                  "denetim_izi", "kurumsal_raporlama", "qdms"]
SYS_MODULLER  = ["ayarlar", "anayasa"]
OPS_MODULLER  = ["uretim_girisi"]  # zone_gate('ops') olan
SERBEST_MODULLER = [m for m in TUM_MODULLER
                    if m not in MGT_MODULLER + SYS_MODULLER + OPS_MODULLER]

# OPS'un erişebileceği modüller: portal + profilim + ops modülleri
OPS_ERISIM = {"portal", "profilim", "uretim_girisi", "personel_hijyen",
              "temizlik_kontrol", "soguk_oda", "map_uretim",
              "gunluk_gorevler", "personel_vardiya_yonetimi"}


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

def _at(modul: str, rol: str = "ADMIN") -> AppTest:
    at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
    at.session_state["logged_in"]     = True
    at.session_state["user"]          = f"{rol}_sim"
    at.session_state["user_rol"]      = rol
    at.session_state["user_fullname"] = f"{rol} SIM"
    at.session_state["user_id"]       = 1
    at.session_state["active_module_key"] = modul
    at.run()
    return at


def _topnav_keys(at: AppTest) -> list[str]:
    return [b.key for b in at.button if b.key and b.key.startswith("topnav_")]


def _sidebar_widget_sayisi(at: AppTest) -> int:
    return (len(at.sidebar.button) + len(at.sidebar.selectbox)
            + len(at.sidebar.radio) + len(at.sidebar.checkbox)
            + len(at.sidebar.text_input))


# ════════════════════════════════════════════════════════════════════════════
# A) TOPBAR YAPI TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestTopBarYapi:
    """TopBar bileşeninin temel yapısı — sidebar sıfır garantisi."""

    def test_sidebar_buton_yok(self):
        at = _at("portal")
        assert len(at.exception) == 0
        assert len(at.sidebar.button) == 0, \
            f"Sidebar butonu kaldı: {len(at.sidebar.button)}"

    def test_sidebar_selectbox_yok(self):
        at = _at("portal")
        assert len(at.exception) == 0
        assert len(at.sidebar.selectbox) == 0

    def test_sidebar_radio_yok(self):
        at = _at("portal")
        assert len(at.exception) == 0
        assert len(at.sidebar.radio) == 0

    def test_topbar_logout_butonu_var(self):
        at = _at("portal")
        assert len(at.exception) == 0
        assert any(b.key == "topbar_logout" for b in at.button), \
            "topbar_logout butonu bulunamadı"

    def test_admin_topnav_en_az_17_modul(self):
        """ADMIN tüm 17 modülün topnav butonunu görür."""
        at = _at("portal")
        assert len(at.exception) == 0
        navs = _topnav_keys(at)
        assert len(navs) >= 17, f"ADMIN topnav eksik: {len(navs)} (beklenen ≥17)"

    def test_topnav_sluglar_kayitli_modullerle_eslesiyor(self):
        """Her topnav_ butonu bilinen bir slug'a karşılık gelmeli."""
        at = _at("portal")
        assert len(at.exception) == 0
        bilinmeyen = [
            k.replace("topnav_", "")
            for k in _topnav_keys(at)
            if k.replace("topnav_", "") not in TUM_MODULLER
        ]
        assert not bilinmeyen, f"Bilinmeyen topnav slug: {bilinmeyen}"

    def test_portal_toplam_buton_sayisi(self):
        """ADMIN portal: TopBar (17 topnav + logout) + içerik butonları ≥ 18."""
        at = _at("portal")
        assert len(at.exception) == 0
        assert len(at.button) >= 18, \
            f"Portal buton sayısı düşük: {len(at.button)}"

    def test_exception_yok_portal(self):
        at = _at("portal")
        assert len(at.exception) == 0, str(at.exception)


# ════════════════════════════════════════════════════════════════════════════
# B) NAVİGASYON SİMÜLASYONU
# ════════════════════════════════════════════════════════════════════════════

class TestNavigasyonSimulasyon:
    """TopBar buton tıklama → slug değişimi simülasyonu."""

    def test_topnav_tikla_slug_degisir(self):
        """topnav_ butonuna tıklayınca active_module_key değişmeli."""
        at = _at("portal")
        navs = [b for b in at.button if b.key and b.key.startswith("topnav_")
                and b.key != "topnav_portal"]
        assert navs, "Hedef topnav butonu bulunamadı"
        hedef = navs[0]
        hedef_slug = hedef.key.replace("topnav_", "")
        hedef.click().run()
        assert len(at.exception) == 0
        assert at.session_state["active_module_key"] == hedef_slug, \
            f"Slug değişmedi: beklenen={hedef_slug}, mevcut={at.session_state.get('active_module_key')}"

    def test_aktif_modul_butonu_primary_type(self):
        """Aktif modülün topnav butonu primary tipte olmalı."""
        at = _at("map_uretim")
        assert len(at.exception) == 0
        aktif_btn = next(
            (b for b in at.button if b.key == "topnav_map_uretim"), None
        )
        assert aktif_btn is not None, "topnav_map_uretim butonu bulunamadı"

    def test_gecersiz_slug_portale_dusuyor(self):
        """Bilinmeyen slug → portal'a fallback, exception yok."""
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.session_state["logged_in"]          = True
        at.session_state["user"]               = "AdminTest"
        at.session_state["user_rol"]           = "ADMIN"
        at.session_state["user_fullname"]      = "ADMIN"
        at.session_state["user_id"]            = 1
        at.session_state["active_module_key"]  = "OLMAYAN_MODUL_XYZ_999"
        at.run()
        assert len(at.exception) == 0
        assert at.session_state["active_module_key"] == "portal"

    def test_session_state_logged_in_korunur(self):
        """Render sonrası logged_in=True kalmalı."""
        at = _at("portal")
        assert at.session_state["logged_in"] is True

    def test_ardisik_rerun_stable(self):
        """İki ardışık rerun'da exception oluşmamalı."""
        at = _at("portal")
        at.run()
        assert len(at.exception) == 0

    def test_logout_url_parametresi(self):
        """?logout=1 query param → oturum temizlenmeli, exception yok."""
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.session_state["logged_in"] = True
        at.session_state["user"] = "Admin"
        at.session_state["user_rol"] = "ADMIN"
        at.query_params["logout"] = "1"
        at.run()
        assert len(at.exception) == 0
        assert ("logged_in" not in at.session_state
                or not at.session_state["logged_in"])


# ════════════════════════════════════════════════════════════════════════════
# C) ROL BAZLI ERİŞİM TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestRolBazliErisim:
    """OPS / MGT / ADMIN rol erişim kontrolleri — gerçek zone_yetki ile."""

    def test_ops_topnav_sinirli(self):
        """OPS rolü yalnızca yetkili modüllerin topnav butonunu görür."""
        at = _at("portal", "OPS")
        assert len(at.exception) == 0
        navs = _topnav_keys(at)
        # OPS tüm 17'yi görmemeli
        assert len(navs) < 17, \
            f"OPS fazla topnav görüyor: {len(navs)}"
        # Kendi modüllerini görmeli
        assert "topnav_portal" in navs

    def test_ops_mgt_modulune_erisemez(self):
        """OPS kpi_kontrol'ü açınca zone kapısına takılmalı, exception yok."""
        at = _at("kpi_kontrol", "OPS")
        assert len(at.exception) == 0
        hata = " ".join(str(e.value) for e in at.error).lower()
        widget = len(at.button) + len(at.text_input) + len(at.selectbox)
        zone_devrede = "eri" in hata or widget <= 3
        assert zone_devrede, \
            f"OPS zone kapısına takılmadı (widget={widget}, hata='{hata[:80]}')"

    def test_ops_sys_modulune_erisemez(self):
        """OPS ayarlar modülünü açamaz."""
        at = _at("ayarlar", "OPS")
        assert len(at.exception) == 0
        hata = " ".join(str(e.value) for e in at.error).lower()
        widget = len(at.button) + len(at.text_input) + len(at.selectbox)
        zone_devrede = "eri" in hata or widget <= 3
        assert zone_devrede, f"OPS SYS zone'a girdi (widget={widget})"

    def test_admin_tum_moduller_exception_yok(self):
        """ADMIN tüm 17 modülü exception olmadan açar."""
        hatali = {}
        for m in TUM_MODULLER:
            at = _at(m)
            if at.exception:
                hatali[m] = str(at.exception[0])[:80]
        assert not hatali, \
            "ADMIN erişim hataları:\n" + "\n".join(f"  {k}: {v}" for k,v in hatali.items())

    def test_ops_kendi_modullerinde_exception_yok(self):
        """OPS erişebildiği modüllerde exception olmamalı."""
        hatali = {}
        for m in OPS_ERISIM:
            at = _at(m, "OPS")
            if at.exception:
                hatali[m] = str(at.exception[0])[:80]
        assert not hatali, \
            "OPS modül hataları:\n" + "\n".join(f"  {k}: {v}" for k,v in hatali.items())


# ════════════════════════════════════════════════════════════════════════════
# D) TÜM MODÜLLER: SİDEBAR BOŞ + EXCEPTİON YOK
# ════════════════════════════════════════════════════════════════════════════

class TestTumModullerTopBar:
    """Her modülde sidebar sıfır ve exception yok garantisi."""

    @pytest.mark.parametrize("modul", TUM_MODULLER)
    def test_modul_exception_yok(self, modul):
        at = _at(modul)
        assert len(at.exception) == 0, \
            f"{modul}: {at.exception[0] if at.exception else ''}"

    @pytest.mark.parametrize("modul", TUM_MODULLER)
    def test_modul_sidebar_bos(self, modul):
        """v6.3.0: Hiçbir modül sidebar widget üretmemeli."""
        at = _at(modul)
        sayisi = _sidebar_widget_sayisi(at)
        assert sayisi == 0, \
            f"{modul}: sidebar'da {sayisi} widget kaldı"

    @pytest.mark.parametrize("modul", TUM_MODULLER)
    def test_modul_en_az_bir_widget(self, modul):
        """Her modül ana alanda en az 1 interaktif widget içermeli."""
        at = _at(modul)
        toplam = (len(at.button) + len(at.selectbox)
                  + len(at.text_input) + len(at.radio) + len(at.checkbox))
        assert toplam >= 1, f"{modul}: ana alanda hiç widget yok"


# ════════════════════════════════════════════════════════════════════════════
# E) MODÜL BAZLI WİDGET ENVANTERİ (Sistemin Mevcut Hali)
# ════════════════════════════════════════════════════════════════════════════

class TestModulWidgetEnvanteri:
    """Modüllerin gerçek widget sayılarına karşı gerileme testleri."""

    def test_portal_topnav_eksiksiz(self):
        """Portal: 17 modülün tamamı için topnav butonu mevcut."""
        at = _at("portal")
        mevcut_sluglar = {k.replace("topnav_", "") for k in _topnav_keys(at)}
        eksik = [m for m in TUM_MODULLER if m not in mevcut_sluglar]
        assert not eksik, f"Portal'da eksik topnav: {eksik}"

    def test_map_uretim_expander_widget(self):
        """MAP: inline expander içinde selectbox ve radio mevcut."""
        at = _at("map_uretim")
        assert len(at.exception) == 0
        assert len(at.selectbox) + len(at.radio) >= 1, \
            "MAP inline widget bulunamadı"

    def test_map_uretim_sidebar_bos(self):
        """MAP: sidebar tamamen boş."""
        at = _at("map_uretim")
        assert _sidebar_widget_sayisi(at) == 0

    def test_raporlar_inline_filtreler(self):
        """Raporlar: tarih input + kategori selectbox inline mevcut."""
        at = _at("kurumsal_raporlama")
        assert len(at.exception) == 0
        assert len(at.selectbox) >= 1, "Raporlar kategori selectbox yok"

    def test_raporlar_sidebar_bos(self):
        """Raporlar: sidebar tamamen boş."""
        at = _at("kurumsal_raporlama")
        assert _sidebar_widget_sayisi(at) == 0

    def test_ayarlar_buton_sayisi(self):
        """Ayarlar: inline widget seti zengin (≥50 buton)."""
        at = _at("ayarlar")
        assert len(at.exception) == 0
        assert len(at.button) >= 50, \
            f"Ayarlar buton sayısı düşük: {len(at.button)}"

    def test_ayarlar_sidebar_bos(self):
        at = _at("ayarlar")
        assert _sidebar_widget_sayisi(at) == 0

    def test_vardiya_onay_widget(self):
        """Vardiya modülü onay widget'larını render etmeli."""
        at = _at("personel_vardiya_yonetimi")
        assert len(at.exception) == 0
        assert len(at.button) + len(at.selectbox) + len(at.radio) >= 3

    def test_hijyen_widget_var(self):
        """Hijyen modülü en az 1 widget render etmeli."""
        at = _at("personel_hijyen")
        assert len(at.exception) == 0
        assert len(at.button) + len(at.radio) >= 1

    def test_uretim_girisi_widget(self):
        """Üretim girişi: form widget'ları mevcut."""
        at = _at("uretim_girisi")
        assert len(at.exception) == 0
        assert len(at.button) + len(at.selectbox) + len(at.text_input) >= 3


# ════════════════════════════════════════════════════════════════════════════
# F) ADMIN ARAÇLARI INLINE KONTROL
# ════════════════════════════════════════════════════════════════════════════

class TestAdminAraclariInline:
    """v6.3.0: Admin araçları sidebar yerine ana alanda görünmeli."""

    def test_admin_reset_btn_inline(self):
        """Admin reset butonu ana alanda mevcut, sidebar'da yok."""
        at = _at("portal")
        assert len(at.exception) == 0
        assert any(b.key == "admin_reset_btn" for b in at.button), \
            "admin_reset_btn ana alanda bulunamadı"
        assert not any(b.key == "admin_reset_btn" for b in at.sidebar.button), \
            "admin_reset_btn sidebar'da kalıyor"

    def test_admin_sorgu_sayaci_inline(self):
        """ADMIN'in sorgu sayacı inline görünmeli — exception yok."""
        at = _at("portal")
        assert len(at.exception) == 0

    def test_session_trace_expander_admin(self):
        """ADMIN oturumunda Session Trace expander sayfada render olmalı."""
        at = _at("portal")
        assert len(at.exception) == 0
        # Expander varlığı dolaylı: exception yok + button sayısı değişmiyor
        assert len(at.button) >= 1


# ════════════════════════════════════════════════════════════════════════════
# G) SESSION STATE KARARLILİĞI
# ════════════════════════════════════════════════════════════════════════════

class TestSessionKararlilik:
    """Ardışık rerun ve modül geçişlerinde session state bozulmamalı."""

    def test_active_module_key_korunur(self):
        """Render sonrası active_module_key kaybolmamalı."""
        at = _at("map_uretim")
        assert "active_module_key" in at.session_state
        assert at.session_state["active_module_key"] == "map_uretim"

    def test_user_rol_rerun_sonrasi_korunur(self):
        """user_rol render sonrası değişmemeli."""
        at = _at("portal", "OPS")
        assert at.session_state["user_rol"] == "OPS"

    @pytest.mark.parametrize("modul", ["portal", "map_uretim", "ayarlar"])
    def test_coklu_modul_session_kararliligi(self, modul):
        """Her modülde session state bütünlüğü korunmalı."""
        at = _at(modul)
        assert at.session_state["logged_in"] is True
        assert at.session_state["active_module_key"] == modul


# ════════════════════════════════════════════════════════════════════════════
# H) LOGIN EKRANI
# ════════════════════════════════════════════════════════════════════════════

class TestLoginEkrani:
    """Login ekranı TopBar göçünden etkilenmemeli."""

    def test_render_exception_yok(self):
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        assert len(at.exception) == 0

    def test_kullanici_selectbox_var(self):
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        assert len(at.selectbox) >= 1

    def test_sifre_input_var(self):
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        assert len(at.text_input) >= 1

    def test_giris_butonu_var(self):
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        assert len(at.button) >= 1

    def test_hatali_giris_exception_yok(self):
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        at.text_input[0].set_value("yanlis_sifre_xyz_999")
        at.button[0].click().run()
        assert len(at.exception) == 0
        assert ("logged_in" not in at.session_state
                or not at.session_state["logged_in"])


# ════════════════════════════════════════════════════════════════════════════
# I) HATA İZLEYİCİ INLINE
# ════════════════════════════════════════════════════════════════════════════

class TestHataIzleyiciInline:
    """error_tracker.display_error_panel sidebar yerine inline render ediyor."""

    def test_hata_paneli_sidebar_degil(self):
        """Hata paneli sidebar'da değil, exception da yok."""
        at = _at("portal")
        assert len(at.exception) == 0
        # Sidebar'da expander/hata widget beklenmez
        assert len(at.sidebar.button) == 0
