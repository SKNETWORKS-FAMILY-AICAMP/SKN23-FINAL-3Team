# -*- coding: utf-8 -*-
"""
models/chat_message.py
----------------------
chat_messages 테이블 ORM 모델.

채팅방 내 대화 메시지.
- room_id: chat_rooms.id FK
- 삭제 없음 (영구 보존 정책)
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ChatMessage(Base):
    """채팅방 내 대화 메시지 (영구 보존)."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_messages_room", "room_id", "created_at"),
        {
            "comment": "채팅방 내 대화 메시지",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="메시지 ID")

    # FK → chat_rooms
    room_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_rooms.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        comment="채팅방 ID",
    )

    role: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="발신자 구분 (user | assistant | system)",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="메시지 본문")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="발송 일시",
    )

    # ── Relationships ──────────────────────────────────────────────────────
    room: Mapped[ChatRoom] = relationship("ChatRoom", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} room_id={self.room_id} role={self.role!r}>"
