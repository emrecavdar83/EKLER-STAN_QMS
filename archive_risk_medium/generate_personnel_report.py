import json
import psycopg2
import pandas as pd
from datetime import datetime
import os

def compare_personnel():
    # 1. Load target list from sync_payload.json
    payload_path = r"c:\Projeler\S_program\EKLERİSTAN_QMS\sync_payload.json"
    with open(payload_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    
    target_names = set(payload.get("target_list", []))
    
    # 2. Get DB connection from secrets
    # DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    conn_str = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(conn_str)
        # Fetch status as well to report on active/passive
        query = "SELECT ad_soyad, durum FROM personel"
        live_df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    # Normalize names for robust comparison
    def normalize(name):
        if not name: return ""
        return " ".join(name.strip().upper().split())

    target_normalized = {normalize(n): n for n in target_names}
    live_df['normalized'] = live_df['ad_soyad'].apply(normalize)
    
    live_names_all = set(live_df['normalized'])
    live_names_active = set(live_df[live_df['durum'] == 'AKTİF']['normalized'])
    
    # Analysis
    missing_in_live = [] # In target but NOT in live (any status)
    passive_in_live_but_in_target = [] # In target but PASSIVE in live
    extra_in_live_active = [] # Active in live but NOT in target
    
    # 1. Missing in Live (Total)
    for norm_name, original_name in target_normalized.items():
        if norm_name not in live_names_all:
            missing_in_live.append(original_name)
            
    # 2. Passive but should be Active (In target)
    for norm_name, original_name in target_normalized.items():
        if norm_name in live_names_all and norm_name not in live_names_active:
            status = live_df[live_df['normalized'] == norm_name]['durum'].iloc[0]
            passive_in_live_but_in_target.append(f"{original_name} (Mevcut Durum: {status})")

    # 3. Active in Live but NOT in target (Extra)
    for _, row in live_df[live_df['durum'] == 'AKTİF'].iterrows():
        if row['normalized'] not in target_normalized:
            extra_in_live_active.append(row['ad_soyad'])

    # Prepare Report
    report = []
    report.append("# Personel Listesi Karşılaştırma Raporu")
    report.append(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    report.append("\n## Özet")
    report.append(f"- Görsel Listesindeki (Hedef) Personel Sayısı: {len(target_names)}")
    report.append(f"- Canlı Veritabanındaki Aktif Personel Sayısı: {len(live_names_active)}")
    report.append(f"- Canlı Veritabanındaki Toplam Kayıt Sayısı: {len(live_df)}")
    
    report.append("\n## 1. Eksik Personeller (Listede var, Veritabanında hiç yok)")
    if missing_in_live:
        for name in sorted(missing_in_live):
            report.append(f"- [ ] {name}")
    else:
        report.append("- Tüm personel kayıtları veritabanında mevcut.")

    report.append("\n## 2. Pasif Durumdaki Personeller (Listede var, Veritabanında PASİF/NULL)")
    report.append("> [!NOTE]\n> Bu personeller veritabanında kayıtlı ancak durumları 'AKTİF' değil. Aktif edilmeleri gerekebilir.")
    if passive_in_live_but_in_target:
        for name in sorted(passive_in_live_but_in_target):
            report.append(f"- [ ] {name}")
    else:
        report.append("- Listedeki tüm personeller veritabanında aktif.")

    report.append("\n## 3. Fazla/Silinecek Personeller (Veritabanında Aktif, ama listede YOK)")
    report.append("> [!WARNING]\n> Bu personeller listede bulunmuyor ancak şu an sistemde aktif görünüyorlar.")
    if extra_in_live_active:
        for name in sorted(extra_in_live_active):
            report.append(f"- [ ] {name}")
    else:
        report.append("- Fazla aktif personel bulunmadı.")

    report_content = "\n".join(report)
    
    # Save to file
    with open("PERSONEL_KARSILASTIRMA_RAPORU.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Rapor oluşturuldu: PERSONEL_KARSILASTIRMA_RAPORU.md")

if __name__ == "__main__":
    compare_personnel()
