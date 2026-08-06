"""Kết nối Instagram & đăng Reels tự động (instagrapi).

Hỗ trợ NHIỀU tài khoản: mỗi account có file session riêng (sessions/<user>.json)
để tránh đăng nhập lại nhiều lần -> giảm nguy cơ checkpoint / xác minh thiết bị lạ.
"""

import os

from . import _compat  # noqa: F401  (alias moviepy.VideoFileClip cho instagrapi)
from instagrapi import Client


def _new_client() -> Client:
    cl = Client()
    cl.delay_range = [1, 3]  # Delay ngẫu nhiên giữa các request -> giống người thật.
    return cl


def _login(cl: Client, username: str, password: str) -> None:
    """Đăng nhập; nếu có 2FA thì lấy mã từ biến môi trường IG_2FA_CODE."""
    code = os.getenv("IG_2FA_CODE", "").strip()
    if code:
        cl.login(username, password, verification_code=code)
    else:
        cl.login(username, password)


def _get_logged_in_client(username: str, password: str, session_file: str) -> Client:
    os.makedirs(os.path.dirname(session_file) or ".", exist_ok=True)
    sessionid = os.getenv("IG_SESSIONID", "").strip()
    cl = _new_client()

    # 1. Ưu tiên session đã lưu (không cần đăng nhập lại -> không bị challenge).
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.get_timeline_feed()  # Kiểm tra session còn sống.
            print(f"🔑 [{username}] Dùng session đã lưu.")
            return cl
        except Exception as e:
            print(f"⚠️  [{username}] Session cũ hết hạn ({e}). Tạo lại...")
            cl = _new_client()

    # 2. Đăng nhập bằng SESSIONID lấy từ trình duyệt (BỎ QUA challenge).
    if sessionid:
        try:
            cl.login_by_sessionid(sessionid)
            cl.dump_settings(session_file)
            print(f"🔑 [{username}] Đăng nhập bằng sessionid thành công, đã lưu session.")
            return cl
        except Exception as e:
            raise RuntimeError(
                f"IG_SESSIONID không dùng được ({e}). Lấy lại sessionid mới từ trình duyệt "
                "(đang đăng nhập Instagram) rồi dán vào .env."
            )

    # 3. Đăng nhập bằng username + password (dễ bị challenge với máy/IP lạ).
    if not username or not password:
        raise RuntimeError("Thiếu IG_USERNAME/IG_PASSWORD (hoặc IG_SESSIONID) trong .env.")
    try:
        _login(cl, username, password)
    except Exception as e:
        name = type(e).__name__
        low = str(e).lower()
        if "TwoFactor" in name or "2fa" in low:
            raise RuntimeError(
                "Tài khoản bật 2FA. Chạy lại với: IG_2FA_CODE=123456 python test_post.py"
            )
        if "Challenge" in name or "challenge" in low or "checkpoint" in low:
            raise RuntimeError(
                "Instagram chặn đăng nhập mật khẩu (challenge/checkpoint). "
                "CÁCH KHẮC PHỤC: lấy IG_SESSIONID từ trình duyệt đang đăng nhập Instagram "
                "và dán vào .env (xem hướng dẫn). Đây là cách ổn định nhất."
            )
        raise
    cl.dump_settings(session_file)
    print(f"🔑 [{username}] Đăng nhập mới thành công, đã lưu {session_file}.")
    return cl


def publish_to_instagram(video_path: str, caption: str,
                         username: str, password: str, session_file: str) -> str:
    """Đăng video lên Reels bằng tài khoản chỉ định. Trả về media pk."""
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Không tìm thấy video để đăng: {video_path}")

    cl = _get_logged_in_client(username, password, session_file)
    print(f"🚀 [{username}] Đang tải video lên Instagram Reels...")
    media = cl.clip_upload(path=video_path, caption=caption)
    print(f"✅ [{username}] Đăng thành công! Media ID: {media.pk}")
    return str(media.pk)
