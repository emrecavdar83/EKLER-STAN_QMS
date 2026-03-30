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
    except:
        pass

def dokuman_indir(url: str) -> str:
    """Belirtilen URL'den dokümanı ham metin olarak indirir."""
    if not url: return ""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        log_aktivite("INDIRME_HATASI", f"URL: {url} | Hata: {str(e)}")
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
        os.makedirs(cache_yolu)
    
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
        with open(yol, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if ":" in line and "-" not in line and "libraries" not in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        key = parts[0].strip().lower()
                        val = parts[1].strip()
                        libs[key] = val
    except:
        log_aktivite("REGISTRY_HATASI", "Kayıt defteri okunamadı.")
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
    # Anayasa Madde 1: Zero Hardcode (Veri Registry'den gelir)
    registry = registry_oku()
    if not registry: return
    
    count = 0
    for lib, props in registry.items():
        # Basit line-based parser desteği (RAW URL veya JSON gibi davranır)
        url = props if isinstance(props, str) else props.get("github_raw", "")
        if "http" in str(url):
            kütüphane_guncelle(lib, url)
            count += 1
    
    log_aktivite("SYNC_COMPLETED", f"{count} kütüphane başarıyla senkronize edildi.")

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
