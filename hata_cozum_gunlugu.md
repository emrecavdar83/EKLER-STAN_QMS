# EKLERİSTAN QMS — Hata Çözüm Günlüğü (2026-03-30)

## v4.3.8 - Şeffaflık ve Stabilizasyon Raporu

Bugün tespit edilen ve kalıcı olarak çözülen kritik hataların dökümü aşağıdadır:

| Referans No | Tarih / Saat | Hata Mesajı / Kök Neden | Uygulanan Teknik Çözüm | Durum |
| :--- | :--- | :--- | :--- | :--- |
| `#N1IH` | 30.03.2026 14:17 | **Bcrypt 72-byte Limit:** Şifre uzunluğu sınırı aşıldı. | `auth_logic.py` içinde 64-byte sabitleme ve zırh eklendi. | ✅ ÇÖZÜLDÜ |
| `#Y6FJ` | 30.03.2026 15:08 | **Navigation Sync:** Sidebar ve menü anahtarları çakıştı. | `app.py` içinde çift yönlü senkronizasyon bariyeri kuruldu. | ✅ ÇÖZÜLDÜ |
| `#3DQI` | 30.03.2026 18:14 | **State Mutation:** Widget çizildikten sonra değer atandı. | Navigasyon sistemi `Index-Controlled` mimariye taşındı. | ✅ ÇÖZÜLDÜ |
| `#0Q5C` | 30.03.2026 18:18 | **Portal Mutation:** Portal butonları kilitlenmeye sebep oldu. | `portal_ui.py` içindeki el yordamı atamalar silindi. | ✅ ÇÖZÜLDÜ |
| `#QWDI` | 30.03.2026 18:57 | **Ghost Rerun:** Streamlit sinyalleri hata sanıldı. | `error_handler.py` filtreleme mantığı güncellendi. | ✅ ÇÖZÜLDÜ |

## 🛠️ Teknik Altyapı Notları

- **Index-Controlled Widget:** Artık navigasyon "zorlama" değil, "indeks" üzerinden akıyor. Bu en güvenli yöntemdir.
- **Transparent Debug:** Hata kutuları artık asıl teknik sebebi de doğrudan gösteriyor.

---

**Hazırlayan:** Antigravity AI | EKLERİSTAN QMS Stabilizasyon Ekibi
