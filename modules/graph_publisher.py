"""Đăng Reels bằng Instagram Graph API CHÍNH THỨC (Meta).

Quy trình 3 bước theo tài liệu Content Publishing API:
  1) Tạo media container  : POST /{ig_user_id}/media (media_type=REELS, video_url=...)
  2) Chờ Instagram xử lý  : GET /{container_id}?fields=status_code  -> FINISHED
  3) Publish              : POST /{ig_user_id}/media_publish (creation_id=...)

LƯU Ý: Graph API KHÔNG nhận file local — video phải nằm ở URL public HTTPS
(xem modules/media_host.py để đưa video đã xử lý lên hosting công khai).

Yêu cầu mỗi tài khoản:
  - Là Instagram Business/Creator, đã liên kết với 1 Facebook Page.
  - ig_user_id  : Instagram Business Account ID.
  - access_token: Long-lived Page Access Token có quyền
                  instagram_basic, instagram_content_publish, pages_read_engagement.
"""

import time

import requests

GRAPH_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _raise_graph_error(resp: requests.Response, step: str):
    try:
        err = resp.json().get("error", {})
        msg = err.get("message", resp.text)
        code = err.get("code")
        raise RuntimeError(f"[Graph API - {step}] lỗi (code {code}): {msg}")
    except ValueError:
        raise RuntimeError(f"[Graph API - {step}] HTTP {resp.status_code}: {resp.text}")


def _create_container(ig_user_id, access_token, video_url, caption, cover_url=None,
                      share_to_feed=True):
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": str(share_to_feed).lower(),
        "access_token": access_token,
    }
    if cover_url:
        params["cover_url"] = cover_url
    resp = requests.post(f"{BASE}/{ig_user_id}/media", params=params, timeout=60)
    if not resp.ok:
        _raise_graph_error(resp, "tạo container")
    return resp.json()["id"]


def _wait_until_ready(container_id, access_token, timeout_sec=600, interval=8):
    """Poll status_code cho tới khi FINISHED. Reels cần vài chục giây để Instagram xử lý."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        resp = requests.get(
            f"{BASE}/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=30,
        )
        if not resp.ok:
            _raise_graph_error(resp, "kiểm tra trạng thái")
        data = resp.json()
        code = data.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"[Graph API] Instagram xử lý video lỗi: {data.get('status')}")
        # IN_PROGRESS / PUBLISHED / EXPIRED...
        print(f"   ⏱️  Instagram đang xử lý video (status={code})...")
        time.sleep(interval)
    raise TimeoutError("Instagram xử lý video quá lâu (timeout).")


def _publish(ig_user_id, access_token, creation_id):
    resp = requests.post(
        f"{BASE}/{ig_user_id}/media_publish",
        params={"creation_id": creation_id, "access_token": access_token},
        timeout=60,
    )
    if not resp.ok:
        _raise_graph_error(resp, "publish")
    return resp.json()["id"]


def publish_reel(ig_user_id: str, access_token: str, video_url: str,
                 caption: str, cover_url: str = None) -> str:
    """Đăng 1 Reel qua Graph API. Trả về media id đã đăng."""
    if not ig_user_id or not access_token:
        raise RuntimeError("Thiếu ig_user_id hoặc access_token cho tài khoản.")

    print(f"🧱 [{ig_user_id}] Tạo media container...")
    creation_id = _create_container(ig_user_id, access_token, video_url, caption, cover_url)

    print(f"⏳ [{ig_user_id}] Chờ Instagram xử lý video...")
    _wait_until_ready(creation_id, access_token)

    print(f"🚀 [{ig_user_id}] Publishing...")
    media_id = _publish(ig_user_id, access_token, creation_id)
    print(f"✅ [{ig_user_id}] Đăng thành công! Media ID: {media_id}")
    return media_id


def verify_token(ig_user_id: str, access_token: str) -> dict:
    """Kiểm tra nhanh token & id còn hợp lệ. Trả về thông tin account."""
    resp = requests.get(
        f"{BASE}/{ig_user_id}",
        params={"fields": "username,followers_count", "access_token": access_token},
        timeout=30,
    )
    if not resp.ok:
        _raise_graph_error(resp, "verify token")
    return resp.json()
