import streamlit as st
import pandas as pd
from ui.hijyen_ui import _hijyen_tablo_hazirla

def run_security_test():
    print("--- HİJYEN MODÜLÜ STATE GÜVENLİK TESTİ ---")
    
    # 1. Başlangıç Durumu Simülasyonu
    print("\nSENARYO 1: İlk Yükleme (Boş State)")
    if 'hijyen_tablo' in st.session_state:
        del st.session_state['hijyen_tablo']
    if 'son_bolum' in st.session_state: del st.session_state['son_bolum']
    if 'son_vardiya' in st.session_state: del st.session_state['son_vardiya']

    personel_rulo_gunduz = ["ALİCAN ALİ", "MİHRİMAH ALİ"]
    
    res1 = _hijyen_tablo_hazirla(personel_rulo_gunduz, "RULO PASTA", "GÜNDÜZ VARDİYASI")
    print(f"[BAŞARILI] Tablo oluşturuldu, satır sayısı: {len(res1)}")
    assert len(res1) == 2
    assert st.session_state.son_bolum == "RULO PASTA"
    assert st.session_state.son_vardiya == "GÜNDÜZ VARDİYASI"
    
    # 2. Kullanıcı veri girdi ama vardiya değiştirdi (Kaza Senaryosu)
    print("\nSENARYO 2: Veri Kaybı Koruma (Dirty State + Geçiş)")
    # Manuel olarak state'i "kirletiyoruz"
    st.session_state.hijyen_tablo.loc[0, "Durum"] = "Gelmedi" 
    
    personel_rulo_gece = ["MUHAP KAHPEVAR"]
    res2 = _hijyen_tablo_hazirla(personel_rulo_gece, "RULO PASTA", "GECE VARDİYASI")
    
    # Tablonun sıfırlanmamış, eski personellerin kalmış olması lazım
    personeller_res2 = res2["Personel Adı"].tolist()
    print(f"Dönen Tablodaki Personeller: {personeller_res2}")
    if "ALİCAN ALİ" in personeller_res2 and len(res2) == 2:
        print("[BAŞARILI] Koruma mekanizması çalıştı. Tablo sıfırlanmadı.")
    else:
        print("[HATA] Veri kaybı oldu! Tablo sıfırlandı.")
        
    assert "ALİCAN ALİ" in personeller_res2

    # 3. Temiz formda vardiya değiştirme (Normal Senaryo)
    print("\nSENARYO 3: Temiz Formda Dinamik Yükleme")
    # State'i temizleyelim
    st.session_state.hijyen_tablo["Durum"] = "Sorun Yok"
    
    res3 = _hijyen_tablo_hazirla(personel_rulo_gece, "RULO PASTA", "GECE VARDİYASI")
    personeller_res3 = res3["Personel Adı"].tolist()
    print(f"Dönen Tablodaki Personeller: {personeller_res3}")
    
    if "MUHAP KAHPEVAR" in personeller_res3 and len(res3) == 1:
        print("[BAŞARILI] Temiz formda liste yeni vardiyaya başarıyla güncellendi.")
    else:
        print("[HATA] Yeni personeller yüklenemedi!")
        
    assert "MUHAP KAHPEVAR" in personeller_res3
    
    print("\n✅ TÜM GÜVENLİK TESTLERİ (13. ADAM RİSK ANALİZİ) BAŞARIYLA GEÇİLDİ.")

if __name__ == "__main__":
    # Streamlit ortamını simüle etmek için dummy session_state objesi oluştur
    class DummySessionState(dict):
        def __getattr__(self, name):
            if name in self:
                return self[name]
            raise AttributeError(f"No attribute {name}")
        def __setattr__(self, name, value):
            self[name] = value

    st.session_state = DummySessionState()
    
    # Dummy warning function
    st.warning = lambda msg: print(f"*** STREAMLIT UYARISI EKRANA BASILDI: {msg} ***")
    
    run_security_test()
