"""
EKLERİSTAN QMS — Zone Yetki Modülü
İki katmanlı yetki sistemi: Bölge kapısı + Modül yetkisi

Tüm kontroller RAM'den yapılır, 0 DB sorgusu.
Yetki haritası oturum başında 1 kez yüklenir.
v3.2.0 - ANTIGRAVITY
"""
import streamlit as st
from sqlalchemy import text

# ── Bölge tanımları (sabit, hardcode değil — DB'den gelir) ──
ZONE_VARSAYILAN_MODULLERI = {
    'ops': 'uretim_girisi',
    'mgt': 'kpi_kontrol',
    'sys': 'ayarlar',
}

ROL_ZONE_HARITASI = {
    'PERSONEL':  ['ops'],
    'OPERATÖR':  ['ops'],
    'KALİTE':    ['ops', 'mgt'],
    'MÜDÜR':     ['mgt'],
    'DİREKTÖR':  ['mgt', 'sys'],
    'ADMIN':     ['ops', 'mgt', 'sys'],
}

def yetki_haritasi_yukle(engine, rol: str) -> dict:
    """
    Kullanıcının tüm yetkilerini tek sorguda çeker.
    session_state.yetki_haritasi'na yazılır.
    """
    # Rol normalizasyonu
    rol_upper = str(rol).upper().replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    
    # 13. ADAM: Eğer rol haritada yoksa OPS sadece görüntüle gibi bir kısıtla başla
    roller = ROL_ZONE_HARITASI.get(str(rol).upper(), ['ops'])

    moduller = _modul_yetkileri_getir(engine, rol)
    varsayilan = _varsayilan_modul_bul(roller, moduller)

    return {
        'roller': roller,
        'moduller': moduller,
        'varsayilan_modul': varsayilan,
    }

def zone_girebilir_mi(zone: str) -> bool:
    """Bölge kapısı — Katman 1."""
    harita = st.session_state.get('yetki_haritasi', {})
    return zone in harita.get('roller', [])

def modul_gorebilir_mi(modul_anahtari: str) -> bool:
    """Modül görünürlük kontrolü — Katman 2."""
    harita = st.session_state.get('yetki_haritasi', {})
    modul = harita.get('moduller', {}).get(modul_anahtari)
    if not modul:
        return False
    return modul.get('erisim') in ('tam', 'goruntule')

def eylem_yapabilir_mi(modul_anahtari: str, eylem: str) -> bool:
    """Buton/eylem yetki kontrolü — Katman 3."""
    harita = st.session_state.get('yetki_haritasi', {})
    modul = harita.get('moduller', {}).get(modul_anahtari, {})
    eylemler = modul.get('eylemler', {})
    return eylemler.get(eylem, False)

def varsayilan_modul_getir() -> str:
    """Kullanıcının rol'üne göre açılış modülü."""
    harita = st.session_state.get('yetki_haritasi', {})
    return harita.get('varsayilan_modul', 'uretim_girisi')

def _modul_yetkileri_getir(engine, rol: str) -> dict:
    """Tek sorguda tüm modül yetkilerini çeker."""
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
    for zone in roller:
        varsayilan = ZONE_VARSAYILAN_MODULLERI.get(zone)
        if varsayilan and varsayilan in moduller:
            return varsayilan
    return list(moduller.keys())[0] if moduller else 'uretim_girisi'
