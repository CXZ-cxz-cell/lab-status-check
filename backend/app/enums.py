"""接口约定的枚举值（与 docs/api.md 第 2 节保持一致）。"""

from typing import Literal

DeviceStatus = Literal["normal", "fault"]
FaultStatus = Literal["pending", "processing", "resolved"]
InspectionResult = Literal["normal", "abnormal"]

DEVICE_STATUSES: tuple[str, ...] = ("normal", "fault")
FAULT_STATUSES: tuple[str, ...] = ("pending", "processing", "resolved")
INSPECTION_RESULTS: tuple[str, ...] = ("normal", "abnormal")

# 仍处于故障中的状态
ACTIVE_FAULT_STATUSES: tuple[str, ...] = ("pending", "processing")
