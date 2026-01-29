-- Rename 'KEK' to 'PANDİSPANYA' in department names
-- Case-insensitive match usually requires LIKE with %

-- 1. Exact Match update
UPDATE ayarlar_bolumler SET bolum_adi = REPLACE(bolum_adi, 'KEK', 'PANDİSPANYA') WHERE bolum_adi LIKE '%KEK%';
UPDATE ayarlar_bolumler SET bolum_adi = REPLACE(bolum_adi, 'Kek', 'PANDİSPANYA') WHERE bolum_adi LIKE '%Kek%';
UPDATE ayarlar_bolumler SET bolum_adi = REPLACE(bolum_adi, 'kek', 'PANDİSPANYA') WHERE bolum_adi LIKE '%kek%';

-- Also check uppercase/lowercase variations explicitly if needed
