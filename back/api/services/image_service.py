# -*- coding: utf-8 -*-
"""
services/image.py
-----------------
이미지 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_image()  : S3 업로드 → DB 저장 (원자성 보장)
    - get_image()     : 이미지 단건 조회 (Soft Delete 미포함)
    - delete_image()  : FK 참조 확인 후 Soft Delete

S3 업로드 실패 시 DB 저장 없이 502 예외를 반환합니다.
users.profile_id / diaries.image_id 참조 시 409 예외로 삭제를 거부합니다.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
import aioboto3

from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image as PILImage, UnidentifiedImageError

from models.image import Image
from core.utils import kst_now
from core.config import settings
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)


# ── 매직 바이트 검증 헬퍼 (정책 #72-A) ────────────────────────────────────────

def _validate_image_integrity(content: bytes) -> None:
    """이미지 매직 바이트·구조 검증.

    PIL `Image.verify()` 로 헤더·구조 무결성을 확인합니다. ContentType 위장
    (예: text 파일을 image/jpeg 로 보내는) 시도를 차단합니다.

    Args:
        content: 업로드 파일 바이트.

    Raises:
        HTTPException 400: 이미지 헤더가 유효하지 않음.
    """
    try:
        PILImage.open(BytesIO(content)).verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 이미지 파일입니다",
        ) from e


# ── S3 key 추출 헬퍼 (delete_objects 용) ────────────────────────────────────

def _extract_s3_key(file_url: str) -> str | None:
    """`https://{bucket}.s3.{region}.amazonaws.com/{key}` 에서 key 추출.

    `settings.AWS_S3_BUCKET_NAME` 과 다른 버킷 / 잘못된 형식 / 빈 key 는 None 반환.
    """
    parsed = urlparse(file_url)
    expected_host_prefix = f"{settings.AWS_S3_BUCKET_NAME}."
    if not parsed.netloc.startswith(expected_host_prefix):
        return None
    key = parsed.path.lstrip("/")
    return key if key else None


# ── S3 bulk 삭제 헬퍼 — hard_delete_withdrawn_users 배치 사용 ──────────────────

async def _delete_from_s3(file_urls: list[str]) -> tuple[list[str], list[str]]:
    """S3 객체 bulk 삭제. retry 5회 + exponential backoff (1·2·4·8s).

    Args:
        file_urls: 삭제할 객체의 `file_url` 목록 (DB images.file_url 컬럼).

    Returns:
        (deleted_urls, failed_urls) — 성공·최종실패 분리.

    동작:
        - `delete_objects` (boto3 bulk API) 호출. 응답의 `Errors` 배열에 박힌 객체만
          다음 retry 대상으로 남김. 최대 5회 시도 후에도 실패하면 `logger.error`.
        - 잘못된 URL 형식 (다른 버킷 / 파싱 실패) 은 retry 없이 즉시 failed 분류.
        - DB 트랜잭션 외부에서 호출 가정 — 외부 시스템 latency 가 트랜잭션에 영향 X.
    """
    if not file_urls:
        return [], []

    deleted: list[str] = []
    failed: list[str] = []
    url_to_key: dict[str, str] = {}

    for url in file_urls:
        key = _extract_s3_key(url)
        if key is None:
            logger.warning("[S3] skip invalid url (bucket mismatch or empty key): %s", url)
            failed.append(url)
            continue
        url_to_key[url] = key

    pending_urls = list(url_to_key.keys())
    if not pending_urls:
        return deleted, failed

    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    ) as s3_client:
        for attempt in range(5):
            if not pending_urls:
                break

            objects = [{"Key": url_to_key[u]} for u in pending_urls]
            try:
                response = await s3_client.delete_objects(
                    Bucket=settings.AWS_S3_BUCKET_NAME,
                    Delete={"Objects": objects, "Quiet": False},
                )
                error_entries = response.get("Errors", []) or []
                error_keys = {e.get("Key") for e in error_entries}

                # 성공 객체 분리
                remaining: list[str] = []
                for url in pending_urls:
                    if url_to_key[url] in error_keys:
                        remaining.append(url)
                    else:
                        deleted.append(url)
                pending_urls = remaining

                if not pending_urls:
                    break

                logger.warning(
                    "[S3] %d objects failed at attempt %d/5: %s",
                    len(pending_urls), attempt + 1, error_entries[:3],
                )
            except Exception as e:
                logger.warning(
                    "[S3] delete_objects exception at attempt %d/5: %s",
                    attempt + 1, e,
                )

            # 마지막 시도 후엔 sleep 생략
            if attempt < 4:
                await asyncio.sleep(2 ** attempt)  # 1·2·4·8s

    # 5회 retry 후에도 실패한 객체
    for url in pending_urls:
        logger.error("[S3] delete failed after 5 retries: %s", url)
        failed.append(url)

    return deleted, failed


# ── S3 업로드 헬퍼 ───────────────────────────────────────────────────────────
async def _upload_to_s3(
    content: bytes,
    original_filename: str,
    content_type: str,
) -> str:
    """
        파일을 AWS S3에 업로드하고 공개 URL을 반환합니다.

        Args:
                content          : 파일 바이트
                original_filename: 원본 파일명 (확장자 추출용)
                content_type     : MIME 타입

        Returns:
                S3 공개 URL (https://{bucket}.s3.{region}.amazonaws.com/{key})

        Raises:
                Exception: S3 업로드 실패 시
    """
    ext = Path(original_filename).suffix.lower() or ".bin"
    s3_key = f"images/{uuid.uuid4().hex}{ext}"

    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    ) as s3_client:
        await s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
        )

    return (
        f"https://{settings.AWS_S3_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def create_image(file: UploadFile, db: AsyncSession) -> Image:
    """
        multipart 파일을 S3에 업로드하고 images 테이블에 메타데이터를 저장합니다.

        [트랜잭션 보장]
        - S3 업로드를 먼저 수행합니다.
        - S3 실패 시 DB 저장 없이 502 예외를 반환합니다.
        - DB 저장은 get_db() 세션의 commit에 위임합니다.

        Args:
                file: FastAPI UploadFile (multipart/form-data)
                db  : AsyncSession

        Returns:
                저장된 Image ORM 객체

        Raises:
                HTTPException 422: 파일 미전송
                HTTPException 502: S3 업로드 실패
    """
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="파일이 전송되지 않았습니다.",
        )

    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    original_filename = file.filename

    # 매직 바이트 검증 (정책 #72-A — ContentType 위장 차단, S3 업로드 전)
    _validate_image_integrity(content)

    # Step 1: S3 업로드 (실패 시 DB 저장 없음)
    try:
        file_url = await _upload_to_s3(content, original_filename, content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 업로드 실패: {e}",
        )

    # Step 2: DB 저장
    image = Image(file_url=file_url, file_name=original_filename)
    db.add(image)
    await db.flush()  # id 생성 (commit은 get_db() deps에서 처리)
    await db.refresh(image)

    return image


async def get_image(image_id: int, db: AsyncSession) -> Image:
    """
        이미지 단건 조회.

        Args:
                image_id: 조회할 이미지 ID
                db      : AsyncSession

        Returns:
                Image ORM 객체

        Raises:
                HTTPException 404: 존재하지 않거나 이미 삭제된 이미지
    """
    result = await db.execute(
        select(Image).where(
            Image.id == image_id,
            Image.deleted_at.is_(None),
        )
    )
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"이미지(id={image_id})를 찾을 수 없습니다.",
        )

    return image


async def delete_image(image_id: int, db: AsyncSession) -> None:
    """
        이미지 Soft Delete.

        [FK 참조 확인]
        - users.profile_id 에서 참조 중이면 409 반환
        - pets.image_id 에서 참조 중이면 409 반환
        - diaries.image_id 에서 참조 중이면 409 반환

        Args:
                image_id: 삭제할 이미지 ID
                db      : AsyncSession

        Raises:
                HTTPException 404: 이미지 없음
                HTTPException 409: FK 참조 중 — 삭제 불가
    """
    # 순환 임포트 방지를 위해 함수 내에서 임포트
    from models.diary import Diary
    from models.pet import Pet
    from models.user import User

    image = await get_image(image_id, db)

    # FK 참조 확인 — users.profile_id
    user_ref_count = await db.scalar(
        select(func.count(User.id)).where(
            User.profile_id == image_id,
            User.deleted_at.is_(None),
        )
    )
    if user_ref_count and user_ref_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="현재 프로필 이미지로 사용 중입니다. 먼저 프로필 사진을 변경해주세요.",
        )

    # FK 참조 확인 — pets.image_id (활성 pet 기준)
    pet_ref_count = await db.scalar(
        select(func.count(Pet.id)).where(
            Pet.image_id == image_id,
            Pet.deleted_at.is_(None),
        )
    )
    if pet_ref_count and pet_ref_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="반려견 프로필 이미지로 사용 중입니다. 먼저 반려견 사진을 변경해주세요.",
        )

    # FK 참조 확인 — diaries.image_id
    diary_ref_count = await db.scalar(
        select(func.count(Diary.id)).where(
            Diary.image_id == image_id,
            Diary.deleted_at.is_(None),
        )
    )
    if diary_ref_count and diary_ref_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="다이어리에서 사용 중인 이미지입니다. 먼저 다이어리를 삭제해주세요.",
        )

    # Soft Delete
    image.deleted_at = kst_now()
    await db.flush()
