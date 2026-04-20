"""
EKLERİSTAN QMS — Zone Yetki Modülü
İki katmanlı yetki sistemi: Bölge kapısı + Modül yetkisi

Tüm kontroller RAM'den yapılır, 0 DB sorgusu.
Yetki haritası oturum başında 1 kez yüklenir.
v3.2.0 - ANTIGRAVITY
"""
import streamlit as st
from sqlalchemy import text

# ── PERFORMANS SAYAÇLARI ──
def sorgu_sayisini_getir():
    if '_zone_sorgu_sayaci' not in st.session_state:
        st.session_state['_zone_sorgu_sayaci'] = 0
    return st.session_state.get('_zone_sorgu_sayaci', 0)

# ── Bölge tanımları (sabit, hardcode değil — DB'den gelir) ──
ZONE_VARSAYILAN_MODULLERI = {
    'ops': 'uretim_girisi',
    'mgt': 'kpi_kontrol',
    'sys': 'ayarlar',
}

# 1. TEMEL YAPI VE ÖNBELLEK
_YETKI_CACHE = {} # {rol_adi: {map}}

def _normalize_rol(s):
    """v5.8.0: Rol isimlerini normalize ederek karşılaştırma sağlar."""
    if not s: return ""
    import re
    s = str(s).upper().strip()
    translation = str.maketrans("İÜÖÇŞĞ", "IUOCSG")
    s = s.translate(translation)
    s = "".join(re.findall(r'[A-Z0-9\s]', s))
    return s.strip()

def _yetki_verilerini_isle(conn, rol_adi_norm: str, harita: dict) -> dict:
    """Modül ve yetki verilerini DB'den çekip haritaya işler."""
    mod_data = conn.execute(text("SELECT modul_anahtari, modul_etiketi, zone FROM ayarlar_moduller WHERE aktif = 1")).fetchall()
    etiket_anahtar_map = {row[1]: row[0] for row in mod_data}
    anahtar_zone_map = {row[0]: row[2] for row in mod_data}
    
    try:
        sql = text("SELECT rol_adi, modul_adi, erisim_turu, ay.eylem_yetkileri FROM ayarlar_yetkiler ay")
        res = conn.execute(sql).fetchall()
    except Exception:
        sql = text("SELECT rol_adi, modul_adi, erisim_turu, NULL FROM ayarlar_yetkiler")
        res = conn.execute(sql).fetchall()
    
    seen_zones = set()
    for r_db, m_input, erisim_turu, eylem_yetkileri in res:
        if _normalize_rol(r_db) == rol_adi_norm:
            m_key = etiket_anahtar_map.get(m_input, m_input) 
            zone = anahtar_zone_map.get(m_key, "ops")
            harita['modules'][m_key] = {'erisim': erisim_turu, 'eylemler': eylem_yetkileri or {}, 'zone': zone}
            if zone and erisim_turu not in ('Yok', None):
                seen_zones.add(zone)
    harita['zones'] = list(seen_zones)
    return harita

def _admin_bypass_ve_varsayilan(conn, rol_adi: str, harita: dict) -> dict:
    """Admin için tam yetki tanımlar ve varsayılan modülü bulur."""
    if _normalize_rol(rol_adi) == 'ADMIN':
        harita['zones'] = ['ops', 'mgt', 'sys']
        all_mods = conn.execute(text("SELECT modul_anahtari, zone FROM ayarlar_moduller WHERE aktif = 1")).fetchall()
        for am_anahtar, am_zone in all_mods:
            if am_anahtar not in harita['modules']:
                harita['modules'][am_anahtar] = {'erisim': 'Düzenle', 'eylemler': {}, 'zone': am_zone}
    
    harita['varsayilan_modul'] = _varsayilan_modul_bul(harita['zones'], harita['modules'])
    return harita

def _get_fallback_authorizations(rol_adi: str) -> dict:
    """Hata durumunda güvenli yetki setini döner."""
    if rol_adi and str(rol_adi).upper() == 'ADMIN':
        return {
            'zones': ['ops', 'mgt', 'sys'],
            'modules': {k: {'erisim': 'düzenle', 'eylemler': {}, 'zone': 'ops'} for k in ['portal', 'ayarlar', 'uretim_girisi']},
            'varsayilan_modul': 'portal'
        }
    return {
        'zones': ['ops'],
        'modules': {'portal': {'erisim': 'goruntule', 'eylemler': {}, 'zone': 'ops'}},
        'varsayilan_modul': 'portal'
    }

