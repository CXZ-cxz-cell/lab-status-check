"""通用工具函数。"""

from datetime import datetime, timedelta, timezone

# 接口约定中的时间统一为北京时间，例如 2026-11-24T10:30:00+08:00
BEIJING_TZ = timezone(timedelta(hours=8))


def now_iso() -> str:
    """返回带时区的 ISO 8601 时间字符串。"""
    return datetime.now(BEIJING_TZ).isoformat(timespec="seconds")
