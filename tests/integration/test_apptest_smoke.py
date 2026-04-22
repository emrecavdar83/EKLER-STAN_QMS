"""
tests/test_apptest_smoke.py
AppTest tabanlı uçtan uca widget ve modül smoke testleri.
Gerçek DB bağlantısı gerektirir (.streamlit/secrets.toml mevcut olmalı).
"""
import pytest
from streamlit.testing.v1 import AppTest

TIMEOUT = 60  # ayarlar modülü yavaş

# Registry'deki tüm modül anahtarları
TUM_MODULLER = [
    "portal",
    "uretim_girisi",
    "kpi_kontrol",
    "gmp_denetimi",
    "personel_hijyen",
    "temizlik_kontrol",
    "soguk_oda",
    "map_uretim",
    "gunluk_gorevler",
    "personel_vardiya_yonetimi",
    "performans_polivalans",
    "denetim_izi",
    "ayarlar",
    "profilim",
    "anayasa",
    "qdms",
    "kurumsal_raporlama",
]

# Zone kapısı olan modüller (OPS dışı rol ile erişilemez)
MGT_MODULLER = ["kpi_kontrol", "gmp_denetimi", "performans_polivalans", "denetim_izi", "kurumsal_raporlama", "qdms"]
SYS_MODULLER = ["ayarlar", "anayasa"]


def _admin_at(modul: str) -> AppTest:
    """ADMIN oturumu enjekte edilmiş AppTest örneği döner."""
    at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
    at.session_state["logged_in"] = True
    at.session_state["user"] = "Admin"
    at.session_state["user_rol"] = "ADMIN"
    at.session_state["user_fullname"] = "ADMIN"
    at.session_state["user_id"] = 1
    at.session_state["active_module_key"] = modul
    at.run()
    return at


def _ops_at(modul: str) -> AppTest:
    """OPS rolü ile AppTest örneği döner."""
    at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
    at.session_state["logged_in"] = True
    at.session_state["user"] = "ops_test"
    at.session_state["user_rol"] = "OPS"
    at.session_state["user_fullname"] = "OPS TEST"
    at.session_state["user_id"] = 99
    at.session_state["active_module_key"] = modul
    at.run()
    return at


# ────────────────────────────────────────────────────────────────
# SINIF 1: Login Ekranı Widget Testleri
# ────────────────────────────────────────────────────────────────

class TestLoginEkrani:
    def _login_at(self) -> AppTest:
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.run()
        return at

    def test_login_ekrani_render(self):
        """Login ekranı hatasız açılmalı."""
        at = self._login_at()
        assert len(at.exception) == 0

    def test_login_kullanici_selectbox(self):
        """Kullanıcı seçim kutusu mevcut olmalı."""
        at = self._login_at()
        assert len(at.selectbox) >= 1
        assert "Kullan" in at.selectbox[0].label  # encoding-safe

    def test_login_sifre_input(self):
        """Şifre alanı mevcut olmalı."""
        at = self._login_at()
        assert len(at.text_input) >= 1

    def test_login_giris_butonu(self):
        """'Giriş Yap' butonu mevcut olmalı."""
        at = self._login_at()
        assert len(at.button) >= 1

    def test_login_beni_hatirla_checkbox(self):
        """'Beni Hatırla' checkbox mevcut olmalı."""
        at = self._login_at()
        assert len(at.checkbox) >= 1

    def test_login_hatali_sifre_hata_gosterir(self):
        """Yanlış şifre girilince hata mesajı gösterilmeli, exception olmamalı."""
        at = self._login_at()
        at.selectbox[0].set_value(at.selectbox[0].value)
        at.text_input[0].set_value("yanlis_sifre_xyz_999")
        at.button[0].click().run()
        assert len(at.exception) == 0
        # Hatalı giriş sonrası hâlâ login ekranında olunmalı
        # AppTest session_state .get() desteklemez, [] veya 'in' kullanılır
        assert "logged_in" not in at.session_state or not at.session_state["logged_in"]


# ────────────────────────────────────────────────────────────────
# SINIF 2: Modül Smoke Testleri (ADMIN — Tüm Modüller)
# ────────────────────────────────────────────────────────────────

class TestModulSmoke:
    @pytest.mark.parametrize("modul", TUM_MODULLER)
    def test_modul_exception_yok(self, modul):
        """Her modül ADMIN oturumuyla hatasız render olmalı."""
        at = _admin_at(modul)
        assert len(at.exception) == 0, \
            f"{modul}: {at.exception[0] if at.exception else ''}"

    @pytest.mark.parametrize("modul", TUM_MODULLER)
    def test_modul_en_az_bir_widget(self, modul):
        """Her modül en az 1 interaktif widget içermeli (v6.3.0: TopBar — sidebar sayılmaz)."""
        at = _admin_at(modul)
        widget_toplam = (
            len(at.button)
            + len(at.selectbox)
            + len(at.text_input)
            + len(at.radio)
            + len(at.checkbox)
        )
        assert widget_toplam >= 1, f"{modul}: hiç widget yok"

    def test_portal_cok_buton(self):
        """Portal TopBar navigasyon butonlarıyla en az 10 butona sahip olmalı."""
        at = _admin_at("portal")
        assert len(at.button) >= 10, f"Portal beklenenden az buton: {len(at.button)}"

    def test_ayarlar_yonetim_arayuzu_zengin(self):
        """Ayarlar modülü en zengin widget setine sahip olmalı (v6.3.0: inline)."""
        at = _admin_at("ayarlar")
        assert len(at.button) >= 50, f"Ayarlar beklenenden az buton: {len(at.button)}"


# ────────────────────────────────────────────────────────────────
# SINIF 3: Zone Kapısı Testleri
# ────────────────────────────────────────────────────────────────

