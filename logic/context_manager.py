import re
import os
import urllib.request
from datetime import datetime
from sqlalchemy import text
from database.connection import get_engine

# EKLERİSTAN A.Ş. 
# Faz 2.3: Dinamik Dokümantasyon Bağlam Sistemi (Context7 Eşdeğeri)

def log_aktivite(islem: str, detay: str):
    """Anayasa Madde 12: Sessizce (fail-silent) log kaydı yapar."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            sql = text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES (:i, :d)")
            conn.execute(sql, {"i": "CONTEXT_SYS", "d": f"[{islem}] {detay}"})
    except Exception as _e:
        print(f"LOG_AKTIVITE_ERR [{islem}]: {_e}")

def dokuman_indir(url: str) -> str:
    """Belirtilen URL'den dokümanı ham metin olarak indirir."""
    if not url: return ""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        log_aktivite("INDIRME_HATASI", f"URL: {url} | Hata: {str(e)}")
        # Akılda kalıcı olması için print veya traceback bırakabiliriz (Terminal için)
        print(f"Iletisim hatasi: {url} -> {e}")
        return ""

def html_ve_rst_temizle(ham_metin: str) -> str:
    """HTML etiketlerini ve RST işaretlerini temizler (Regex tabanlı)."""
    if not ham_metin: return ""
    # HTML Temizleme
    metin = re.sub(r'<[^>]+>', '', ham_metin)
    # RST Temizleme (Linkler, Code blokları vb. basitçe)
    metin = re.sub(r'`([^`]+)`_', r'\1', metin) # RST Link
    metin = re.sub(r'(\.\. [^:]+::)', '---', metin) # RST Directive
    metin = re.sub(r'(:[a-zA-Z0-9_-]+:`[^`]+`)', r'\1', metin) # Role
    return metin.strip()

def icerik_parcala(metin: str, parca_boyutu_kb: int = 50) -> list:
    """Uzun metni belirlenen KB sınırına göre anlamlı parçalara böler."""
    sinir = parca_boyutu_kb * 1024
    parcalar = []
    current_chunk = ""
    
    for line in metin.splitlines():
        if len(current_chunk.encode('utf-8')) + len(line.encode('utf-8')) < sinir:
            current_chunk += line + "\n"
        else:
            parcalar.append(current_chunk)
            current_chunk = line + "\n"
    
    if current_chunk: parcalar.append(current_chunk)
    return parcalar

def döküman_kaydet(lib_name: str, parcalar: list):
    """Temizlenmiş parçaları cache dizinine kaydeder."""
    cache_yolu = f".antigravity/context/cache/{lib_name}/"
    if not os.path.exists(cache_yolu):
        os.makedirs(cache_yolu, exist_ok=True)
    
    for i, parca in enumerate(parcalar):
        dosya_adi = f"{cache_yolu}parca_{i+1}.md"
        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write(f"# Context: {lib_name} (Part {i+1})\n")
            f.write(f"Updated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(parca)
    
    log_aktivite("KAYIT_BASARILI", f"{lib_name} için {len(parcalar)} parça kaydedildi.")

def registry_oku() -> dict:
    """.antigravity/context/registry.yaml dosyasını okur ve sözlük döner."""
    yol = ".antigravity/context/registry.yaml"
    libs = {}
    if not os.path.exists(yol): return libs
    
    try:
        import yaml
        with open(yol, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if 'libraries' in data:
                return data['libraries']
    except ImportError:
        # PyYAML yoksa manuel basit parser
        try:
            current_lib = None
            in_libraries = False
            with open(yol, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip() or line.strip().startswith("#"): continue
                    
                    if not line.startswith(" "):
                        # Root nodes
                        if line.startswith("libraries:"): in_libraries = True
                        elif line.startswith("settings:"): in_libraries = False
                        continue
                        
                    if not in_libraries: continue
                    
                    if line.startswith("  ") and not line.startswith("    ") and ":" in line:
                        current_lib = line.split(":")[0].strip()
                        libs[current_lib] = {}
                    elif line.startswith("    ") and ":" in line and current_lib:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            libs[current_lib][parts[0].strip()] = parts[1].strip().strip('"').strip("'")
        except Exception:
            log_aktivite("REGISTRY_HATASI", "Manuel YAML parser hatası.")
    except Exception as e:
        log_aktivite("REGISTRY_HATASI", f"Kayıt defteri okunamadı: {e}")
    return libs

def kütüphane_guncelle(lib_name: str, url: str):
    """Tek bir kütüphane için dökümanı çeker, temizler ve kaydeder."""
    ham = dokuman_indir(url)
    if not ham: return
    
    temiz = html_ve_rst_temizle(ham)
    parcalar = icerik_parcala(temiz)
    döküman_kaydet(lib_name, parcalar)

def tümünü_senkronize_et():
    """Kayıt defterindeki tüm dökümanları sırayla günceller."""
    import streamlit as st
    registry = registry_oku()
    if not registry: 
        st.error("Kayıt defteri (registry.yaml) boş veya okunamadı!")
        return 0
    
    count = 0
    hatalar = 0
    for lib, props in registry.items():
        url = props if isinstance(props, str) else props.get("github_raw", "")
        if "http" in str(url):
            ham = dokuman_indir(url)
            if ham:
                temiz = html_ve_rst_temizle(ham)
                parcalar = icerik_parcala(temiz)
                döküman_kaydet(lib, parcalar)
                count += 1
            else:
                hatalar += 1
                st.warning(f"⚠️ İndirilemedi: {lib.upper()} ({url[:40]}...)")
                
    st.info(f"Senkronizasyon Raporu: {count} Başarılı, {hatalar} Başarısız/Eksik.")
    log_aktivite("SYNC_COMPLETED", f"{count} kütüphane başarıyla senkronize edildi.")
    return count

def ajanlara_baglam_ekle():
    """Ajanların CLAUDE.md dosyalarına dokümantasyon referansı ekler."""
    ajanlar = ["builder_backend", "builder_db", "builder_frontend", "tester", "guardian"]
    for ajan in ajanlar:
        yol = f".antigravity/{ajan}/CLAUDE.md"
        if os.path.exists(yol):
            _claudemd_guncelle(yol, ajan)

def _claudemd_guncelle(yol: str, ajan_adi: str):
    """Bireysel CLAUDE.md dosyasını yeni bağlam ile günceller."""
    with open(yol, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "## 📚 DOKÜMANTASYON BAĞLAMI" in content: return # Zaten ekli
    
    baglam_notu = "\n\n---\n\n## 📚 DOKÜMANTASYON BAĞLAMI\n"
    baglam_notu += "> [!NOTE]\n"
    baglam_notu += "> Bu ajan, kod üretirken `.antigravity/context/cache/` altındaki\n"
    baglam_notu += "> güncel resmi doküman parçalarını referans almalıdır.\n"
    
    new_content = content.replace("## UZMANLIK KURALLARI", baglam_notu + "## UZMANLIK KURALLARI")
    with open(yol, "w", encoding="utf-8") as f:
        f.write(new_content)
