"""Hàm chờ ngẫu nhiên giữa các lần đăng bài."""

import random
import time


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
