# -*- coding: utf-8 -*-
"""Ürün tablosu analizi"""
import sqlite3
import os

os.chdir(r"c:\Projeler\S_program\EKLERİSTAN_QMS")

print("=== LOKAL VERITABANI ANALİZİ ===\n")

conn = sqlite3.connect("ekleristan.db")
cur = conn.cursor()

# Tabloları listele
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Mevcut tablolar:")
for t in tables:
    print(f"  - {t[0]}")

print("\n--- ayarlar_urunler Tablo Yapısı ---")
cur.execute("PRAGMA table_info(ayarlar_urunler)")
cols = cur.fetchall()
if cols:
    for c in cols:
        print(f"  {c[1]:25} ({c[2]})")
else:
    print("  TABLO YOK!")

print("\n--- Ürün Örnekleri (İlk 20) ---")
try:
    cur.execute("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler LIMIT 20")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  {r[0]:30} -> {r[1]}")
    else:
        print("  VERİ YOK!")
except Exception as e:
    print(f"  HATA: {e}")

# RULO PASTA kontrolü
print("\n--- RULO PASTA ile İlgili Ürünler ---")
try:
    cur.execute("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE sorumlu_departman LIKE '%RULO%'")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  {r[0]:30} -> {r[1]}")
    else:
        print("  Bulunamadı!")
except Exception as e:
    print(f"  HATA: {e}")

conn.close()
