# -*- coding: utf-8 -*-
"""
database.py
-----------
.env 파일의 AWS 설정을 읽어 MySQL(RDS) DB에 연결하는 모듈.

[흐름]
- SERVER=local  : SSH 터널(EC2 → RDS) → PyMySQL 연결
- SERVER=ec2    : EC2 내부에서 RDS 직접 연결

[의존 패키지]
    pip install python-dotenv pymysql sqlalchemy sshtunnel cryptography
"""

import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Windows 터미널 UTF-8 출력 보장
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ── .env 로드 ──────────────────────────────────────────────────────────────
# 프로젝트 루트의 .env를 명시적으로 지정
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_BASE_DIR, ".env"))

SERVER      = os.getenv("SERVER", "local").strip().strip("'\"")

DB_HOST     = os.getenv("DB_HOST", "localhost")   # RDS 엔드포인트 (local/ec2 공통)
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "withdog")

SSH_HOST    = os.getenv("SSH_HOST")
SSH_PORT    = int(os.getenv("SSH_PORT", 22))
SSH_USER    = os.getenv("SSH_USER", "ubuntu")
SSH_PKEY    = os.getenv("SSH_PKEY")   # PEM 키 절대경로


# ── SSH 터널 관리 ─────────────────────────────────────────────────────────
_tunnel = None

def _start_ssh_tunnel() -> int:
    """EC2 SSH 터널을 시작하고 로컬 바인딩 포트를 반환합니다."""
    from sshtunnel import SSHTunnelForwarder

    global _tunnel
    if _tunnel and _tunnel.is_active:
        return _tunnel.local_bind_port

    print(f"[SSH Tunnel] EC2({SSH_HOST}) -> RDS({DB_HOST}:{DB_PORT}) 터널 연결 시도...")
    _tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_PKEY,
        remote_bind_address=(DB_HOST, DB_PORT),  # RDS 엔드포인트:포트
        local_bind_address=("127.0.0.1",),         # 로컬 포트 자동 할당
    )
    _tunnel.start()
    print(f"[SSH Tunnel] 연결 완료 -> localhost:{_tunnel.local_bind_port}")
    return _tunnel.local_bind_port


def _stop_ssh_tunnel():
    """SSH 터널을 종료합니다."""
    global _tunnel
    if _tunnel and _tunnel.is_active:
        _tunnel.stop()
        print("[SSH Tunnel] 연결 종료")


# ── 엔진 생성 (지연 초기화) ──────────────────────────────────────────────
_engine = None
_SessionLocal = None
Base = declarative_base()


def get_engine():
    """
    싱글턴 SQLAlchemy 엔진을 반환합니다.
    최초 호출 시 SSH 터널(local 모드) 또는 직접(ec2 모드) 연결을 생성합니다.
    """
    global _engine
    if _engine is not None:
        return _engine

    if SERVER == "local":
        local_port = _start_ssh_tunnel()
        host, port = "127.0.0.1", local_port
    else:
        host, port = DB_HOST, DB_PORT

    url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{host}:{port}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    _engine = create_engine(
        url,
        pool_pre_ping=True,   # 끊긴 커넥션 자동 재확인
        pool_recycle=1800,    # 30분마다 커넥션 재생성
        echo=False,           # True 로 변경하면 SQL 로그 출력
    )
    return _engine


def get_session_factory():
    """싱글턴 SessionLocal 팩토리를 반환합니다."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


# ── FastAPI 의존성 주입용 함수 ────────────────────────────────────────────
def get_db():
    """
    FastAPI 라우터에서 Depends(get_db)로 사용하는 DB 세션 제공자.

    Example::

        from fastapi import Depends
        from sqlalchemy.orm import Session
        from back.db.database import get_db

        @app.get("/dogs")
        def read_dogs(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 직접 실행 시 연결 테스트 ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[Config] SERVER  = {SERVER}")
    print(f"[Config] DB_HOST = {DB_HOST}:{DB_PORT}")
    print(f"[Config] DB_NAME = {DB_NAME}")
    print()

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DATABASE(), VERSION()"))
            row = result.fetchone()
            print("[OK] DB 연결 성공!")
            print(f"     데이터베이스 : {row[0]}")
            print(f"     MySQL 버전   : {row[1]}")
    except Exception as e:
        print(f"[ERROR] DB 연결 실패: {e}")
    finally:
        _stop_ssh_tunnel()
