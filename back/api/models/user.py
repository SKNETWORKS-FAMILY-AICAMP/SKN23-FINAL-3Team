# -*- coding: utf-8 -*-
"""
models/user.py
--------------
users 테이블 ORM 모델.

소셜 로그인(카카오/구글/네이버) 기반 사용자 계정.
- profile_id: images.id FK (프로필 이미지)
- type_id   : keywords.id FK (대표 성향 키워드)
- Soft Delete: deleted_at 기록 → 10일 후 Hard Delete (scheduler.py)
"""

from __future__ import annotations

from typing import Any
from core.utils import kst_now
from core.database import Base
from datetime import date, datetime
from core.type.gender import GenderEnum
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (BigInteger, DateTime, Date, Enum as SAEnum, ForeignKey, Index, JSON, String, UniqueConstraint, func)


class User(Base):
    """소셜 로그인 사용자 계정."""

    __tablename__ = "users"
    __table_args__ = (
        # 소셜 로그인 중복 가입 방지
        UniqueConstraint("provider", "provider_id", name="uq_users_provider"),
        # 이메일 조회 인덱스
        Index("idx_users_email", "email"),
        {
            "comment": "소셜 로그인 사용자 계정",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="사용자 ID")
    email: Mapped[str] = mapped_column(String(255), nullable=False, comment="이메일 주소")
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, comment="닉네임")
    gender: Mapped[GenderEnum | None] = mapped_column(SAEnum(GenderEnum), nullable=True, comment="성별")
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="생년월일")

    # FK → images
    profile_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("images.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="프로필 이미지 ID",
    )

    provider: Mapped[str] = mapped_column(String(20), nullable=False, comment="소셜 로그인 제공자 (google/kakao/naver)")
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="OAuth2.0 제공자 발급 고유 ID")

    # FK → keywords
    type_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("keywords.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="대표 성향 키워드 ID",
    )

    # FK → pets (대표 반려견, 1:1 포인터). 본인 소유 pet 여야 함은 service 단 검증.
    # ON DELETE SET NULL: 대표 pet 이 hard delete 되면 자동 NULL.
    # soft delete 케이스는 pet_service.delete_pet 가 자동 승격으로 처리.
    primary_pet_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("pets.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        comment="대표 반려견 ID (마이페이지 카드·기본 컨텍스트용)",
    )

    selected_tags: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, comment="선택한 여행 성향 태그 목록")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="생성 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, onupdate=kst_now, server_default=func.now(),
        comment="최종 수정 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="탈퇴 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    # selectin: UserResponse.model_validate 시 profile_image_url property 자동 매핑용 prefetch.
    profile: Mapped[Image | None] = relationship("Image", foreign_keys=[profile_id], lazy="selectin")
    # selectin: UserResponse.type_name property 가 동기 access 안전하도록 prefetch.
    type: Mapped[Keyword | None] = relationship("Keyword", foreign_keys=[type_id], lazy="selectin")
    # users.primary_pet_id ↔ pets.user_id 양방향 FK 라 SQLAlchemy 추론 모호 → foreign_keys 명시.
    pets: Mapped[list[Pet]] = relationship(
        "Pet",
        back_populates="user",
        foreign_keys="[Pet.user_id]",
        cascade="all, delete-orphan",
    )
    # 대표 반려견 nested 응답용. async 환경이라 lazy="selectin" — UserResponse.model_validate 시 자동 로드.
    primary_pet: Mapped[Pet | None] = relationship(
        "Pet",
        foreign_keys=[primary_pet_id],
        lazy="selectin",
    )
    chat_rooms: Mapped[list[ChatRoom]] = relationship("ChatRoom", back_populates="user", cascade="all, delete-orphan")
    diaries: Mapped[list[Diary]] = relationship("Diary", back_populates="user", cascade="all, delete-orphan")

    @property
    def profile_image_url(self) -> str | None:
        """UserResponse 의 from_attributes 매핑용 — relationship 에서 url 동적 추출.

        relationship 이 lazy=selectin 으로 prefetch 되어 동기 access 안전.
        Pet.profile_image_url property 와 동일 패턴.
        """
        return self.profile.file_url if self.profile else None

    @property
    def type_name(self) -> str | None:
        """UserResponse 의 from_attributes 매핑용 — keywords.name 동적 추출.

        User.type relationship 이 lazy=selectin 으로 prefetch 되어 동기 access 안전.
        type_id 가 NULL 이면 None 반환 — 마이페이지에서 "성향 미설정" 표시 분기.
        """
        return self.type.name if self.type else None

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} provider={self.provider!r}>"