def yetki_haritasi_yukle(engine, rol_adi, force_refresh=False) -> dict:
    """Anayasa v5.0: Hibrit Zone/Modül haritasını DB'den yükler (Refactored)."""
    rol_adi_raw = str(rol_adi).strip()
    rol_adi_norm = _normalize_rol(rol_adi)
    if not force_refresh and rol_adi_raw in _YETKI_CACHE:
        return _YETKI_CACHE[rol_adi_raw]
    try:
        harita = {'zones': [], 'modules': {}, 'varsayilan_modul': 'portal'}
        with engine.connect() as conn:
            harita = _yetki_verilerini_isle(conn, rol_adi_norm, harita)
            harita = _admin_bypass_ve_varsayilan(conn, rol_adi, harita)
        if harita['zones']:
            _YETKI_CACHE[rol_adi_raw] = harita
        st.session_state['yetki_haritasi'] = harita
        return harita
    except Exception as e:
        print(f"Yetki yükleme hatası: {e}")
        harita = _get_fallback_authorizations(rol_adi)
        st.session_state['yetki_haritasi'] = harita
        return harita


def zone_girebilir_mi(zone: str) -> bool:
    """Bölge kapısı — Katman 1. (Zırhlı Admin Bypass dahil)"""
    # v6.8.2: Hardcoded Admin Bypass (Son Savunma Hattı)
    if _normalize_rol(st.session_state.get('user_rol')) == 'ADMIN':
        return True
    
    harita = st.session_state.get('yetki_haritasi', {})
    return zone in harita.get('zones', [])

def modul_gorebilir_mi(modul_anahtari: str) -> bool:
    """Modül görünürlük kontrolü — Katman 2. (Zırhlı Admin Bypass dahil)"""
    # v6.8.2: Hardcoded Admin Bypass
    if _normalize_rol(st.session_state.get('user_rol')) == 'ADMIN':
        return True

    harita = st.session_state.get('yetki_haritasi', {})
    modul = harita.get('modules', {}).get(modul_anahtari)
    if not modul:
        return False
    erisim = str(modul.get('erisim', 'Yok')).lower()
    return erisim in ('tam', 'goruntule', 'görüntüle', 'düzenle', 'duzenle')

def eylem_yapabilir_mi(modul_anahtari: str, eylem: str) -> bool:
    """Buton/eylem yetki kontrolü — Katman 3."""
    harita = st.session_state.get('yetki_haritasi', {})
    modul = harita.get('modules', {}).get(modul_anahtari, {})
    eylemler = modul.get('eylemler', {})
    return eylemler.get(eylem, False)

def varsayilan_modul_getir() -> str:
    """Kullanıcının rol'üne göre açılış modülü."""
    harita = st.session_state.get('yetki_haritasi', {})
    # Her zaman Portal'ı tercih et (Anayasa v4.0.6)
    return 'portal'

def _modul_yetkileri_getir(engine, rol: str) -> dict:
    """Tek sorguda tüm modül yetkilerini çeker."""
    if '_zone_sorgu_sayaci' not in st.session_state:
        st.session_state['_zone_sorgu_sayaci'] = 0
    st.session_state['_zone_sorgu_sayaci'] += 1
    sql = text("""
        SELECT
            ay.modul_adi,
            ay.erisim_turu,
            ay.zone_erisim,
            ay.eylem_yetkileri,
            am.zone
        FROM ayarlar_yetkiler ay
        JOIN ayarlar_moduller am
            ON ay.modul_adi = am.modul_anahtari
        WHERE ay.rol_adi = :rol
        AND am.aktif = 1
    """)
    sonuc = {}
    with engine.connect() as conn:
        rows = conn.execute(sql, {'rol': rol}).fetchall()
        for row in rows:
            # SQLAlchemy Row nesnesi erişimi
            sonuc[row[0]] = {
                'erisim':  row[2] or row[1],
                'eylemler': row[3] or {},
                'zone':    row[4],
            }
    return sonuc

def _varsayilan_modul_bul(roller: list, moduller: dict) -> str:
    """Rol'e göre en uygun açılış modülünü bulur."""
    if 'portal' in moduller:
        return 'portal'
    for zone in roller:
        varsayilan = ZONE_VARSAYILAN_MODULLERI.get(zone)
        if varsayilan and varsayilan in moduller:
            return varsayilan
    return 'portal' if 'portal' in moduller else (list(moduller.keys())[0] if moduller else 'portal')
