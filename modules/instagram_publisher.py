"""Kết nối Instagram & đăng Reels tự động (instagrapi).

Hỗ trợ NHIỀU tài khoản: mỗi account có file session riêng (sessions/<user>.json)
để tránh đăng nhập lại nhiều lần -> giảm nguy cơ checkpoint / xác minh thiết bị lạ.
"""

import os

from instagrapi import Client
from instagrapi.exceptions import LoginRequired


def _get_logged_in_client(username: str, password: str, session_file: str) -> Client:
    if not username or not password:
        raise RuntimeError("Thiếu username/password của tài khoản.")

    os.makedirs(os.path.dirname(session_file) or ".", exist_ok=True)

    cl = Client()
    cl.delay_range = [1, 3]  # Delay ngẫu nhiên giữa các request -> giống người thật.

    # 1. Thử dùng session đã lưu.
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(username, password)  # Dùng lại session cookie nếu còn hạn.
            cl.get_timeline_feed()        # Kiểm tra session còn sống.
            print(f"🔑 [{username}] Đăng nhập bằng session đã lưu.")
            return cl
        except Exception as e:
            print(f"⚠️  [{username}] Session cũ không dùng được ({e}). Đăng nhập lại...")
            old = cl.get_settings()
            cl = Client()
            cl.delay_range = [1, 3]
            cl.set_settings({})
            cl.set_uuids(old.get("uuids", {}))  # Giữ device UUID -> không bị coi là thiết bị mới.

    # 2. Đăng nhập mới và lưu session.
    cl.login(username, password)
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
