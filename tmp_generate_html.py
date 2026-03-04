import os

LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"

def generate_base_html(title, doc_no, report_date, period, summary_cards, content, signatures):
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 18mm 15mm 18mm 15mm; }}
  body {{ font-family: Arial, sans-serif; font-size: 11px; color: #333; background: white; margin: 0; padding: 10px; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #8B0000; padding-bottom: 10px; margin-bottom: 14px; auto; }}
  .header-logo img {{ height: 50px; }}
  .header-title {{ text-align: center; }}
  .header-title h1 {{ font-size: 16px; color: #1a2744; margin: 0; }}
  .header-title p {{ margin: 2px 0; font-size: 11px; color: #555; }}
  .header-meta {{ text-align: right; font-size: 10px; color: #555; }}
  .ozet-bar {{ display: flex; gap: 12px; margin-bottom: 14px; width: 100%; }}
  .ozet-kart {{ flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; }}
  .onay {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }}
  .red {{ background: #ffebee; color: #b71c1c; border: 1px solid #b71c1c; }}
  .toplam {{ background: #e3f2fd; color: #1565c0; border: 1px solid #1565c0; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }}
  th {{ background-color: #1a2744; color: white; padding: 6px; text-align: left; border: 1px solid #ccc; }}
  td {{ padding: 6px; border: 1px solid #ccc; }}
  tr:nth-child(even) {{ background-color: #f8f8f8; }}
  tr.highlight-yellow {{ background-color: #fffde7; }}
  .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; display: inline-block; text-align: center; }}
  .bg-green {{ background-color: #2e7d32; color: white; }}
  .bg-red {{ background-color: #b71c1c; color: white; }}
  .bg-orange {{ background-color: #e65100; color: white; }}
  .imza-alani {{ margin-top: 30px; border-top: 2px solid #1a2744; padding-top: 15px; page-break-inside: avoid; }}
  .imza-tablo {{ display: flex; gap: 20px; }}
  .imza-kutu {{ flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa; }}
  .imza-kutu b {{ display: block; color: #1a2744; margin-bottom: 8px; font-size: 11px; }}
  .footer {{ margin-top: 20px; border-top: 1px solid #ccc; padding-top: 8px; display: flex; justify-content: space-between; font-size: 9px; color: #777; }}
  .brc-warning {{ font-weight: bold; color: #b71c1c; font-size: 10px; text-align: center; margin-bottom: 5px; }}
</style>
</head>
<body>
<div class="header">
  <div class="header-logo"><img src="{LOGO_URL}" alt="Logo"></div>
  <div class="header-title">
    <h1>{title}</h1>
    <p>Doküman No: {doc_no}</p>
    <p>Dönem: <b>{period}</b></p>
  </div>
  <div class="header-meta">Sayfa: 1 / 1<br>Rev:02 - 15.01.2026<br>Baskı Tarihi: <b>{report_date}</b></div>
</div>

<div class="ozet-bar">
  {summary_cards}
</div>

{content}

<div class="imza-alani">
  <div class="brc-warning">UYARI: Kritik sapma veya uygunsuzluk durumunda (Kırmızı işaretliler) derhal Kalite Güvence birimine haber veriniz. Ürün karantinaya alınmalıdır.</div>
  <div class="imza-tablo">
    {signatures}
  </div>
</div>

<div class="footer">
  <span>Gizlilik: Dahili Kullanım (BRCGS v9 Uyumlu Form)</span>
  <span>Ekleristan Kalite Yönetim Sistemi v2.0</span>
  <span>Baskı: {report_date}</span>
</div>
</body>
</html>
"""

# ----------------- ÜRETİM RAPORU ÖRNEĞİ -----------------
uretim_cards = """
  <div class="ozet-kart toplam">Toplam Üretim: 12,450 Adet</div>
  <div class="ozet-kart onay">Kabul Edilebilir Fire: %1.2</div>
  <div class="ozet-kart red">Toplam Kritik Fire: 185 Adet</div>
"""
uretim_content = """
<table>
  <thead>
    <tr>
      <th>Saat</th>
      <th>Vardiya</th>
      <th>Ürün</th>
      <th>Çıktı Parti (Lot) No</th>
      <th>Üretim (Adet)</th>
      <th>Fire (Adet)</th>
      <th>Fire Sebebi</th>
      <th>Durum</th>
      <th>Sorumlu Personel</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>08:30</td><td>08:00 - 16:00</td><td>Profiterol</td><td>LOT-260301-P1</td><td>4,500</td><td>45</td><td>Olağan Sürtünme</td><td><span class="badge bg-green">ONAY</span></td><td>Ahmet Yılmaz</td>
    </tr>
    <tr class="highlight-yellow">
      <td>11:15</td><td>08:00 - 16:00</td><td>Çilekli Ekler</td><td>LOT-260301-E1</td><td>3,200</td><td>185</td><td><b>Fırın Isı Sapması (Yanık)</b></td><td><span class="badge bg-red">KRİTİK FİRE</span></td><td>Ayşe Demir</td>
    </tr>
    <tr>
      <td>14:00</td><td>08:00 - 16:00</td><td>Bomba</td><td>LOT-260301-B1</td><td>4,750</td><td>20</td><td>Şekil Bozukluğu</td><td><span class="badge bg-green">ONAY</span></td><td>Mehmet Can</td>
    </tr>
  </tbody>
</table>
"""
uretim_sigs = """
    <div class="imza-kutu"><b>Üretim Sorumlusu</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Vardiya Şefi</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Üretim Müdürü</b><br>Ad Soyad / İmza</div>
"""
with open("C:/Users/GIDA MÜHENDİSİ/.gemini/antigravity/brain/56287005-424d-4275-adae-0ce210a06c48/ornek_uretim_raporu.html", "w", encoding="utf-8") as f:
    f.write(generate_base_html("GÜNLÜK ÜRETİM VE FİRE BEYAN RAPORU", "EKL-URE-001", "01.03.2026 23:45", "01.03.2026", uretim_cards, uretim_content, uretim_sigs))

# ----------------- HİJYEN RAPORU ÖRNEĞİ -----------------
hijyen_cards = """
  <div class="ozet-kart toplam">Kontrol Edilen Personel: 45</div>
  <div class="ozet-kart onay">Uygun: 42</div>
  <div class="ozet-kart red">Uygunsuz / Kusurlu: 3</div>
"""
hijyen_content = """
<table>
  <thead>
    <tr>
      <th>Saat</th>
      <th>Bölüm</th>
      <th>Personel Adı</th>
      <th>Vardiya</th>
      <th>Durum (Kök Neden)</th>
      <th>DÖF / Alınan Aksiyon</th>
      <th>Kontrolör</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>08:05</td><td>İmalathane</td><td>Ahmet Yılmaz</td><td>08:00-16:00</td><td><span class="badge bg-green">Sorun Yok</span></td><td>-</td><td>Zeynep Kalite</td>
    </tr>
    <tr class="highlight-yellow">
      <td>08:10</td><td>Paketleme</td><td>Fatma Şahin</td><td>08:00-16:00</td><td><span class="badge bg-orange">Uygunsuzluk: Oje Tespiti</span></td><td><b>DÖF:</b> Üretim alanından çıkarıldı, oje temizlettirildi. Uyarı formu imzalatıldı.</td><td>Zeynep Kalite</td>
    </tr>
    <tr class="highlight-yellow">
      <td>08:15</td><td>İmalathane</td><td>Ali Kılıç</td><td>08:00-16:00</td><td><span class="badge bg-red">Grip / Ateşli İşçi</span></td><td><b>DÖF:</b> Tesise girişi engellendi, revire yönlendirildi.</td><td>Vardiya Amiri</td>
    </tr>
  </tbody>
</table>
"""
hijyen_sigs = """
    <div class="imza-kutu"><b>Kontrolü Yapan Personel</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Vardiya Amiri</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Kalite Yönetimi</b><br>Ad Soyad / İmza</div>
"""
with open("C:/Users/GIDA MÜHENDİSİ/.gemini/antigravity/brain/56287005-424d-4275-adae-0ce210a06c48/ornek_hijyen_raporu.html", "w", encoding="utf-8") as f:
    f.write(generate_base_html("PERSONEL HİJYEN VE SAĞLIK KONTROL RAPORU", "EKL-KYS-HIJ-002", "01.03.2026 23:45", "01.03.2026", hijyen_cards, hijyen_content, hijyen_sigs))

# ----------------- TEMİZLİK RAPORU ÖRNEĞİ -----------------
temizlik_cards = """
  <div class="ozet-kart toplam">Planlanan Temizlik: 12 Alan</div>
  <div class="ozet-kart onay">Doğrulanan (ATP Dahil): 11</div>
  <div class="ozet-kart red">Eksik / Uygunsuz: 1</div>
"""
temizlik_content = """
<table>
  <thead>
    <tr>
      <th>Saat</th>
      <th>Bölüm</th>
      <th>Alan / Ekipman</th>
      <th>Kimyasal / Dozaj</th>
      <th>Doğrulama Durumu (Kritik)</th>
      <th>ATP Swab (RLU)</th>
      <th>Gerçekleştiren</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>15:30</td><td>İmalathane</td><td>Hamur Karıştırma Mikseri</td><td>Klorlu Köpük (%2)</td><td><span class="badge bg-green">GÖRSEL ONAY</span></td><td><span class="badge bg-green">10 RLU</span> (Limit: <30)</td><td>Mehmet Can</td>
    </tr>
    <tr>
      <td>15:45</td><td>Soğuk Hava</td><td>-18 Donuk Depo Zemin</td><td>Zemin Dezenfektanı (Dozaj pompası)</td><td><span class="badge bg-green">GÖRSEL ONAY</span></td><td>Gerekli Değil</td><td>Ali Kılıç</td>
    </tr>
    <tr class="highlight-yellow">
      <td>16:00</td><td>Paketleme</td><td>Paketleme Bandı Yüzeyi</td><td>Alkol Bazlı Yüzey T. (%70)</td><td><span class="badge bg-red">GÖRSEL RED (Kalıntı)</span></td><td><span class="badge bg-red">140 RLU</span> (Limit Aşımı)</td><td>Fatma Şahin</td>
    </tr>
  </tbody>
</table>
"""
temizlik_sigs = """
    <div class="imza-kutu"><b>Temizliği Yapan Personel</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Vardiya Şefi</b><br>Ad Soyad / İmza</div>
    <div class="imza-kutu"><b>Kalite Doğrulama Uzmanı</b><br>Ad Soyad / İmza</div>
"""
with open("C:/Users/GIDA MÜHENDİSİ/.gemini/antigravity/brain/56287005-424d-4275-adae-0ce210a06c48/ornek_temizlik_raporu.html", "w", encoding="utf-8") as f:
    f.write(generate_base_html("ALAN VE EKİPMAN TEMİZLİK DOĞRULAMA RAPORU", "EKL-KYS-TEM-003", "01.03.2026 23:45", "01.03.2026", temizlik_cards, temizlik_content, temizlik_sigs))

print("Guncel BRC ornekleri basariyla olusturuldu.")
