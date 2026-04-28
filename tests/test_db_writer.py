"""
test_db_writer.py — Görev 1.1: Çift fetchone() bug fix doğrulama testleri.

Bu testler db_writer.py:40-41 ve :75-77'deki düzeltmeleri doğrular.
Fix öncesinde KIRMIZI, fix sonrasında YEŞİL olmalıdır.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestGuvenliKayitEkle:
    """guvenli_kayit_ekle fonksiyonundaki fetchone düzeltmesini test eder."""

    @patch("logic.db_writer.clear_personnel_cache")
    @patch("logic.db_writer.log_field_change")
    @patch("database.connection.get_engine")
    def test_kpi_insert_returns_valid_id(self, mock_get_engine, mock_log, mock_cache):
        """
        KPI kaydı sonrası RETURNING id ile dönen ID'nin doğru alındığını
        ve log_field_change'in çağrıldığını doğrular.
        """
        # Mock cursor result: RETURNING id → 42
        mock_row = (42,)
        mock_result = MagicMock()
        # Düzeltilmiş kodda fetchone() yalnızca 1 kez çağrılır
        mock_result.fetchone = MagicMock(return_value=mock_row)

        mock_conn = MagicMock()
        mock_conn.execute = MagicMock(return_value=mock_result)
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        mock_engine = MagicMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_get_engine.return_value = mock_engine

        # 21 elemanlı KPI veri tuple'ı
        veri = (
            "2026-04-28", "10:00", "Sabah", "Peynir", "LOT001",
            "LOT001", "STT01", "NUM01",
            1.5, 2.0, 1.8,          # ölçümler
            "UYGUN", "1",            # karar, kullanici
            None, None, None,       # pad
            "iyi", "güzel", "not",   # tat, görüntü, notlar
            None, None              # foto yolları
        )

        from logic.db_writer import guvenli_kayit_ekle
        result = guvenli_kayit_ekle("Urun_KPI_Kontrol", veri)

        # Fonksiyon True dönmeli (kayıt başarılı)
        assert result is True, "guvenli_kayit_ekle başarısız döndü"

        # KRİTİK: log_field_change çağrılmış olmalı (kpi_id None değilse çağrılır)
        assert mock_log.called, (
            "log_field_change çağrılmadı! "
            "kpi_id None → audit trail kayıp."
        )

    @patch("logic.db_writer.clear_personnel_cache")
    @patch("logic.db_writer.log_field_change")
    @patch("database.connection.get_engine")
    def test_kpi_insert_audit_trail_has_correct_id(self, mock_get_engine, mock_log, mock_cache):
        """
        log_field_change'e gönderilen kpi_id'nin doğru değeri (42) taşıdığını doğrular.
        """
        mock_row = (42,)
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=mock_row)

        mock_conn = MagicMock()
        mock_conn.execute = MagicMock(return_value=mock_result)
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        mock_engine = MagicMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_get_engine.return_value = mock_engine

        veri = (
            "2026-04-28", "10:00", "Sabah", "Peynir", "LOT001",
            "LOT001", "STT01", "NUM01",
            1.5, 2.0, 1.8,
            "UYGUN", "1",
            None, None, None,
            "iyi", "güzel", "not",
            None, None
        )

        from logic.db_writer import guvenli_kayit_ekle
        guvenli_kayit_ekle("Urun_KPI_Kontrol", veri)

        assert mock_log.called, "log_field_change çağrılmadı"
        call_args = mock_log.call_args
        actual_id = call_args[0][2]  # 3. pozisyonel parametre = record ID
        assert actual_id == 42, (
            f"Audit trail'e gönderilen ID {actual_id}, beklenen 42."
        )


class TestGuvenliCokluKayitEkle:
    """guvenli_coklu_kayit_ekle fonksiyonundaki fetchone düzeltmesini test eder."""

    @patch("logic.db_writer.log_field_change")
    @patch("database.connection.get_engine")
    def test_hijyen_batch_logs_audit_trail(self, mock_get_engine, mock_log):
        """
        Her hijyen kaydı için audit trail yazılmasını doğrular.
        3 kayıt → 3 audit log çağrısı.
        """
        # Her insert için ayrı mock result (her biri 1 kez fetchone çağrılacak)
        def make_mock_result(row_id):
            mock_result = MagicMock()
            mock_result.fetchone = MagicMock(return_value=(row_id,))
            return mock_result

        mock_conn = MagicMock()
        mock_conn.execute = MagicMock(
            side_effect=[make_mock_result(101), make_mock_result(102), make_mock_result(103)]
        )
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        mock_engine = MagicMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_get_engine.return_value = mock_engine

        # 3 hijyen kaydı
        veri_listesi = [
            ("2026-04-28", "08:00", "admin", "Sabah", "Uretim", "Ali", "UYGUN", "", ""),
            ("2026-04-28", "08:01", "admin", "Sabah", "Uretim", "Veli", "UYGUN", "", ""),
            ("2026-04-28", "08:02", "admin", "Sabah", "Uretim", "Ayse", "UYGUNSUZ", "Eldiven yok", "Uyari"),
        ]

        from logic.db_writer import guvenli_coklu_kayit_ekle
        result = guvenli_coklu_kayit_ekle("Hijyen_Kontrol_Kayitlari", veri_listesi)

        assert result is True, "guvenli_coklu_kayit_ekle basarisiz dondu"

        # 3 kayıt için 3 audit log çağrısı olmalı
        assert mock_log.call_count == 3, (
            f"Beklenen 3 audit log cagrisi, gerceklesen {mock_log.call_count}."
        )


class TestImportTemizlik:
    """db_writer.py'deki tekrar import ve erişilmez kod tespiti."""

    def test_tekrar_import_yok(self):
        """'from sqlalchemy import text' yalnızca 1 kez olmalı."""
        import inspect
        from logic import db_writer
        source = inspect.getsource(db_writer)

        import_count = source.count("from sqlalchemy import text")
        assert import_count == 1, (
            f"'from sqlalchemy import text' {import_count} kez bulundu, 1 olmali."
        )

    def test_erisilemez_return_yok(self):
        """guvenli_coklu_kayit_ekle'de fazladan erisilemez return False olmamali."""
        import inspect
        from logic import db_writer
        func_source = inspect.getsource(db_writer.guvenli_coklu_kayit_ekle)

        # except blokundaki return False + basi guard (if not veri_listesi: return False) = max 2
        # try icerisindeki return True ve except'teki return False + guard = 2 return False kabul edilir
        # try disinda 3. bir return False → erisilemez kod
        return_false_count = func_source.count("return False")
        assert return_false_count <= 2, (
            f"guvenli_coklu_kayit_ekle'de {return_false_count} adet 'return False' var. "
            f"Fazla olan erisilemez koddur."
        )
