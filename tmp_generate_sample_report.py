import os

def generate_sample_html():
    sample_html = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Soğuk Oda Raporu Taslağı</title>
<style>
  @page { size: A4; margin: 18mm 15mm 18mm 15mm; }
  @media print { 
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } 
      .page-break { page-break-after: always; }
      .no-print { display: none; }
  }
  body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #333; background: #f4f6f9; margin: 0; padding: 20px; }
  .a4-container { background: white; margin: 0 auto 20px auto; padding: 18mm 15mm; width: 210mm; min-height: 297mm; box-shadow: 0 0 10px rgba(0,0,0,0.1); box-sizing: border-box; position: relative; }
  
  .header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 3px solid #1a2744; padding-bottom: 10px; margin-bottom: 20px; }
  .header-logo img { height: 45px; }
  .header-title { text-align: center; flex-grow: 1; }
  .header-title h1 { font-size: 18px; color: #1a2744; margin: 0 0 5px 0; letter-spacing: 0.5px; }
  .header-title h2 { font-size: 14px; color: #c62828; margin: 0; font-weight: bold; }
  .header-meta { text-align: right; font-size: 10px; color: #666; line-height: 1.4; }
  
  .info-bar { display: flex; justify-content: space-between; background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px 15px; margin-bottom: 20px; }
  .info-item { display: flex; flex-direction: column; }
  .info-label { font-size: 9px; color: #777; text-transform: uppercase; font-weight: bold; margin-bottom: 3px; }
  .info-value { font-size: 12px; color: #1a2744; font-weight: bold; }
  
  table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }
  th { background-color: #1a2744; color: white; padding: 8px; text-align: center; border: 1px solid #d0d0d0; font-weight: bold; }
  td { padding: 8px; border: 1px solid #d0d0d0; text-align: center; vertical-align: middle; }
  tr:nth-child(even) { background-color: #f9fbfd; }
  
  .badge { padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; display: inline-block; }
  .bg-green { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
  .bg-red { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
  .bg-gray { background-color: #f5f5f5; color: #757575; border: 1px solid #e0e0e0; }
  
  .deviation-box { margin-top: 15px; border-left: 4px solid #c62828; background: #fff5f5; padding: 12px 15px; border-radius: 0 6px 6px 0; }
  .deviation-title { color: #c62828; font-size: 12px; font-weight: bold; margin-bottom: 8px; display: flex; align-items: center; gap: 5px; }
  .deviation-list { margin: 0; padding-left: 20px; color: #333; font-size: 11px; line-height: 1.6; }
  .deviation-list li span.val { font-weight: bold; color: #c62828; }
  
  .imza-alani { position: absolute; bottom: 30px; left: 15mm; right: 15mm; }
  .imza-tablo { display: flex; gap: 15px; }
  .imza-kutu { flex: 1; border: 1px dashed #bbb; border-radius: 6px; padding: 10px 10px 45px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa; }
  .imza-kutu b { display: block; color: #1a2744; margin-bottom: 12px; font-size: 11px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
  
  .footer { position: absolute; bottom: 10px; left: 15mm; right: 15mm; border-top: 1px solid #e0e0e0; padding-top: 5px; display: flex; justify-content: space-between; font-size: 8px; color: #999; }
</style>
</head>
<body>

<div class="no-print" style="text-align:center; padding: 10px; background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; border-radius: 6px; margin-bottom: 20px; font-weight: bold;">
    ℹ️ Bu bir PDF önizlemesidir. Yazdırıldığında veya PDF yapıldığında arkaplan silinir; her oda 1 adet şık A4 sayfasına sığar.
</div>

<!-- ODA 1 SAYFASI -->
<div class="a4-container page-break">
  <div class="header">
    <div class="header-logo"><img src="https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png" alt="Logo"></div>
    <div class="header-title">
      <h1>SOĞUK ODA İZLEME FORMU</h1>
      <h2>Rulo Pasta Odası (-20°C)</h2>
    </div>
    <div class="header-meta">
      Doküman: EKL-SO-004<br>
      Rev: 03 - 15.01.2026<br>
      Baskı: 07.03.2026 09:45
    </div>
  </div>

  <div class="info-bar">
    <div class="info-item">
      <span class="info-label">İzleme Tarihi</span>
      <span class="info-value">06.03.2026</span>
    </div>
    <div class="info-item">
      <span class="info-label">Hedef Sıcaklık Aralığı</span>
      <span class="info-value">-22.0°C ile -18.0°C arası</span>
    </div>
    <div class="info-item">
      <span class="info-label">Günlük Kayıt Durumu</span>
      <span class="info-value" style="color:#c62828;">⚠️ 1 Sapma Tespit Edildi</span>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th width="12%">Ölçüm Saati</th>
        <th width="15%">Ölçülen Değer</th>
        <th width="15%">Durum</th>
        <th width="20%">Sorumlu Personel</th>
        <th width="38%">Uygulayıcı Notu</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>08:00</td>
        <td>-19.5 °C</td>
        <td><span class="badge bg-green">Uygun</span></td>
        <td>Ayşegül Tetik</td>
        <td>-</td>
      </tr>
      <tr>
        <td>12:00</td>
        <td>-20.2 °C</td>
        <td><span class="badge bg-green">Uygun</span></td>
        <td>Ayşegül Tetik</td>
        <td>-</td>
      </tr>
      <tr>
        <td>16:00</td>
        <td><span style="color:#c62828; font-weight:bold;">-16.4 °C</span></td>
        <td><span class="badge bg-red">Sapma</span></td>
        <td>Ayşegül Tetik</td>
        <td>Kapı açık unutulmuş, kapatılarak müdahale edildi.</td>
      </tr>
      <tr>
        <td>20:00</td>
        <td>-</td>
        <td><span class="badge bg-gray">Gecikti</span></td>
        <td>-</td>
        <td>-</td>
      </tr>
    </tbody>
  </table>

  <div class="deviation-box">
    <div class="deviation-title">🚨 Kritik Sapma Raporu</div>
    <ul class="deviation-list">
      <li>Saat <b>16:00</b> itibarıyla ölçülen <span class="val">-16.4 °C</span> değeri, belirlenen maksimum (-18.0 °C) limitini aştığı için Kalite Güvence birimine bilgi verilmelidir.</li>
    </ul>
  </div>

  <div class="imza-alani">
    <div style="font-weight: bold; color: #c62828; font-size: 10px; text-align: center; margin-bottom: 8px;">UYARI: Kritik sapma durumunda BRCGS prosedürlerine göre DÖF başlatılmalıdır.</div>
    <div class="imza-tablo">
      <div class="imza-kutu"><b>Ölçümü Yapan Personel(ler)</b>İsim / İmza</div>
      <div class="imza-kutu"><b>Kalite Kontrol Sorumlusu</b>İsim / İmza / Onay</div>
      <div class="imza-kutu"><b>İşletme/Üretim Müdürü</b>İsim / İmza / Onay</div>
    </div>
  </div>
  
  <div class="footer">
    <span>Gizlilik: Dahili Kullanım (BRCGS v9 Uyumlu Form)</span>
    <span>Ekleristan Kalite Yönetim Sistemi v3.0</span>
    <span>Sayfa: 1/2</span>
  </div>
</div>

<!-- ODA 2 SAYFASI -->
<div class="a4-container page-break">
  <div class="header">
    <div class="header-logo"><img src="https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png" alt="Logo"></div>
    <div class="header-title">
      <h1>SOĞUK ODA İZLEME FORMU</h1>
      <h2>Ham Madde Odası (+4°C)</h2>
    </div>
    <div class="header-meta">
      Doküman: EKL-SO-004<br>
      Rev: 03 - 15.01.2026<br>
      Baskı: 07.03.2026 09:45
    </div>
  </div>

  <div class="info-bar">
    <div class="info-item">
      <span class="info-label">İzleme Tarihi</span>
      <span class="info-value">06.03.2026</span>
    </div>
    <div class="info-item">
      <span class="info-label">Hedef Sıcaklık Aralığı</span>
      <span class="info-value">+2.0°C ile +8.0°C arası</span>
    </div>
    <div class="info-item">
      <span class="info-label">Günlük Kayıt Durumu</span>
      <span class="info-value" style="color:#2e7d32;">✅ Tümü Uygun</span>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th width="12%">Ölçüm Saati</th>
        <th width="15%">Ölçülen Değer</th>
        <th width="15%">Durum</th>
        <th width="20%">Sorumlu Personel</th>
        <th width="38%">Uygulayıcı Notu</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>10:00</td>
        <td>+4.5 °C</td>
        <td><span class="badge bg-green">Uygun</span></td>
        <td>Zilan Çiftçi</td>
        <td>-</td>
      </tr>
      <tr>
        <td>18:00</td>
        <td>+5.1 °C</td>
        <td><span class="badge bg-green">Uygun</span></td>
        <td>Zilan Çiftçi</td>
        <td>Ürün girişinden hemen sonra.</td>
      </tr>
    </tbody>
  </table>

  <div class="imza-alani">
    <div class="imza-tablo">
      <div class="imza-kutu"><b>Ölçümü Yapan Personel(ler)</b>İsim / İmza</div>
      <div class="imza-kutu"><b>Kalite Kontrol Sorumlusu</b>İsim / İmza / Onay</div>
      <div class="imza-kutu"><b>İşletme/Üretim Müdürü</b>İsim / İmza / Onay</div>
    </div>
  </div>
  
  <div class="footer">
    <span>Gizlilik: Dahili Kullanım (BRCGS v9 Uyumlu Form)</span>
    <span>Ekleristan Kalite Yönetim Sistemi v3.0</span>
    <span>Sayfa: 2/2</span>
  </div>
</div>

</body>
</html>
    """
    with open('ornek_soguk_oda_coklu_sayfa.html', 'w', encoding='utf-8') as f:
        f.write(sample_html)
    print("Örnek HTML dosyası oluşturuldu.")

if __name__ == "__main__":
    generate_sample_html()
