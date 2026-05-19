# -*- coding: utf-8 -*-
"""image_service._validate_image_integrity 단위 테스트.

PIL Image.verify() 를 통한 매직 바이트·구조 검증.
ContentType 위장·0-byte·텍스트 파일·잘린 헤더 차단 확인.

가을쥐 정책 (#72-A — 매직 바이트 검증, 2026-05-07 결정) 권위.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image as PILImage

from services.image_service import _validate_image_integrity


def _make_image_bytes(format: str, size: tuple[int, int] = (1, 1), color: str = "red") -> bytes:
    """Pillow 로 메모리에 정상 이미지 생성 후 bytes 반환."""
    buf = BytesIO()
    PILImage.new("RGB", size, color).save(buf, format=format)
    return buf.getvalue()


class TestValidImage:
    def test_정상_PNG(self):
        _validate_image_integrity(_make_image_bytes("PNG"))

    def test_정상_JPEG(self):
        _validate_image_integrity(_make_image_bytes("JPEG"))

    def test_큰_이미지_OK(self):
        _validate_image_integrity(_make_image_bytes("PNG", size=(256, 256)))


class TestInvalidImage:
    def test_텍스트_위장_거부(self):
        """정책 #72-A — ContentType 우회 차단."""
        fake = b"This is not an image, just plain text"
        with pytest.raises(HTTPException) as exc:
            _validate_image_integrity(fake)
        assert exc.value.status_code == 400
        assert "유효하지 않은" in exc.value.detail

    def test_0_byte_거부(self):
        with pytest.raises(HTTPException) as exc:
            _validate_image_integrity(b"")
        assert exc.value.status_code == 400

    def test_잘린_PNG_헤더_거부(self):
        # 매직 바이트는 정상이나 IHDR/IDAT/IEND chunk 부재
        truncated = b"\x89PNG\r\n\x1a\n"
        with pytest.raises(HTTPException) as exc:
            _validate_image_integrity(truncated)
        assert exc.value.status_code == 400

    def test_랜덤_바이트_거부(self):
        with pytest.raises(HTTPException) as exc:
            _validate_image_integrity(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        assert exc.value.status_code == 400

    def test_PDF_위장_거부(self):
        # %PDF- 헤더로 시작하는 텍스트
        fake_pdf = b"%PDF-1.4\n%random content"
        with pytest.raises(HTTPException) as exc:
            _validate_image_integrity(fake_pdf)
        assert exc.value.status_code == 400
