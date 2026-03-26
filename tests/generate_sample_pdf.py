import sys
import os
sys.path.insert(0, '.')

from modules.qdms.pdf_uretici import pdf_uret

veri = {
    'belge_adi': 'GENEL HİJYEN VE SANİTASYON PROSEDÜRÜ',
    'belge_tipi': 'PR',
    'yonu': 'dikey',
    'rev_no': '01',
    'donem': 'Mart 2026',
    'ilk_yayin_tarihi': '20.03.2026',
    'rev_tarihi': '26.03.2026',
    'amac': (
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
        'Bu prosedürün amacı, EKLERİSTAN A.Ş. üretim tesislerinde hijyen ve '
        'sanitasyon faaliyetlerinin sistematik biçimde yürütülmesini sağlamak, '
        'gıda güvenliği risklerini asgariye indirmek ve BRCGS v9 ile IFS v8 '
        'gerekliliklerine tam uyumu temin etmektir.'
    ),
    'kapsam': (
        'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium. '
        'Bu prosedür; tüm üretim, paketleme ve depolama alanlarını kapsar. '
        'Tüm vardiya personeli ve ziyaretçiler için bağlayıcıdır.'
    ),
    'tanimlar': (
        'Hijyen: Mikroorganizmaların yayılmasını önleyen uygulamalar.\n'
        'Sanitasyon: Yüzeylerin temizlenmesi ve dezenfekte edilmesi süreci.\n'
        'CCP (Kritik Kontrol Noktası): Risklerin kontrol altına alındığı adım.'
    ),
    'icerik': (
        '4.1 GENEL KURALLAR\n'
        'Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam. '
        'Personel el yıkama istasyonlarını (EKL-FR-022) talimatlara uygun kullanmalıdır.\n\n'
        '4.2 TEMİZLİK PROGRAMI\n'
        'At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium. '
        'Tüm ekipmanlar vardiya bitiminde dezenfekte edilmelidir.'
    ),
    'dokumanlar': (
        'EKL-TL-011 — El Yıkama Talimatı\n'
        'EKL-FR-022 — Hijyen Kontrol Formu\n'
        'BRCGS v9 Madde 4.11'
    ),
    'imzalar': [
        {'rol': 'Hazırlayan', 'ad_soyad': 'Antigravity S1-Builder', 'gorev': 'AI Ajanı', 'tarih': '26.03.2026'},
        {'rol': 'Kontrol Eden', 'ad_soyad': 'EKLERİSTAN Auditor', 'gorev': 'Kalite Müdürü', 'tarih': '26.03.2026'},
        {'rol': 'Onaylayan', 'ad_soyad': 'MEHMET YILMAZ', 'gorev': 'Genel Müdür', 'tarih': '26.03.2026'},
    ],
    'satirlar': []
}

pdf_out = 'EKLERISTAN_ORNEK_DIKEY_BELGE.pdf'
out = pdf_uret(None, 'EKL-PR-001', veri, pdf_out)
print(f'PDF_SUCCESS: {os.path.abspath(out)}')
