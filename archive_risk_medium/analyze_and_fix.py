import pandas as pd
from sqlalchemy import create_engine, text
import jellyfish

# Dosya Yolları
DB_PATH = 'sqlite:///ekleristan_local.db'
TXT_PATH = 'personnel_update_20260131.txt'

def normalize_name(name):
    """
    Türkçe karakterleri ve boşlukları normalize eder.
    """
    if not isinstance(name, str):
        return ""
    
    replacements = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'
    }
    name = name.strip().upper()
    for tr, en in replacements.items():
        name = name.replace(tr, en)
    return " ".join(name.split())

def main():
    print("--- Personel Fark Analizi Başlıyor ---")
    
    # 1. Veritabanını Oku
    engine = create_engine(DB_PATH)
    try:
        df_db = pd.read_sql("SELECT * FROM personnel", engine)
        print(f"Veritabanındaki Kayıt Sayısı: {len(df_db)}")
    except Exception as e:
        print(f"Hata: Veritabanı okunamadı - {e}")
        return

    # 2. Text Dosyasını Oku
    try:
        # Tab ile ayrılmış olabilir, veya sabit genişlikli. İçeriğe bakarak tab seperator varsayıyorum veya satır satır okuyup işleyebiliriz.
        # Önceki tool çıktısında: Sno\tAdı Soyadı\t... formatı görülüyordu.
        with open(TXT_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        target_names = []
        for line in lines[1:]: # Başlığı atla
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                # İkinci sütun isim gibi görünüyor, ama indexlere dikkat
                # Örnek satır: 1   ABDALRAOUF...
                # Boşluklarla ayrılmışsa split() yeterli olabilir ama isimde boşluk var.
                # Dosya içeriği tab ile ayrılmış gibi duruyor (kopyalanan excel verisi).
                # Ancak view_file çıktısı sekmeli (tab) yapıyı gösteriyor.
                
                # Split by tab first
                tab_parts = line.strip().split('\t')
                if len(tab_parts) > 1:
                    raw_name = tab_parts[1].strip() # 2. kolon İsim
                    target_names.append(raw_name)
                else:
                     # Tab yoksa çoklu boşluk deneyelim (manual parse)
                     parts = line.strip().split()
                     if len(parts) > 2:
                         # 1 ABDALRAOUF ... PROFITEROL ...
                         # Biraz zorlama olabilir, dosya formatı tab-delimited gibi.
                         pass

        print(f"Dosyadaki Hedef Kişi Sayısı: {len(target_names)}")
        
        if len(target_names) == 0:
            print("UYARI: Dosyadan isim okunamadı! Tab ile ayrıştırma başarısız olmuş olabilir.")
            # Alternatif okuma: Pandas ile
            try:
                df_txt = pd.read_csv(TXT_PATH, sep='\t')
                target_names = df_txt.iloc[:, 1].dropna().astype(str).str.strip().tolist()
                print(f"Pandas ile okunan kişi sayısı: {len(target_names)}")
            except:
                print("Pandas ile de okunamadı.")
                return

    except Exception as e:
        print(f"Hata: Dosya okunamadı - {e}")
        return

    # 3. Karşılaştırma
    db_names_normalized = {normalize_name(name): name for name in df_db['name']}
    target_names_normalized = {normalize_name(name): name for name in target_names}
    
    db_set = set(db_names_normalized.keys())
    target_set = set(target_names_normalized.keys())
    
    missing_in_db = target_set - db_set # Olması gereken ama DB'de olmayan
    extra_in_db = db_set - target_set   # DB'de var ama listede yok (Silinecek adaylar)
    
    print(f"\nVeritabanında OLMAYANlar (Eklenecekler?): {len(missing_in_db)}")
    for n in missing_in_db:
        print(f" - {target_names_normalized[n]}")
        
    print(f"\nVeritabanında FAZLA olanlar (Silinecekler?): {len(extra_in_db)}")
    extras_list = []
    for n in extra_in_db:
        original_name = db_names_normalized[n]
        print(f" - {original_name}")
        # ID'yi bul
        rec = df_db[df_db['name'] == original_name]
        for _, row in rec.iterrows():
             extras_list.append({'id': row['id'], 'name': row['name']})

    # 4. Eşitleme (Kullanıcı onayı istemeden önce raporluyoruz, ama buradaki görev "Eşitle" olduğu için auto-fix opsiyonu ekliyorum)
    # Ancak önce kullanıcıya bir "bak bunlar silinecek" çıktısı vermek daha güvenli, 
    # ama kullanıcı "UYGULA" dediği için ve "4 kişilik farkın nedenini kontrol et ve eşitle" dediği için
    # eğer tam 4 kişi fazlaysa ve missing 0 ise direkt silebiliriz.
    
    if len(missing_in_db) == 0 and len(extra_in_db) > 0:
        print("\n--- OTOMATİK DÜZELTME ---")
        print("Hedef liste veritabanında tam olarak kapsanıyor.")
        print("Fazlalık kayıtlar siliniyor...")
        
        with engine.connect() as conn:
            for item in extras_list:
                print(f"Siliniyor: ID {item['id']} - {item['name']}")
                conn.execute(text("DELETE FROM personnel WHERE id = :id"), {"id": item['id']})
            conn.commit()
            
        print("Silme işlemi tamamlandı.")
        
        # Son Kontrol
        df_final = pd.read_sql("SELECT * FROM personnel", engine)
        print(f"Güncel Veritabanı Kayıt Sayısı: {len(df_final)}")
        
    elif len(missing_in_db) > 0:
        print("\nUYARI: Veritabanında eksikler var! Sadece silme yaparak eşitlemek doğru olmaz.")
        print("Önce eksiklerin eklenmesi, sonra fazlalıkların silinmesi veya isim düzeltmesi gerekebilir.")
        print("Benzerlik kontrolü yapılıyor...")
        
        for missing in missing_in_db:
            best_match = None
            highest_score = 0
            for extra in extra_in_db:
                score = jellyfish.jaro_winkler_similarity(missing, extra)
                if score > 0.85: # Eşik değer
                    if score > highest_score:
                        highest_score = score
                        best_match = extra
            
            if best_match:
                print(f"Olası Eşleşme: '{target_names_normalized[missing]}' <--> '{db_names_normalized[best_match]}' (Skor: {highest_score:.2f})")

if __name__ == "__main__":
    main()
