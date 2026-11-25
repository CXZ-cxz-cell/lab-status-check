"""ORM 数据模型。

MVP 约定：每台设备只保留一条“当前故障记录”，故障信息直接放在 devices 表，
不单独建 faults 历史表。
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    # normal / fault
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    # pending / processing / resolved / NULL（当前无故障）
    fault_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fault_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间以 ISO 8601 字符串存储，保证接口输出带 +08:00 偏移
    last_inspection_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)

    inspections: Mapped[list["Inspection"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="Inspection.id",
    )


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # normal / abnormal
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)

    device: Mapped[Device] = relationship(back_populates="inspections")
