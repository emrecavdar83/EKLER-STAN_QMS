"""
Kurumsal Organizasyon Hiyerarşisi - Merkezi Tanımlar
Tüm QMS sisteminde kullanılacak pozisyon seviyeleri ve yetkilendirme yapısı
"""

POSITION_LEVELS = {
    0: {
        'name': 'Yönetim Kurulu',
        'icon': '🏛️',
        'color': '#1A5276',
        'permissions': ['admin', 'all_departments', 'strategic']
    },
    1: {
        'name': 'Genel Müdür',
        'icon': '👑',
        'color': '#2874A6',
        'permissions': ['admin', 'all_departments', 'operational']
    },
    2: {
        'name': 'Direktörler',
        'icon': '📊',
        'color': '#3498DB',
        'permissions': ['multi_department', 'strategic_operations']
    },
    3: {
        'name': 'Müdürler',
        'icon': '💼',
        'color': '#5DADE2',
        'permissions': ['department_admin', 'sub_departments']
    },
    4: {
        'name': 'Koordinatör / Şef',
        'icon': '🎯',
        'color': '#85C1E9',
        'permissions': ['unit_admin', 'team_management']
    },
    5: {
        'name': 'Bölüm Sorumlusu',
        'icon': '⭐',
        'color': '#A3E4D7',
        'permissions': ['team_management', 'basic_access']
    },
    6: {
        'name': 'Personel',
        'icon': '👥',
        'color': '#D4E6F1',
        'permissions': ['own_records', 'basic_access']
    },
    7: {
        'name': 'Stajyer/Geçici',
        'icon': '📝',
        'color': '#ECF0F1',
        'permissions': ['view_only']
    }
}

# Yönetici seviyeleri (organizasyon şemasında ayrı gösterilecek)
MANAGEMENT_LEVELS = [0, 1, 2, 3, 4, 5]
STAFF_LEVELS = [6, 7]


def get_position_name(level):
    """Pozisyon seviyesinden isim döndürür"""
    return POSITION_LEVELS.get(level, {}).get('name', 'Tanımsız')


def get_position_icon(level):
    """Pozisyon seviyesinden ikon döndürür"""
    return POSITION_LEVELS.get(level, {}).get('icon', '👤')


def get_position_color(level):
    """Pozisyon seviyesinden renk döndürür"""
    return POSITION_LEVELS.get(level, {}).get('color', '#95A5A6')


def is_management(level):
    """Yönetici seviyesi mi kontrol eder"""
    return level in MANAGEMENT_LEVELS


def get_position_label(level):
    """Dropdown için formatlanmış etiket döndürür"""
    return f"{level} - {get_position_name(level)}"


# --- VARDİYA TANIMLARI ---
# Tüm sistemde standardize edilmiş vardiya listesi
VARDIYA_LISTESI = ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"]
