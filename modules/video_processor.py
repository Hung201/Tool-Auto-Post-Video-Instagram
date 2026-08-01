"""Xử lý video & né thuật toán quét trùng lặp của Instagram.

Các biến đổi được áp dụng ngẫu nhiên nhẹ mỗi lần chạy:
  - Visual : đổi tốc độ (±1-2%), độ sáng, độ tương phản, zoom/crop nhẹ.
  - Text   : chèn overlay text (render bằng PIL -> KHÔNG cần ImageMagick).
  - Audio  : đổi nhẹ tốc độ âm thanh, hoặc thay bằng nhạc nền ngẫu nhiên.
  - Hash   : re-encode + xoá sạch metadata (-map_metadata -1) -> đổi MD5.
"""

import glob
import os
import random
import re

from . import _compat  # noqa: F401  (vá Pillow>=10 cho moviepy trước khi resize)
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
)
import moviepy.video.fx.all as vfx
import numpy as np


# ----------------------------------------------------------------------------
# Text overlay bằng PIL (tránh phụ thuộc ImageMagick như TextClip của moviepy)
# ----------------------------------------------------------------------------
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Thử vài font hệ thống phổ biến, fallback về font mặc định."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    """Ngắt dòng thủ công để text không tràn khỏi khung."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        w = draw.textbbox((0, 0), trial, font=font)[2]
        if w <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# Bỏ emoji / ký tự lạ mà font thường không vẽ được (tránh hiện ô vuông □).
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"   # emoji, pictographs
    "\U00002600-\U000027BF"   # misc symbols, dingbats
    "\U0001F1E6-\U0001F1FF"   # cờ
    "\U00002190-\U000021FF"   # mũi tên
    "\U00002B00-\U00002BFF"   # symbols & arrows
    "\U0000FE00-\U0000FE0F"   # variation selectors
    "\U0000200D"              # zero-width joiner
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    text = _EMOJI_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _make_text_image(text: str, video_w: int, video_h: int) -> np.ndarray:
    """Tạo ảnh RGBA chứa text kiểu 'trắng đậm + bóng đổ mềm' (giống video mẫu)."""
    text = _strip_emoji(text)
    img = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Cỡ chữ nhỏ gọn hơn (~3.8% chiều cao). Đổi qua .env TEXT_SCALE nếu cần.
    scale = float(os.getenv("TEXT_SCALE", "0.038"))
    font_size = max(24, int(video_h * scale))
    font = _load_font(font_size)

    max_text_width = int(video_w * 0.82)
    lines = _wrap_text(draw, text, font, max_text_width)

    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + int(font_size * 0.35)
    total_height = line_height * len(lines)

    # Vị trí: mặc định TRÊN (như mẫu). Đổi qua .env TEXT_POSITION=top|center|bottom
    pos = (os.getenv("TEXT_POSITION", "top") or "top").strip().lower()
    jitter = int(random.uniform(-0.02, 0.02) * video_h)  # nhích nhẹ để né trùng
    if pos in ("center", "middle"):
        y0 = (video_h - total_height) // 2 + jitter
    elif pos in ("bottom", "lower"):
        y0 = int(video_h * 0.72) + jitter
    else:  # top
        y0 = int(video_h * 0.08) + jitter

    shadow = max(2, font_size // 22)          # độ lệch bóng đổ
    stroke = max(1, font_size // 28)          # viền mảnh cho sắc nét
    for i, line in enumerate(lines):
        w = draw.textbbox((0, 0), line, font=font)[2]
        x = (video_w - w) // 2
        y = y0 + i * line_height
        # 1) Bóng đổ mềm (đen mờ) lệch xuống-phải -> nổi trên mọi nền.
        draw.text((x + shadow, y + shadow), line, font=font, fill=(0, 0, 0, 160))
        # 2) Chữ trắng đặc + viền đen mảnh.
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))

    return np.array(img)


# ----------------------------------------------------------------------------
# Xử lý chính
# ----------------------------------------------------------------------------
def _pick_random_music(music_dir: str):
    if not music_dir or not os.path.isdir(music_dir):
        return None
    files = []
    for ext in ("*.mp3", "*.wav", "*.m4a", "*.aac"):
        files.extend(glob.glob(os.path.join(music_dir, ext)))
    return random.choice(files) if files else None


def process_video_anti_duplicate(
    input_path: str,
    output_path: str,
    overlay_text: str,
    use_random_music: bool = False,
    music_dir: str = "music",
) -> str:
    """Tạo video mới đã né trùng lặp từ video gốc + text AI.

    Trả về đường dẫn output.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Không tìm thấy video gốc: {input_path}")

    clip = VideoFileClip(input_path)
    to_close = [clip]

    try:
        # 1. Đổi tốc độ video nhẹ (0.98x - 1.02x) -> đổi frame timing / hash.
        speed_factor = random.uniform(0.98, 1.02)
        clip = clip.fx(vfx.speedx, speed_factor)

        # 2. GIỮ NGUYÊN MÀU GỐC (không chỉnh sáng/tương phản).
        #    Bật lại nếu muốn: đặt KEEP_ORIGINAL_COLOR=false trong .env
        if os.getenv("KEEP_ORIGINAL_COLOR", "true").strip().lower() not in ("1", "true", "yes", "y"):
            clip = clip.fx(vfx.colorx, random.uniform(0.99, 1.01))
            clip = clip.fx(vfx.lum_contrast, 0, random.uniform(-3, 3), 128)

        # 3. Zoom/crop rất nhẹ (0.5-1.5%) -> đổi visual fingerprint mà mắt khó thấy.
        zoom = random.uniform(1.005, 1.015)
        zw, zh = clip.w, clip.h
        clip = clip.fx(vfx.resize, zoom).fx(
            vfx.crop, width=zw, height=zh, x_center=clip.w / 2, y_center=clip.h / 2
        )

        # 5. Text overlay (render bằng PIL).
        text_arr = _make_text_image(overlay_text, clip.w, clip.h)
        txt_clip = (
            ImageClip(text_arr)
            .set_duration(clip.duration)
            .set_position((0, 0))
        )

        final = CompositeVideoClip([clip, txt_clip])
        to_close.append(final)

        # 6. Audio: nhạc nền ngẫu nhiên hoặc chỉnh nhẹ tốc độ audio gốc.
        music_path = _pick_random_music(music_dir) if use_random_music else None
        if music_path:
            print(f"🎵 Dùng nhạc nền ngẫu nhiên: {os.path.basename(music_path)}")
            bg = AudioFileClip(music_path)
            to_close.append(bg)
            if bg.duration > final.duration:
                bg = bg.subclip(0, final.duration)
            final = final.set_audio(bg)

        # 7. Xuất file, xoá sạch metadata cũ -> đổi MD5 hash.
        bitrate = f"{random.randint(3500, 5500)}k"
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            bitrate=bitrate,
            fps=clip.fps,
            threads=os.cpu_count() or 2,
            ffmpeg_params=["-map_metadata", "-1"],
            verbose=False,
            logger=None,
        )
        return output_path
    finally:
        for c in to_close:
            try:
                c.close()
            except Exception:
                pass
