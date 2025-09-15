from __future__ import annotations

from nedc_bench.api.middleware.error_handler import NEDCAPIException  # type: ignore[attr-defined]


class FileValidationError(NEDCAPIException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, error_code="FILE_VALIDATION_ERROR")


class FileValidator:
    """Basic CSV_BI validation for uploads."""

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    @staticmethod
    async def validate_csv_bi(file_content: bytes, filename: str) -> bool:
        if len(file_content) > FileValidator.MAX_FILE_SIZE:
            raise FileValidationError(f"File too large: {len(file_content)} bytes")
        if not filename.endswith(".csv_bi"):
            raise FileValidationError(f"Invalid extension: {filename}")
        try:
            text = file_content.decode("utf-8")
            lines = text.strip().splitlines()
            if not lines:
                raise FileValidationError("Empty file")
            if not (lines[0].startswith("version =") or lines[0].startswith("# version =")):
                raise FileValidationError("Invalid CSV_BI header")
            return True
        except UnicodeDecodeError as exc:
            raise FileValidationError("File is not valid UTF-8") from exc