class TestZoneKapisi:
    @pytest.mark.parametrize("modul", MGT_MODULLER)
    def test_ops_mgt_modulune_erisemez(self, modul):
        """OPS rolü MGT zone modüllerine erişince 'erişim yok' mesajı görmeli."""
        at = _ops_at(modul)
        assert len(at.exception) == 0  # çökmemeli
        # Hata mesajı veya boş sayfa beklenir (st.error veya st.stop)
        hata_metinleri = " ".join(str(e.value) for e in at.error).lower()
        # Zone kapısı devreye girdiyse erişim mesajı ya da boş içerik beklenir
        # (st.stop() boş widget listesi bırakır)
        main_widget_sayisi = len(at.button) + len(at.text_input) + len(at.selectbox)
        zone_kapisi_devrede = ("eri" in hata_metinleri) or (main_widget_sayisi <= 3)
        assert zone_kapisi_devrede, \
            f"{modul}: OPS rolü zone kapısına takılmadı (widget: {main_widget_sayisi})"

    @pytest.mark.parametrize("modul", SYS_MODULLER)
    def test_ops_sys_modulune_erisemez(self, modul):
        """OPS rolü SYS zone modüllerine erişince zone kapısına takılmalı."""
        at = _ops_at(modul)
        assert len(at.exception) == 0
        hata_metinleri = " ".join(str(e.value) for e in at.error).lower()
        main_widget_sayisi = len(at.button) + len(at.text_input) + len(at.selectbox)
        zone_kapisi_devrede = ("eri" in hata_metinleri) or (main_widget_sayisi <= 3)
        assert zone_kapisi_devrede, \
            f"{modul}: OPS rolü zone kapısına takılmadı (widget: {main_widget_sayisi})"

    def test_admin_her_module_erisir(self):
        """ADMIN tüm modüllere erişebilmeli — hiçbirinde exception olmamalı."""
        hatali = []
        for m in TUM_MODULLER:
            at = _admin_at(m)
            if at.exception:
                hatali.append(m)
        assert not hatali, f"ADMIN erişemedi: {hatali}"


# ────────────────────────────────────────────────────────────────
# SINIF 4: Navigasyon ve Session State Testleri
# ────────────────────────────────────────────────────────────────

class TestNavigasyon:
    def test_topbar_mevcut(self):
        """v6.3.0: ADMIN oturumunda TopBar render olmalı — topnav_ butonları görünmeli."""
        at = _admin_at("portal")
        topnav = [b for b in at.button if b.key and b.key.startswith("topnav_")]
        assert len(topnav) >= 10, f"TopBar navigasyon butonları eksik: {len(topnav)}"

    def test_sidebar_tamamen_bos(self):
        """v6.3.0: TopBar göçü — sidebar'da hiç widget olmamalı."""
        at = _admin_at("portal")
        sidebar_widget = (
            len(at.sidebar.button)
            + len(at.sidebar.selectbox)
            + len(at.sidebar.radio)
            + len(at.sidebar.checkbox)
        )
        assert sidebar_widget == 0, f"Sidebar widget kaldı: {sidebar_widget}"

    def test_active_module_key_korunur(self):
        """Render sonrası active_module_key session_state'de kaybolmamalı."""
        at = _admin_at("map_uretim")
        # session_state erişimi
        assert at.session_state["active_module_key"] == "map_uretim" or \
               at.session_state.get("active_module_key") is not None

    def test_logged_in_korunur(self):
        """Render sonrası logged_in True kalmalı."""
        at = _admin_at("portal")
        assert at.session_state["logged_in"] is True

    def test_logout_url_calisir(self):
        """?logout=1 parametresi session'ı temizlemeli."""
        at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
        at.session_state["logged_in"] = True
        at.session_state["user"] = "Admin"
        at.session_state["user_rol"] = "ADMIN"
        at.query_params["logout"] = "1"
        at.run()
        assert len(at.exception) == 0
        # Logout sonrası login ekranına dönmeli
        assert "logged_in" not in at.session_state or not at.session_state["logged_in"]


# ────────────────────────────────────────────────────────────────
# SINIF 5: Bilinen Uyarı / Kalite Kontrol Testleri
# ────────────────────────────────────────────────────────────────

class TestKaliteKontrol:
    def test_hicbir_modulde_exception_yok_toplu(self):
        """Tüm 17 modül taranır — herhangi birinde exception varsa başarısız."""
        hata_ozeti = {}
        for m in TUM_MODULLER:
            at = _admin_at(m)
            if at.exception:
                hata_ozeti[m] = str(at.exception[0])[:100]
        assert not hata_ozeti, f"Exception'lı modüller:\n" + "\n".join(
            f"  {k}: {v}" for k, v in hata_ozeti.items()
        )

    def test_hijyen_radio_label_bos_degil(self):
        """hijyen_ui.py st.radio boş label uyarısı — widget yine de render edilmeli."""
        at = _admin_at("personel_hijyen")
        assert len(at.exception) == 0
        # Widget'lar erişilebilir olmalı (boş label crash'e yol açmamalı)
        assert (len(at.button) + len(at.radio)) >= 1

    def test_map_uretim_kritik_fonksiyon_erisimi(self):
        """MAP modülü açılışta kilitlenmemeli, en az 5 widget olmalı."""
        at = _admin_at("map_uretim")
        assert len(at.exception) == 0
        assert (len(at.button) + len(at.selectbox)) >= 5

    def test_vardiya_modulu_approval_widgetlari(self):
        """Vardiya modülü onay kuyruğu widget'larını render etmeli."""
        at = _admin_at("personel_vardiya_yonetimi")
        assert len(at.exception) == 0
        assert (len(at.button) + len(at.selectbox) + len(at.radio)) >= 3
