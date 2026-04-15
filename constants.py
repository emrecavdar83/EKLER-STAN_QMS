import streamlit as st
import json
from sqlalchemy import text

# v6.1: DB-Driven Constants with Fallback
# Circular import önlemek için local import kullanıyoruz.

def _get_db_param(key, fallback_val):
    """Veritabanından parametre çeker, yoksa yedeği döner."""
    try:
        from database.connection import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT deger FROM sistem_parametreleri WHERE anahtar = :k"), {"k": key}).fetchone()
            if res:
                return json.loads(res[0])
    except Exception:
        pass
    return fallback_val

@st.cache_data(ttl=600)
def get_position_levels():
    """Hiyerarşi seviyelerini döner (DB + Fallback)."""
    fallback = {
        0: {'name': 'Yönetim Kurulu', 'icon': '🏛️', 'color': '#1A5276', 'permissions': ['admin', 'all_departments', 'strategic']},
        1: {'name': 'Genel Müdür', 'icon': '👑', 'color': '#2874A6', 'permissions': ['admin', 'all_departments', 'operational']},
        2: {'name': 'Direktörler', 'icon': '📊', 'color': '#3498DB', 'permissions': ['multi_department', 'strategic_operations']},
        3: {'name': 'Müdürler', 'icon': '💼', 'color': '#5DADE2', 'permissions': ['department_admin', 'sub_departments']},
        4: {'name': 'Koordinatör / Şef', 'icon': '🎯', 'color': '#85C1E9', 'permissions': ['unit_admin', 'team_management']},
        5: {'name': 'Bölüm Sorumlusu', 'icon': '⭐', 'color': '#A3E4D7', 'permissions': ['team_management', 'basic_access']},
        6: {'name': 'Personel', 'icon': '👥', 'color': '#D4E6F1', 'permissions': ['own_records', 'basic_access']},
        7: {'name': 'Stajyer/Geçici', 'icon': '📝', 'color': '#ECF0F1', 'permissions': ['view_only']}
    }
    # DB'den çekilen veri string key ("0") içerdiği için int key'e (0) çeviriyoruz
    db_val = _get_db_param('POSITION_LEVELS', fallback)
    return {int(k): v for k, v in db_val.items()}

@st.cache_data(ttl=600)
def get_vardiya_listesi():
    """Vardiya listesini döner (DB + Fallback)."""
    fallback = ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"]
    return _get_db_param('VARDIYA_LISTESI', fallback)

# --- Legacy Helper Functions (v6.1: Pointing to DB-driven data) ---

def get_position_name(level):
    return get_position_levels().get(int(level), {}).get('name', 'Tanımsız')

def get_position_icon(level):
    return get_position_levels().get(int(level), {}).get('icon', '👤')

def get_position_color(level):
    return get_position_levels().get(int(level), {}).get('color', '#95A5A6')

def is_management(level):
    return int(level) in [0, 1, 2, 3, 4, 5]

def get_position_label(level):
    return f"{level} - {get_position_name(level)}"

# Global Değişkenler (UI uyumluluğu için dinamik olmayan hali korunur ama fonksiyon çağrısı önerilir)
POSITION_LEVELS = get_position_levels()
VARDIYA_LISTESI = get_vardiya_listesi()
MANAGEMENT_LEVELS = [0, 1, 2, 3, 4, 5]
STAFF_LEVELS = [6, 7]
