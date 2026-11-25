"""设备与巡检核心接口（成员 A 负责）。

对应 docs/api.md：
- GET    /api/devices
- GET    /api/devices/{device_id}
- GET    /api/devices/{device_id}/inspections
- POST   /api/devices/{device_id}/inspections
- PATCH  /api/devices/{device_id}/fault
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ACTIVE_FAULT_STATUSES, DeviceStatus, FaultStatus
from app.models import Device, Inspection
from app.schemas import (
    DeviceListOut,
    DeviceOut,
    FaultUpdate,
    InspectionCreate,
    InspectionListOut,
    InspectionOut,
)
from app.utils import now_iso

router = APIRouter(prefix="/devices", tags=["devices"])


def _get_device_or_404(db: Session, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return device


@router.get("", response_model=DeviceListOut)
def list_devices(
    keyword: str | None = Query(default=None, description="按设备名称模糊搜索，忽略大小写"),
    device_status: DeviceStatus | None = Query(default=None, alias="status"),
    fault_status: FaultStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DeviceListOut:
    stmt = select(Device)

    if keyword is not None and keyword.strip():
        stmt = stmt.where(func.lower(Device.name).contains(keyword.strip().lower()))
    if device_status is not None:
        stmt = stmt.where(Device.status == device_status)
    if fault_status is not None:
        stmt = stmt.where(Device.fault_status == fault_status)

    stmt = stmt.order_by(Device.id.asc())
    devices = list(db.scalars(stmt))
    return DeviceListOut(items=devices, total=len(devices))


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)) -> Device:
    return _get_device_or_404(db, device_id)


@router.get("/{device_id}/inspections", response_model=InspectionListOut)
def list_inspections(device_id: int, db: Session = Depends(get_db)) -> InspectionListOut:
    _get_device_or_404(db, device_id)

    stmt = (
        select(Inspection)
        .where(Inspection.device_id == device_id)
        .order_by(Inspection.created_at.desc(), Inspection.id.desc())
    )
    inspections = list(db.scalars(stmt))
    return InspectionListOut(items=inspections, total=len(inspections))


@router.post(
    "/{device_id}/inspections",
    response_model=InspectionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_inspection(
    device_id: int,
    payload: InspectionCreate,
    db: Session = Depends(get_db),
) -> Inspection:
    device = _get_device_or_404(db, device_id)
    now = now_iso()

    inspection = Inspection(
        device_id=device.id,
        result=payload.result,
        note=payload.note,
        created_at=now,
    )
    db.add(inspection)

    device.last_inspection_at = now
    device.updated_at = now

    # 异常巡检且当前没有未解决故障时，自动登记为待处理故障；
    # 已有 pending / processing 故障时不重复创建，保留原状态和描述。
    if payload.result == "abnormal" and device.fault_status not in ACTIVE_FAULT_STATUSES:
        device.fault_status = "pending"
        device.fault_description = payload.note
        device.status = "fault"

    db.commit()
    db.refresh(inspection)
    return inspection


@router.patch("/{device_id}/fault", response_model=DeviceOut)
def update_fault(
    device_id: int,
    payload: FaultUpdate,
    db: Session = Depends(get_db),
) -> Device:
    device = _get_device_or_404(db, device_id)
    now = now_iso()

    if payload.fault_status == "resolved":
        if device.fault_status not in ACTIVE_FAULT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前没有可解决的故障",
            )
        device.fault_status = "resolved"
        device.status = "normal"
    else:
        # pending / processing：没有故障或故障已解决时创建，已有故障时更新
        device.fault_status = payload.fault_status
        device.status = "fault"

    # 显式传入才覆盖描述；未传时保留原描述
    if "fault_description" in payload.model_fields_set:
        device.fault_description = payload.fault_description

    device.updated_at = now
    db.commit()
    db.refresh(device)
    return device
