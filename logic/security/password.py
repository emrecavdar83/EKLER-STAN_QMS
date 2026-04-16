import streamlit as st
import pandas as pd
from sqlalchemy import text
import bcrypt
import json
from datetime import datetime
from passlib.hash import bcrypt as passlib_bcrypt

# v4.3.4 Hotfix: Bcrypt 4.0+ ile Passlib __about__ hatasını önlemek için yama
if not hasattr(bcrypt, "__about__"):
    from types import SimpleNamespace
    bcrypt.__about__ = SimpleNamespace(__version__=getattr(bcrypt, "__version__", "4.0.0"))

def sifre_hashle(plain_sifre):
    """
    v4.4.2-FINAL: Garantili Byte Budama (Byte-Based Slashing).
    Bcrypt'in 72-byte limitine çarpılmayı FİZİKSEL olarak imkansız kılar.
    """
    if not plain_sifre: return None
    try:
        # v4.4.2: String değil, BYTE seviyesinde 64 byte limitine çekiyoruz.
        safe_bytes = str(plain_sifre).encode('utf-8')[:64]
        safe_str = safe_bytes.decode('utf-8', 'ignore')
        return passlib_bcrypt.hash(safe_str)
    except Exception as e:
        from logic.error_handler import log_error
        log_error(e, modul="SECURITY_PASSWORD", fonksiyon="sifre_hashle")
        return str(plain_sifre)

def _bcrypt_formatinda_mi(s):
    """Şifrenin bcrypt hash formatında ($2b$...) olup olmadığını kontrol eder."""
    return str(s).startswith("$2b$") or str(s).startswith("$2a$")

def sifre_dogrula(girilen_sifre, db_sifre, kullanici_adi=None, engine=None):
    """Dual-Validation: Hem plain-text hem bcrypt destekler, otomatik migration sağlar."""
    if not db_sifre: return False
    
    try:
        # v4.3.3: Bcrypt 64-byte Zırhı
        input_bytes = str(girilen_sifre).encode('utf-8')[:64]
        clean_sifre = input_bytes.decode('utf-8', 'ignore')
        hash_val = str(db_sifre).strip()

        if _bcrypt_formatinda_mi(hash_val):
            return passlib_bcrypt.verify(clean_sifre, hash_val)
        else:
            # Fallback: Plain-text karşılaştırma
            if _plaintext_fallback_izni_var_mi(engine):
                gecerli = (str(girilen_sifre) == str(db_sifre))
                if gecerli and kullanici_adi and engine:
                    _sifreyi_hashle_ve_guncelle(kullanici_adi, girilen_sifre, engine)
                return gecerli
            return False
    except Exception as e:
        print(f"⚠️ SIFRE_DOGRULAMA_KRITIK: {e}")
        try:
            return str(girilen_sifre) == str(db_sifre)
        except:
            return False

def _plaintext_fallback_izni_var_mi(engine=None):
    """Anayasa v3.2: Plain-text şifre desteğinin hala geçerli olup olmadığını kontrol eder."""
    if not engine:
        from database.connection import get_engine
        engine = get_engine()
    try:
        with engine.connect() as conn:
            sql = text("SELECT param_adi, param_degeri FROM sistem_parametreleri WHERE param_adi IN ('plaintext_fallback_aktif', 'fallback_bitis_tarihi')")
            res = conn.execute(sql).fetchall()
            ayarlar = {r[0]: r[1] for r in res}
            
            aktif = ayarlar.get('plaintext_fallback_aktif', 'True').lower() == 'true'
            if not aktif: return False
            
            bitis_str = ayarlar.get('fallback_bitis_tarihi', '2026-06-15')
            bitis_tarihi = pd.to_datetime(bitis_str)
            bugun = pd.Timestamp.now().normalize()
            return bugun <= bitis_tarihi
    except Exception:
        return True

def get_fallback_info(engine=None):
    """Anayasa v3.2: Grace period bitiş tarihini ve durumunu döner."""
    if not engine:
        from database.connection import get_engine
        engine = get_engine()
    try:
        with engine.connect() as conn:
            sql = text("SELECT param_degeri FROM sistem_parametreleri WHERE param_adi = 'fallback_bitis_tarihi'")
            res = conn.execute(sql).scalar()
            return str(res) if res else "2026-06-15"
    except Exception:
        return "2026-06-15"

def _sifreyi_hashle_ve_guncelle(kullanici_adi, plain_sifre, engine):
    """Şifreyi atomik ve güvenli bir şekilde bcrypt hash'ine dönüştürür."""
    if not plain_sifre: return False
    try:
        yeni_hash = sifre_hashle(plain_sifre)
        if not yeni_hash or yeni_hash == plain_sifre: return False
        
        # Yazmadan önce doğrula
        if not sifre_dogrula(plain_sifre, yeni_hash): return False
            
        with engine.begin() as conn:
            sql = text("UPDATE personel SET sifre = :h WHERE kullanici_adi = :k AND (sifre IS NULL OR sifre NOT LIKE '$2%')")
            conn.execute(sql, {"h": yeni_hash, "k": kullanici_adi})
            # Log kaydı auth_logic üzerinden yapılacak (circular import'tan kaçınmak için)
        return True
    except Exception:
        return False
