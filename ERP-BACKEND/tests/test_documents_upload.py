"""
Unit tests for the document upload endpoint (app/routers/documents.py).

Covers the security-hardening changes introduced in this PR:
- Reading and validating file content via `validate_file_upload` before persisting
- Rejecting invalid/unsafe uploads with a 400 and the validator's error message
- Storing the sanitized filename (not the raw client-supplied filename)
- Deriving MIME type from the filename via `mimetypes.guess_type` instead of
  trusting the client-supplied `content_type`
- Writing the already-read file content directly instead of streaming via `shutil`
"""
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

# `app.routers.documents` imports `validate_file_upload` from
# `app.services.security_utils`. If that module isn't available in the
# environment under test, stub it out so the module under test can still be
# imported; individual tests patch `documents.validate_file_upload` directly
# so the stub's own behavior is irrelevant.
try:
    import app.services.security_utils  # noqa: F401
except ModuleNotFoundError:
    _stub = MagicMock()
    _stub.validate_file_upload = MagicMock(return_value=(True, None, "stub.txt"))
    sys.modules["app.services.security_utils"] = _stub

from fastapi import HTTPException

from app.routers import documents


pytestmark = pytest.mark.asyncio


class FakeUploadFile:
    """Minimal stand-in for FastAPI's UploadFile for direct function testing."""

    def __init__(self, filename, content, content_type="application/octet-stream"):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


class TestUploadDocumentValidation:
    """Tests for input validation performed by upload_document."""

    async def test_missing_filename_raises_400_before_reading_content(self, db_session):
        file = FakeUploadFile(filename="", content=b"irrelevant")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload") as mock_validate:
            with pytest.raises(HTTPException) as exc_info:
                await documents.upload_document(
                    file=file, entity_type=None, entity_id=None, title=None,
                    db=db_session, current_user=user,
                )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No file provided"
        mock_validate.assert_not_called()

    async def test_invalid_file_raises_400_with_validator_error_message(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="malware.exe", content=b"MZ-fake-binary")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(False, "File type not allowed", None)):
            with pytest.raises(HTTPException) as exc_info:
                await documents.upload_document(
                    file=file, entity_type=None, entity_id=None, title=None,
                    db=db_session, current_user=user,
                )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "File type not allowed"

    async def test_invalid_file_is_not_written_to_disk(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="bad.exe", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(False, "rejected", None)):
            with pytest.raises(HTTPException):
                await documents.upload_document(
                    file=file, entity_type=None, entity_id=None, title=None,
                    db=db_session, current_user=user,
                )

        assert list(tmp_path.iterdir()) == []

    async def test_invalid_file_does_not_create_document_record(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="bad.exe", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(False, "rejected", None)):
            with pytest.raises(HTTPException):
                await documents.upload_document(
                    file=file, entity_type=None, entity_id=None, title=None,
                    db=db_session, current_user=user,
                )

        assert db_session.query(documents.Document).count() == 0

    async def test_validate_file_upload_called_with_raw_content_and_original_filename(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        content = b"some file bytes"
        file = FakeUploadFile(filename="../../etc/passwd.txt", content=content)
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "passwd.txt")) as mock_validate, \
             patch.object(documents, "log_activity"):
            await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        mock_validate.assert_called_once_with(content, "../../etc/passwd.txt")


class TestUploadDocumentSuccess:
    """Tests for the happy path of upload_document once validation succeeds."""

    async def test_stores_sanitized_filename_not_raw_client_filename(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="../../etc/passwd.txt", content=b"hello world")
        user = MagicMock(id=7)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "passwd.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type="contact", entity_id=5, title=None,
                db=db_session, current_user=user,
            )

        assert doc.filename == "passwd.txt"

    async def test_generates_unique_filename_using_uuid_prefix_and_safe_filename(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        content = b"hello world"
        file = FakeUploadFile(filename="report.txt", content=content)
        user = MagicMock(id=1)
        fixed_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "report.txt")), \
             patch.object(documents, "log_activity"), \
             patch.object(documents.uuid, "uuid4", return_value=fixed_uuid):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        expected_path = tmp_path / f"{fixed_uuid}_report.txt"
        assert expected_path.exists()
        assert expected_path.read_bytes() == content
        assert doc.file_path == str(expected_path)

    async def test_writes_already_read_content_without_reopening_source_file(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        content = b"\x89PNG\r\n\x1a\nfake-binary-content"
        file = FakeUploadFile(filename="image.png", content=content)
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "image.png")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        with open(doc.file_path, "rb") as f:
            assert f.read() == content

    async def test_file_size_reflects_length_of_read_content(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        content = b"x" * 1234
        file = FakeUploadFile(filename="data.bin", content=content)
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "data.bin")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.file_size == 1234

    async def test_empty_file_content_results_in_zero_file_size(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="empty.txt", content=b"")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "empty.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.file_size == 0

    async def test_mime_type_derived_from_filename_not_client_content_type(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        # Client claims octet-stream, but the real extension is .pdf.
        file = FakeUploadFile(filename="contract.pdf", content=b"%PDF-1.4", content_type="application/octet-stream")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "contract.pdf")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.mime_type == "application/pdf"

    async def test_mime_type_is_none_for_unrecognized_extension(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="mystery.unknownext", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "mystery.unknownext")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.mime_type is None

    async def test_title_defaults_to_original_client_filename_when_not_provided(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="original-name.txt", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "sanitized-name.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        # Title falls back to the raw client filename, while the stored
        # filename itself is the sanitized one.
        assert doc.title == "original-name.txt"
        assert doc.filename == "sanitized-name.txt"

    async def test_explicit_title_overrides_default_filename_title(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="report.pdf", content=b"%PDF-1.4")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "report.pdf")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title="Q1 Report",
                db=db_session, current_user=user,
            )

        assert doc.title == "Q1 Report"

    async def test_entity_type_and_entity_id_are_persisted(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="notes.txt", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "notes.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type="project", entity_id=42, title=None,
                db=db_session, current_user=user,
            )

        assert doc.entity_type == "project"
        assert doc.entity_id == 42

    async def test_uploaded_by_set_to_current_user_id(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="notes.txt", content=b"data")
        user = MagicMock(id=99)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "notes.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.uploaded_by == 99

    async def test_document_is_persisted_with_generated_id(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="notes.txt", content=b"data")
        user = MagicMock(id=1)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "notes.txt")), \
             patch.object(documents, "log_activity"):
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        assert doc.id is not None
        assert db_session.query(documents.Document).filter(
            documents.Document.id == doc.id
        ).count() == 1

    async def test_logs_document_uploaded_activity_with_expected_arguments(
        self, db_session, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
        file = FakeUploadFile(filename="notes.txt", content=b"data")
        user = MagicMock(id=3)

        with patch.object(documents, "validate_file_upload",
                           return_value=(True, None, "notes.txt")), \
             patch.object(documents, "log_activity") as mock_log:
            doc = await documents.upload_document(
                file=file, entity_type=None, entity_id=None, title=None,
                db=db_session, current_user=user,
            )

        mock_log.assert_called_once_with(
            db_session, user_id=3, action="document_uploaded",
            entity_type="document", entity_id=doc.id,
        )