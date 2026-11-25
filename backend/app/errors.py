"""统一异常处理。

目标：所有业务错误都返回 {"detail": "字符串"}，前端只需要处理字符串。
FastAPI 默认的 422 响应里 detail 是数组，这里统一转成中文提示。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

FIELD_LABELS = {
    "result": "巡检结果",
    "note": "巡检备注",
    "fault_status": "故障状态",
    "fault_description": "故障描述",
    "status": "设备状态",
    "device_id": "设备 ID",
    "keyword": "搜索关键词",
}

# 枚举类字段的固定提示，避免把 pydantic 的英文报错直接暴露给前端
ENUM_MESSAGES = {
    "result": "巡检结果必须是 normal 或 abnormal",
    "fault_status": "fault_status 必须是 pending、processing 或 resolved",
    "status": "status 必须是 normal 或 fault",
}


def _build_message(error: dict) -> str:
    loc = [part for part in error.get("loc", ()) if isinstance(part, str)]
    field = loc[-1] if loc else ""
    error_type = error.get("type", "")

    label = FIELD_LABELS.get(field, field or "请求参数")

    if error_type == "missing":
        return f"{label}不能为空"
    if field in ENUM_MESSAGES:
        return ENUM_MESSAGES[field]
    if error_type == "string_too_short":
        return f"{label}不能为空"
    if error_type == "string_too_long":
        max_length = next(
            (ctx for ctx in error.get("ctx", {}).values() if isinstance(ctx, int)),
            500,
        )
        return f"{label}长度不能超过 {max_length} 字"
    if error_type in ("int_parsing", "int_type"):
        return f"{label}必须是整数"

    return f"{label}参数校验失败"


def _build_detail(errors: list[dict]) -> str:
    messages: list[str] = []
    for error in errors:
        message = _build_message(error)
        if message not in messages:
            messages.append(message)
    return "；".join(messages) or "参数校验失败"


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": _build_detail(exc.errors())})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未捕获异常: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
