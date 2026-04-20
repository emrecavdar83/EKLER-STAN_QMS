# BUG FIX: Personnel Save Silent Error (Foreign Key Violation)

**Issue:** Personnel edit form ("Personel Ekle/Düzenle" tab) would throw database error during save operation but error message was not displayed to user.

**User Report:** 
- "PERSONEL EKLE DÜZENLE SEKMESİNDE MEVCUT PERSONEL DÜZELTME SEGMESİ KAYIT İŞLEMİNDE ATIYOR"
- "HATA MESAJI VERMİYOR" (No error message displayed)

**Root Cause Analysis:**
When user selected "- Yok -" (None) for optional manager/supervisor fields, the form was passing:
- `yonetici_id = 0`
- `operasyonel_bolum_id = 0`
- `ikincil_yonetici_id = 0`

The `personel` table has foreign key constraints on these columns that require either:
1. Valid record ID from the `personel` table, OR
2. NULL value

The value 0 is rejected by both constraints.

**Database Schema:**
```sql
personel (
  yonetici_id INTEGER,  -- FK to personel(id)
  operasyonel_bolum_id INTEGER,  -- FK to personel(id)
  ikincil_yonetici_id INTEGER    -- FK to personel(id)
)
```

**Error Message (from database):**
```
sqlalchemy.exc.IntegrityError: 
  insert or update on table "personel" violates foreign key constraint 
  "personel_yonetici_id_fkey"
  DETAIL: Key (yonetici_id)=(0) is not present in table "personel".
```

**Solution Implemented:**
Modified `_personel_form_kaydet_tetikle()` function in `ui/ayarlar/personel_ui.py`:
- Convert 0 → NULL for optional foreign key fields before passing to database
- Enhanced error handling already in place (st.error + st.warning) will now properly display the error if it occurs

**Code Changes:**
```python
# Before:
"y": robust_id_clean(hiyerarşi['yonetici_id']),
"ob": robust_id_clean(saha['oper_dept_id']),
"iy": robust_id_clean(saha['sec_yon_id']),

# After:
"y": robust_id_clean(hiyerarşi['yonetici_id']) or None,
"ob": robust_id_clean(saha['oper_dept_id']) or None,
"iy": robust_id_clean(saha['sec_yon_id']) or None,
```

**Testing:**
- Created diagnostic test: `scratch/test_personel_save.py`
- Verified: INSERT succeeds with NULL values
- Verified: INSERT fails with 0 values (as expected)
- All test suite runs still pass

**Files Modified:**
- `ui/ayarlar/personel_ui.py` (line 222-231: parameter preparation)

**Impact:**
- Personnel records can now be saved successfully
- Optional manager/supervisor fields properly handle "- Yok -" selection
- Error messages now properly displayed if other database errors occur

**Commit:** cbc760d
