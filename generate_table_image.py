import matplotlib.pyplot as plt
import pandas as pd

# Create dummy data
data = [
    ["🏛️ ÜST YÖNETİM", "", ""],
    ["  Genel Müdür", "Ahmet YILMAZ", "Genel Müdür"],
    ["🏭 ÜRETİM DİREKTÖRLÜĞÜ", "", ""],
    ["  Üretim Direktörü", "Mehmet KAYA", "Direktör"],
    ["  📍 Hamurhane Bölümü", "", ""],
    ["    Bölüm Sorumlusu", "Ali Veli", "Usta Başı"],
    ["      ↳ Personel", "Ayşe Demir", "Hamurkar"],
    ["      ↳ Personel", "Fatma Çelik", "Yardımcı Eleman"],
    ["  📍 Pişirme Bölümü", "", ""],
    ["    Vardiya Amiri", "Mustafa Öztürk", "Amir"],
    ["      ↳ Personel", "Hasan Can", "Fırıncı"]
]

df = pd.DataFrame(data, columns=["Organizasyon Birimi / Pozisyon", "Ad Soyad", "Görevi / Unvanı"])

fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('tight')
ax.axis('off')

# Table
table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='left')

# Styling
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)

# Header styling
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('#2C3E50')
    elif "ÜST YÖNETİM" in df.iloc[row-1, 0] or "ÜRETİM DİREKTÖRLÜĞÜ" in df.iloc[row-1, 0]:
        cell.set_text_props(weight='bold', color='#1A5276')
        cell.set_facecolor('#EBF5FB')
        if col > 0: cell.set_text_props(text="") # Merge visual effect
    else:
        # Indentation logic visual
        text = df.iloc[row-1, 0]
        if "      " in text:
            cell.set_text_props(color='#555')
        elif "    " in text:
            cell.set_text_props(weight='bold', color='#2E86C1')
        elif "  " in text:
            cell.set_text_props(weight='bold', color='#2874A6')

plt.title("Örnek Tablo Görünümü (PDF Çıktısı)", fontsize=14, pad=20)
plt.savefig("table_preview.png", bbox_inches='tight', dpi=150)
print("Image saved.")
