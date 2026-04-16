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

def yetki_haritasi_yukle(engine, rol_adi: str, force_refresh=False) -> dict:
    """Anayasa v4.0: Hibrit Zone/Modül haritasını DB'den yükler.
    Artık statik ROL_ZONE_HARITASI kullanılmaz.
    """
    rol_adi_raw = str(rol_adi).strip()
    rol_adi_norm = _normalize_rol(rol_adi)
    
    if not force_refresh and rol_adi_raw in _YETKI_CACHE:
        return _YETKI_CACHE[rol_adi_raw]

    try:
        harita = {
            'zones': [],      # ['ops', 'mgt']
            'modules': {},    # {'modul_anahtar': {'erisim': 'tam', 'eylemler': {'ekle': True}, 'zone': 'ops'}}
            'varsayilan_modul': 'portal' # Her zaman portal ile başla
        }
        
        with engine.connect() as conn:
            # v5.5.1: Dinamik Modül Haritası
            mod_data = conn.execute(text("SELECT modul_anahtari, modul_etiketi, zone FROM ayarlar_moduller WHERE aktif = 1")).fetchall()
            etiket_anahtar_map = {row[1]: row[0] for row in mod_data} # Label -> Slug
            anahtar_zone_map = {row[0]: row[2] for row in mod_data}   # Slug -> Zone

            # v5.8.0: Tüm yetkileri çek ve Python tarafında normalize ederek eşleştir
            # v5.9.0: eylem_yetkileri kolonu yoksa graceful fallback (Migration Guard)
            try:
                sql = text("SELECT rol_adi, modul_adi, erisim_turu, ay.eylem_yetkileri FROM ayarlar_yetkiler ay")
                res = conn.execute(sql).fetchall()
            except Exception:
                sql = text("SELECT rol_adi, modul_adi, erisim_turu, NULL FROM ayarlar_yetkiler")
                res = conn.execute(sql).fetchall()
            
            seen_zones = set()
            for r_db, m_input, erisim_turu, eylem_yetkileri in res:
                if _normalize_rol(r_db) != rol_adi_norm:
                    continue
                    
                # v5.5.1: Girdi (Anahtar mı yoksa Etiket mi?) tespit et ve Slug'a çevir
                m_key = etiket_anahtar_map.get(m_input, m_input) 
                
                # Zone bilgisini dinamik haritadan al (Wipe Bug koruması)
                zone = anahtar_zone_map.get(m_key, "ops")

                harita['modules'][m_key] = {
                    'erisim': erisim_turu,
                    'eylemler': eylem_yetkileri or {},
                    'zone': zone
                }
                if zone and erisim_turu != 'Yok' and erisim_turu is not None:
                    seen_zones.add(zone)
            
            harita['zones'] = list(seen_zones)
            
            # v5.8.12: CASE-INSENSITIVE ADMIN BYPASS (Garantör Madde)
            if _normalize_rol(rol_adi) == 'ADMIN':
                harita['zones'] = ['ops', 'mgt', 'sys']
                # Tüm aktif modülleri tam yetkiyle ekle
                all_mods = conn.execute(text("SELECT modul_anahtari, zone FROM ayarlar_moduller WHERE aktif = 1")).fetchall()
                for am_anahtar, am_zone in all_mods:
                    if am_anahtar not in harita['modules']:
                        harita['modules'][am_anahtar] = {
                            'erisim': 'Düzenle',
                            'eylemler': {}, 
                            'zone': am_zone
                        }
            
            # Varsayılan modülü belirle
            harita['varsayilan_modul'] = _varsayilan_modul_bul(harita['zones'], harita['modules'])
            
        # Sadece başarılı yüklemeleri cache'le (Hata dönüşlerini sakla)
        if harita['zones']:
            _YETKI_CACHE[rol_adi] = harita
        st.session_state['yetki_haritasi'] = harita
        return harita
    except Exception as e:
        print(f"Yetki yükleme hatası: {e}")
        # v6.3.2: Zırhlı Admin Bypass - DB hatası olsa bile Admin her yeri görür
        if rol_adi and str(rol_adi).upper() == 'ADMIN':
            harita = {
                'zones': ['ops', 'mgt', 'sys'],
                'modules': {k: {'erisim': 'düzenle', 'eylemler': {}, 'zone': 'ops'} for k in ['portal', 'ayarlar', 'uretim_girisi']},
                'varsayilan_modul': 'portal'
            }
            st.session_state['yetki_haritasi'] = harita
            return harita
        
        # Hata durumunda kısıtlı güvenli varsayılanlar
        return {
            'zones': ['ops'],
            'modules': {'portal': {'erisim': 'goruntule', 'eylemler': {}, 'zone': 'ops'}},
            'varsayilan_modul': 'portal'
        }

def zone_girebilir_mi(zone: str) -> bool:
    """Bölge kapısı — Katman 1."""
    harita = st.session_state.get('yetki_haritasi', {})
    return zone in harita.get('zones', [])

def modul_gorebilir_mi(modul_anahtari: str) -> bool:
    """Modül görünürlük kontrolü — Katman 2."""
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
