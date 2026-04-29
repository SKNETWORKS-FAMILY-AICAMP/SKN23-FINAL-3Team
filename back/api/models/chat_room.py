# -*- coding: utf-8 -*-
"""
models/chat_room.py
-------------------
chat_rooms 테이블 ORM 모델.

AI 챗봇 대화 세션.
- user_id: users.id FK
- Soft Delete: deleted_at 기록 (하위 메시지는 물리 보존)
"""

from __future__ import annotations

from datetime import datetime
from core.database import Base
from core.utils import kst_now
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func



class ChatRoom(Base):
    """AI 챗봇 대화 세션."""

    __tablename__ = "chat_rooms"
    __table_args__ = (
        Index("idx_chat_rooms_user", "user_id", "updated_at"),
        {
            "comment": "AI 챗봇 대화 세션",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="채팅방 ID")

    # FK → users
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        comment="사용자 ID",
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="채팅방 제목 (NULL 시 첫 메시지로 자동 생성)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="생성 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, onupdate=kst_now, server_default=func.now(),
        comment="마지막 메시지 발송 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="삭제 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="chat_rooms")
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="save-update, merge",   # 물리 보존 정책 → delete 전파 없음
        order_by="ChatMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<ChatRoom id={self.id} user_id={self.user_id} title={self.title!r}>"
