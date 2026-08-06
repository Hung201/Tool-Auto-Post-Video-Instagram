"""Lịch đăng bài: chờ ngẫu nhiên + canh khung giờ vàng (múi giờ Mỹ)."""

import random
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def random_sleep(min_hours: float = 1.0, max_hours: float = 2.0) -> None:
    """Chờ ngẫu nhiên trong khoảng [min_hours, max_hours] giờ."""
    min_seconds = int(min_hours * 3600)
    max_seconds = int(max_hours * 3600)
    if max_seconds < min_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds

    delay = random.randint(min_seconds, max_seconds)
    hours = delay // 3600
    minutes = (delay % 3600) // 60
    seconds = delay % 60

    print(f"⏳ Chờ ngẫu nhiên: {hours}h {minutes}m {seconds}s trước lần đăng tiếp theo...")
    time.sleep(delay)


# ---------------------------------------------------------------------------
# Canh khung giờ cao điểm (giờ vàng) theo múi giờ Mỹ
# ---------------------------------------------------------------------------
def _parse_windows(windows_str: str):
    """'11-14,19-22' -> [(11,14),(19,22)]. Bỏ qua khung sai định dạng."""
    windows = []
    for part in (windows_str or "").split(","):
        part = part.strip()
        if not part or "-" not in part:
            continue
        try:
            start, end = part.split("-", 1)
            s, e = int(start), int(end)
            if 0 <= s < e <= 24:
                windows.append((s, e))
        except ValueError:
            continue
    return windows


def in_peak_window(now_local: datetime, windows) -> bool:
    """True nếu giờ hiện tại nằm trong bất kỳ khung nào ([start, end))."""
    h = now_local.hour
    return any(s <= h < e for s, e in windows)


def _next_window_start(now_local: datetime, windows) -> datetime:
    """Thời điểm bắt đầu khung cao điểm gần nhất kế tiếp (hôm nay hoặc mai)."""
    candidates = []
    for s, _ in windows:
        today = now_local.replace(hour=s, minute=0, second=0, microsecond=0)
        if today > now_local:
            candidates.append(today)
        candidates.append(today + timedelta(days=1))  # phương án ngày mai
    return min(candidates)


def wait_for_peak_window(timezone_name: str, windows_str: str) -> None:
    """Nếu đang ngoài giờ vàng -> chờ tới khung kế tiếp. Trong giờ vàng -> về ngay."""
    windows = _parse_windows(windows_str)
    if not windows:
        return  # không cấu hình -> không chặn

    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        print(f"⚠️  Múi giờ '{timezone_name}' không hợp lệ (thiếu tzdata?) -> bỏ canh giờ.")
        return

    now = datetime.now(tz)
    if in_peak_window(now, windows):
        print(f"🟢 Đang trong giờ vàng US ({now:%H:%M} {timezone_name}) -> đăng ngay.")
        return

    target = _next_window_start(now, windows)
    delay = (target - now).total_seconds()
    h = int(delay // 3600)
    m = int((delay % 3600) // 60)
    print(f"🌙 Ngoài giờ vàng US (đang {now:%H:%M} {timezone_name}). "
          f"Chờ {h}h {m}m tới khung {target:%H:%M} ({timezone_name})...")
    time.sleep(max(0, delay))
