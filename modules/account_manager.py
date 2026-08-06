"""Quản lý & xoay vòng nhiều tài khoản Instagram.

Đọc cấu hình từ config/accounts.json. Nếu file không tồn tại, tự fallback về
1 tài khoản khai báo trong .env (IG_USERNAME/IG_PASSWORD) để tương thích ngược.

Mỗi account có thể có prompt / hashtags / lịch riêng; thiếu field nào thì lấy
giá trị mặc định từ .env.
"""

import json
import os

ACCOUNTS_FILE = os.path.join("config", "accounts.json")
SESSIONS_DIR = "sessions"


def _default(key: str, fallback: str) -> str:
    return (os.getenv(key) or fallback).strip()


def _normalize(acc: dict) -> dict:
    """Điền field mặc định cho 1 account, chuẩn hoá kiểu dữ liệu.

    Hỗ trợ cả 2 kiểu credential:
      - Graph API (chính thức): ig_user_id + access_token.
      - instagrapi (private)   : username + password.
    'username' cũng được dùng làm nhãn hiển thị / khoá lịch sử / tên session.
    """
    publisher = _default("PUBLISHER", "graph").lower()

    # Nhãn account: username, hoặc 'name', hoặc ig_user_id.
    username = str(acc.get("username") or acc.get("name") or acc.get("ig_user_id") or "").strip()

    ig_user_id = str(acc.get("ig_user_id", "")).strip()
    access_token = str(acc.get("access_token", "")).strip()
    password = str(acc.get("password", "")).strip()

    if publisher in ("graph", "instagram"):
        if not ig_user_id or not access_token:
            raise ValueError(f"Account (API chính thống) thiếu ig_user_id/access_token: {username or acc!r}")
    else:  # instagrapi
        if not username or not password:
            raise ValueError(f"Account (instagrapi) thiếu username/password: {acc!r}")

    if not username:
        username = ig_user_id or "account"

    os.makedirs(SESSIONS_DIR, exist_ok=True)
    return {
        "username": username,
        "password": password,
        "ig_user_id": ig_user_id,
        "access_token": access_token,
        "hashtags": str(acc.get("hashtags", _default("CAPTION_HASHTAGS", "#reels #viral"))),
        "prompt": str(acc.get("prompt", _default("PROMPT_TEXT", ""))) or None,
        "prompt_file": acc.get("prompt_file"),  # đường dẫn file prompt riêng (tùy chọn)
        "use_random_music": bool(acc.get(
            "use_random_music",
            _default("USE_RANDOM_MUSIC", "false").lower() in ("1", "true", "yes"),
        )),
        "min_hours": float(acc.get("min_hours", _default("MIN_HOURS", "1.0"))),
        "max_hours": float(acc.get("max_hours", _default("MAX_HOURS", "2.0"))),
        "session_file": os.path.join(SESSIONS_DIR, f"{username}.json"),
    }


def load_accounts() -> list:
    """Trả về danh sách account đã chuẩn hoá."""
    if os.path.isfile(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("accounts", data) if isinstance(data, dict) else data
        accounts = [_normalize(a) for a in raw]
        if not accounts:
            raise RuntimeError(f"{ACCOUNTS_FILE} không có account nào.")
        return accounts

    # Fallback: 1 account từ .env
    publisher = _default("PUBLISHER", "graph").lower()
    if publisher in ("graph", "instagram"):
        ig_user_id = os.getenv("IG_USER_ID")
        access_token = os.getenv("IG_ACCESS_TOKEN")
        if not ig_user_id or not access_token:
            raise RuntimeError(
                "Không tìm thấy config/accounts.json và cũng thiếu IG_USER_ID/IG_ACCESS_TOKEN "
                "trong .env (đang dùng PUBLISHER=graph)."
            )
        return [_normalize({
            "username": os.getenv("IG_USERNAME") or ig_user_id,
            "ig_user_id": ig_user_id,
            "access_token": access_token,
        })]

    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Không tìm thấy config/accounts.json và cũng thiếu IG_USERNAME/IG_PASSWORD trong .env"
        )
    return [_normalize({"username": username, "password": password})]
