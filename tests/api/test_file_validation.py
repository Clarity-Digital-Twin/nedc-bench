"""Test file validator with real CSV_BI edge cases"""

import pytest
from nedc_bench.api.services.file_validator import FileValidationError, FileValidator


class TestFileValidator:
    """Test CSV_BI file validation edge cases"""

    @pytest.fixture
    def validator(self):
        """Create FileValidator instance"""
        return FileValidator()

    @pytest.mark.asyncio
    async def test_valid_csv_bi_file(self, validator):
        """Test validation of valid CSV_BI file"""
        content = b"""# version = csv_bi_v1.0.0
# duration = 100.0 secs
# patient = test001
channel,start_time,stop_time,label,confidence
TERM,0.0,1.0,seiz,1.0
TERM,2.0,3.0,bckg,1.0
"""
        result = await validator.validate_csv_bi(content, "test.csv_bi")
        assert result is True

    @pytest.mark.asyncio
    async def test_file_too_large(self, validator):
        """Test rejection of oversized files"""
        # Create content larger than MAX_FILE_SIZE
        large_content = b"x" * (FileValidator.MAX_FILE_SIZE + 1)

        with pytest.raises(FileValidationError) as exc_info:
            await validator.validate_csv_bi(large_content, "large.csv_bi")

        assert "File too large" in str(exc_info.value)
        assert str(FileValidator.MAX_FILE_SIZE + 1) in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_filename_extension(self, validator):
        """Test rejection of non-CSV_BI files"""
        content = b"# version = csv_bi_v1.0.0"

        # Test various invalid extensions
        invalid_names = ["test.csv", "test.txt", "test", None, ""]

        for filename in invalid_names:
            with pytest.raises(FileValidationError) as exc_info:
                await validator.validate_csv_bi(content, filename)
            assert "Invalid extension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_file(self, validator):
        """Test rejection of empty files"""
        empty_content = b""

        with pytest.raises(FileValidationError) as exc_info:
            await validator.validate_csv_bi(empty_content, "empty.csv_bi")

        assert "Empty file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_whitespace_only_file(self, validator):
        """Test rejection of whitespace-only files"""
        whitespace_content = b"   \n\t\n   "

        with pytest.raises(FileValidationError) as exc_info:
            await validator.validate_csv_bi(whitespace_content, "whitespace.csv_bi")

        assert "Empty file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_header(self, validator):
        """Test rejection of files without CSV_BI header"""
        invalid_headers = [
            b"channel,start,stop,label",  # Missing version
            b"This is not a CSV_BI file",
            b"version: wrong format",
            b"# comment but no version",
        ]

        for content in invalid_headers:
            with pytest.raises(FileValidationError) as exc_info:
                await validator.validate_csv_bi(content, "invalid.csv_bi")
            assert "Invalid CSV_BI header" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_utf8_content(self, validator):
        """Test rejection of non-UTF8 encoded files"""
        # Invalid UTF-8 byte sequences
        invalid_utf8 = b"\xff\xfe Invalid UTF-8"

        with pytest.raises(FileValidationError) as exc_info:
            await validator.validate_csv_bi(invalid_utf8, "invalid_encoding.csv_bi")

        assert "not valid UTF-8" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_version_header_variations(self, validator):
        """Test acceptance of different valid version header formats"""
        valid_headers = [
            b"version = csv_bi_v1.0.0\n",  # Without #
            b"# version = csv_bi_v1.0.0\n",  # With #
            b"#version=csv_bi_v1.0.0\n",  # No spaces
            b"# version = csv_bi_v2.0.0\n",  # Different version
        ]

        for content in valid_headers:
            result = await validator.validate_csv_bi(content, "valid.csv_bi")
            assert result is True

    @pytest.mark.asyncio
    async def test_file_validation_error_properties(self):
        """Test FileValidationError exception properties"""
        error = FileValidationError("Test error message")

        assert error.status_code == 400
        assert error.detail == "Test error message"
        assert error.error_code == "FILE_VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_max_file_size_boundary(self, validator):
        """Test file size at exact boundary"""
        # Exactly at max size - should pass
        max_content = b"# version = csv_bi_v1.0.0\n" + b"x" * (
            FileValidator.MAX_FILE_SIZE - len(b"# version = csv_bi_v1.0.0\n")
        )

        result = await validator.validate_csv_bi(max_content, "max.csv_bi")
        assert result is True

        # One byte over - should fail
        over_content = max_content + b"x"
        with pytest.raises(FileValidationError) as exc_info:
            await validator.validate_csv_bi(over_content, "over.csv_bi")
        assert "File too large" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_real_csv_bi_format(self, validator):
        """Test with realistic CSV_BI content"""
        realistic_content = b"""# version = csv_bi_v1.0.0
# duration = 3600.0 secs
# bname = 00000258_s002
# session = 00000258_s002_t000
# sampling_frequency = 256 Hz
# montage = tcp_ar
channel,start_time,stop_time,label,confidence
TERM,0.0000,30.0000,bckg,1.0000
TERM,30.0000,45.5000,seiz,1.0000
TERM,45.5000,120.0000,bckg,1.0000
TERM,120.0000,135.2500,seiz,0.9500
TERM,135.2500,3600.0000,bckg,1.0000
"""
        result = await validator.validate_csv_bi(realistic_content, "realistic.csv_bi")
        assert result is True
