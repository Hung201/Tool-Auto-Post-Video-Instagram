"""Ghi lịch sử bài đã đăng & kiểm tra trùng nội dung.

Lưu vào history.json (một list các record). Dùng để:
  - Tránh đăng lại đúng câu text AI đã đăng (theo từng account).
  - Xem lại toàn bộ lịch sử: account, video gốc, text, media_pk, thời gian.
"""

import hashlib
import json
import os
import re
import time

HISTORY_FILE = "history.json"


def _normalize_text(text: str) -> str:
    """Chuẩn hoá để so trùng: thường hoá, bỏ dấu câu thừa & khoảng trắng."""
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text


def _text_hash(text: str) -> str:
    return hashlib.md5(_normalize_text(text).encode("utf-8")).hexdigest()


def _load() -> list:
    if not os.path.isfile(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(records: list) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def is_duplicate_text(username: str, text: str) -> bool:
    """True nếu account này đã từng đăng đúng nội dung text đó."""
    h = _text_hash(text)
    for rec in _load():
        if rec.get("username") == username and rec.get("text_hash") == h:
            return True
    return False


def record_post(username: str, video_source: str, text: str,
                media_pk: str, caption: str) -> None:
    """Ghi 1 bài đã đăng vào lịch sử."""
    records = _load()
    records.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": int(time.time()),
        "username": username,
        "video_source": video_source,
        "text": text,
        "text_hash": _text_hash(text),
        "media_pk": media_pk,
        "caption": caption,
    })
    _save(records)


def posts_count(username: str = None) -> int:
    records = _load()
    if username is None:
        return len(records)
    return sum(1 for r in records if r.get("username") == username)
