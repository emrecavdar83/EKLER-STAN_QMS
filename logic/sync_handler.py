import streamlit as st
import time
from sqlalchemy import text
from database.connection import get_engine
from scripts.sync_manager import SyncManager

# Veritabanı motoru
engine = get_engine()

def render_sync_button(key_prefix="global"):
    """Ayarlar modülü için GÜVENLİ (Upsert) Lokal -> Cloud senkronizasyon butonu"""
    st.markdown("---")
    col_sync1, col_sync2 = st.columns([3, 1])
    with col_sync1:
        st.info("💡 **Akıllı Cloud Sync:** Lokalde yaptığınız değişiklikleri (Yeni ve Güncellenen) canlı sisteme güvenle aktarır. Mevcut verileri silmez.")
        # EŞSİZ KEY: key_prefix ile checkbox ID çakışmasını önle
        dry_run = st.checkbox("Simülasyon Modu (Değişiklik yapmadan test et)", value=False, key=f"{key_prefix}_dry_run")

    with col_sync2:
        btn_label = "🔍 Test Et" if dry_run else "🚀 Canlıya Gönder"
        btn_type = "secondary" if dry_run else "primary"

        # Button key sabit olmalı (time based olmamalı yoksa tıklandığında algılamaz)
        if st.button(btn_label, key=f"{key_prefix}_btn_sync", type=btn_type, use_container_width=True):
            # 1. Ortam Kontrolü
            is_local = 'sqlite' in str(engine.url)
            if not is_local:
                st.warning("⚠️ Zaten Bulut/Canlı veritabanına bağlısınız. Bu işlem sadece Lokalde çalışır.")
                return

            # 3. İşlem Başlat
            mode_text = "SİMÜLASYON" if dry_run else "CANLI AKTARIM"
            with st.status(f"🚀 {mode_text} Başlatılıyor...", expanded=True) as status:
                try:
                    status.write("☁️ Bağlantılar kontrol ediliyor...")

                    # Context Manager ile SyncManager başlat (Otomatik kapanır)
                    with SyncManager() as manager:
                        # Full Sync Çalıştır
                        results = manager.run_full_sync(dry_run=dry_run)

                        total_inserted = 0
                        total_updated = 0

                        for table, res in results.items():
                            if "error" in res:
                                status.write(f"❌ {table}: Hata - {res['message']}")
                                continue
                            
                            # SycnManager v2.1 returns {"pull": ..., "push": ...}
                            push_stats = res.get('push', res) if isinstance(res, dict) else {}
                            
                            if push_stats.get('status') == 'skipped' or res.get('status') == 'skipped':
                                 pass
                            else:
                                ins = push_stats.get('inserted', 0)
                                upd = push_stats.get('updated', 0)
                                total_inserted += ins
                                total_updated += upd

                                if ins > 0 or upd > 0:
                                    status.write(f"📦 {table}: +{ins} Yeni, ✏️ {upd} Güncelleme")
                                else:
                                    status.write(f"✅ {table}: Güncel")

                        status.update(label=f"✅ {mode_text} Tamamlandı!", state="complete", expanded=True)

                        if dry_run:
                            st.info(f"🧪 SİMÜLASYON SONUCU: Toplam **{total_inserted}** yeni kayıt eklenecek, **{total_updated}** kayıt güncellenecek.")
                        else:
                            st.success(f"🎉 İşlem Başarılı! Toplam **{total_inserted}** yeni kayıt eklendi, **{total_updated}** kayıt güncellendi.")
                            st.cache_data.clear() # Cache'i temizle ki yeni veriler anında görünsün
                            if total_inserted > 0 or total_updated > 0:
                                st.toast("Veri transferi başarılı!", icon="✅")
                                time.sleep(1)
                                st.rerun() # Ekranı yenile

                except Exception as e:
                    status.update(label="❌ Genel Hata", state="error")
                    st.error(f"Beklenmeyen hata: {e}")
