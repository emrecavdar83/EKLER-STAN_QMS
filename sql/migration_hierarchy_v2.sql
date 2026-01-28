-- Migration Plan for Hierarchy Refactor
-- Goal: Insert 'Koordinatör' at Level 4.
-- Shift existing levels down by 1 where level >= 4.

-- 1. Shift 'Stajyer / Çırak' (6) to 7
UPDATE personel SET pozisyon_seviye = 7 WHERE pozisyon_seviye = 6;

-- 2. Shift 'Personel' (5) to 6
UPDATE personel SET pozisyon_seviye = 6 WHERE pozisyon_seviye = 5;

-- 3. Shift old 'Şef / Sorumlu / Koordinatör' (4) to 'Şef / Sorumlu' (5)
-- We default them to 5. The user will manually promote Coordinators to 4.
UPDATE personel SET pozisyon_seviye = 5 WHERE pozisyon_seviye = 4;
