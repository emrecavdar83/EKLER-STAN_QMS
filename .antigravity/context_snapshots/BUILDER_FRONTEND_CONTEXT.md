# DOC_CONTEXT — BUILDER_FRONTEND
Oluşturma: 2026-03-30 05:06
İlgili kütüphaneler: python, streamlit, reportlab
============================================================

## STREAMLIT — v1.43.0
### Kritik Özellikler
- st.session_state: Global durum yönetimi (Oturum takibi)
- st.cache_data / st.cache_resource: Performans optimizasyonu
- st.form / st.form_submit_button: Batch veri girişi (Bart Simpson Döngüsü uyarısı)
- st.tabs: Modül içi sekme yapısı (Anayasa Madde 19)
- st.rerun: Akış kontrolü ve sayfa yenileme

### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ Anayasa Madde 19: Tüm UI elementleri render_* fonksiyonu içinde kapsüllenmelidir.
- ⚠️ Anayasa Madde 23: st.form key'leri duplicate hatasını önlemek için benzersiz olmalıdır.

### Hallüsinasyon Tuzakları (Kaçınılacaklar)
- ❌ Eski st.experimental_rerun() yerine st.rerun() kullanılmalıdır.
- ❌ st.cache yerine yeni st.cache_data/resource API'ları zorunludur.

## REPORTLAB — v4.4.10
### EKLERİSTAN Kalıpları (Zorunlu)
- ⚠️ UTF-8 Türkçe karakter sorunu için harici font dosyaları static/fonts/ altından yüklenir.
- ❌ ReportLab 4.x ile 3.x arasındaki bazı import yapıları değişmiştir.
