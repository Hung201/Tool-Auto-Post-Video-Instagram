"""Vá tương thích Pillow >= 10 với moviepy 1.0.3.

Pillow 10 đã xoá hằng số Image.ANTIALIAS (moviepy 1.0.3 vẫn dùng khi resize),
gây lỗi: module 'PIL.Image' has no attribute 'ANTIALIAS'.
Import module này TRƯỚC khi gọi các hàm resize của moviepy để vá lại.
"""

from PIL import Image

if not hasattr(Image, "ANTIALIAS"):
    # Ánh xạ về LANCZOS (chất lượng cao) — thay thế cho ANTIALIAS cũ.
    Image.ANTIALIAS = Image.Resampling.LANCZOS
