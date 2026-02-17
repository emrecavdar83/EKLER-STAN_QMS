
import json
import pandas as pd
from sqlalchemy import create_engine
from difflib import SequenceMatcher

def get_ratio(a, b): return SequenceMatcher(None, a, b).ratio()

# 1. Kaynaktan (sync_payload.json) hedef listeyi oku
try:
    with open('sync_payload.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Unique names, sorted, upper case
    target_list = sorted(list(set([name.strip().upper() for name in data['target_list'] if name])))
except Exception as e:
    print(f"Hata: sync_payload.json okunamadı: {e}")
    exit()

# 2. Canlı veritabanına bağlan
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DB_URL)

try:
    with engine.connect() as conn:
        df_live = pd.read_sql("SELECT ad_soyad, durum, bolum FROM personel WHERE ad_soyad IS NOT NULL", conn)
    
    # Canlı veriyi işle
    df_live['clean_name'] = df_live['ad_soyad'].astype(str).str.upper().str.strip()
    all_live_names = set(df_live['clean_name'].tolist())
    active_live_names = set(df_live[df_live['durum'] == 'AKTİF']['clean_name'].tolist())
    
    # 3. Karşılaştırma
    completely_missing = sorted(list(set(target_list) - all_live_names))
    exists_but_passive = sorted(list((set(target_list) & all_live_names) - active_live_names))
    active_matches = sorted(list(set(target_list) & active_live_names))
    extra_active_in_live = sorted(list(active_live_names - set(target_list)))

    # 4. Raporu oluştur
    report = []
    report.append("--- PERSONEL LISTESI KARSILASTIRMA RAPORU ---")
    report.append(f"Tarih: 30.01.2026")
    report.append(f"\nGENEL OZET:")
    report.append(f"- Gorseldeki (Hedef) Personel Sayisi: {len(target_list)}")
    report.append(f"- Sistemde AKTIF Olarak Kayitli Kisi: {len(active_live_names)}")
    report.append(f"- Sistemde Kayitli Toplam (Aktif+Pasif): {len(all_live_names)}")
    report.append("-" * 30)
    report.append(f"AKTIF ve TAM ESLESEN: {len(active_matches)} kisi")
    report.append(f"SISTEMDE VAR AMA PASIF: {len(exists_but_passive)} kisi")
    report.append(f"SISTEMDE HIC YOK: {len(completely_missing)} kisi")
    report.append(f"SISTEMDE FAZLADAN AKTIF (LISTEDE YOK): {len(extra_active_in_live)} kisi")
    report.append("-" * 30)

    if exists_but_passive:
        report.append("\n[!] SISTEMDE VAR AMA DURUMU PASIF OLANLAR (Aktif Edilmeli):")
        for n in exists_but_passive:
            report.append(f"  - {n}")

    if completely_missing:
        report.append("\n[!] SISTEMDE HIC KAYDI BULUNMAYANLAR (Yeni Eklenmeli):")
        for n in completely_missing:
            report.append(f"  - {n}")

    if extra_active_in_live:
        report.append("\n[!] SISTEMDE AKTIF GORUNEN AMA LISTEDE OLMAYANLAR (Pasife Alinabilir):")
        for n in extra_active_in_live:
            report.append(f"  - {n}")

    # Fuzzy Suggestions
    if completely_missing and extra_active_in_live:
        report.append("\n[!] OLASI ISIM DEGISIKLIKLERI / YAZIM FARKLARI (Oneri):")
        found_any = False
        for miss in completely_missing:
            matches = []
            for extra in extra_active_in_live:
                ratio = get_ratio(miss, extra)
                if ratio > 0.75:
                    matches.append((extra, ratio))
            if matches:
                matches.sort(key=lambda x: x[1], reverse=True)
                best = matches[0][0]
                report.append(f"  - Hedefte: {miss}  -->  Canlida: {best} (Benzerlik: %{int(matches[0][1]*100)})")
                found_any = True
        if not found_any:
            report.append("  - Yakin benzerlik bulunamadi.")

    report.append("\n--- Rapor Sonu ---")
    
    output_text = "\n".join(report)
    # Windows konsolu icin emoji icermeyen metni bas
    print(output_text)

    # Markdown olarak dosyaya yaz (Emoji icerebilir)
    with open('PERSONEL_HABERLESME_RAPORU.md', 'w', encoding='utf-8') as f:
        f.write(output_text.replace('--- ', '# ').replace('\n- ', '\n- ✅ ' if 'TAM ESLESEN' in output_text else '\n- '))

except Exception as e:
    print(f"Hata: {e}")
