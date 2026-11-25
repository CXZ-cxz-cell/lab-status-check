"""数据库连接与会话管理。

默认使用 backend/lab.db，可通过环境变量 LAB_DATABASE_URL 覆盖，
测试时应指向临时数据库，例如：

    LAB_DATABASE_URL=sqlite:///./tmp_test.db
"""

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "lab.db"

DATABASE_URL = os.getenv("LAB_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    # 内存数据库需要共享同一个连接，否则每次会话都会拿到空库
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def init_db() -> None:
    """创建缺失的数据表（幂等）。"""
    # 导入模型以完成注册
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供独立会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
