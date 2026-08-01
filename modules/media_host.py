"""Đưa video đã xử lý lên URL public HTTPS (bắt buộc cho Graph API).

Graph API không nhận file local; nó tự tải video từ 1 URL công khai. Module này
cung cấp vài backend, chọn qua biến MEDIA_HOST trong .env:

  - cloudinary : upload lên Cloudinary (free tier, đơn giản nhất). Cần
                 CLOUDINARY_URL hoặc CLOUD_NAME/API_KEY/API_SECRET.
  - public_dir : copy file vào 1 thư mục mà web server của BẠN đang phục vụ,
                 URL = PUBLIC_BASE_URL + tên file. Dùng khi bạn tự host.

Mỗi backend trả về (public_url, cleanup_fn). Gọi cleanup_fn() SAU khi đăng xong
để xoá file tạm trên hosting.
"""

import os
import shutil


# ---------------------------------------------------------------- Cloudinary
def _upload_cloudinary(local_path: str):
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        raise RuntimeError(
            "Chưa cài cloudinary. Chạy: pip install cloudinary  (hoặc đổi MEDIA_HOST=public_dir)"
        )

    # Nếu có CLOUDINARY_URL thì SDK tự đọc; nếu không, cấu hình thủ công.
    if not os.getenv("CLOUDINARY_URL"):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )
        if not cloudinary.config().cloud_name:
            raise RuntimeError("Thiếu cấu hình Cloudinary trong .env.")

    print("☁️  Upload video lên Cloudinary...")
    result = cloudinary.uploader.upload_large(
        local_path, resource_type="video", folder="ig_auto_poster"
    )
    url = result["secure_url"]
    public_id = result["public_id"]

    def cleanup():
        try:
            cloudinary.uploader.destroy(public_id, resource_type="video")
            print("🧹 Đã xoá video tạm trên Cloudinary.")
        except Exception as e:
            print(f"⚠️  Không xoá được video Cloudinary: {e}")

    return url, cleanup


# ---------------------------------------------------------------- public_dir
def _upload_public_dir(local_path: str):
    base_url = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
    serve_dir = os.getenv("PUBLIC_SERVE_DIR")
    if not base_url or not serve_dir:
        raise RuntimeError(
            "MEDIA_HOST=public_dir cần PUBLIC_BASE_URL và PUBLIC_SERVE_DIR trong .env."
        )
    os.makedirs(serve_dir, exist_ok=True)

    filename = os.path.basename(local_path)
    dest = os.path.join(serve_dir, filename)
    shutil.copy2(local_path, dest)
    url = f"{base_url}/{filename}"
    print(f"🌐 Video công khai tại: {url}")

    def cleanup():
        try:
            if os.path.exists(dest):
                os.remove(dest)
        except Exception as e:
            print(f"⚠️  Không xoá được file public: {e}")

    return url, cleanup


BACKENDS = {
    "cloudinary": _upload_cloudinary,
    "public_dir": _upload_public_dir,
}


def upload_public(local_path: str):
    """Upload theo backend cấu hình. Trả về (public_url, cleanup_fn)."""
    host = (os.getenv("MEDIA_HOST") or "cloudinary").strip().lower()
    if host not in BACKENDS:
        raise RuntimeError(f"MEDIA_HOST không hợp lệ: {host}. Chọn: {list(BACKENDS)}")
    return BACKENDS[host](local_path)
