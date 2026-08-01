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


def _make_text_image(text: str, video_w: int, video_h: int) -> np.ndarray:
    """Tạo ảnh RGBA trong suốt chứa text (có viền đen cho dễ đọc)."""
    img = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = max(28, int(video_h * random.uniform(0.045, 0.06)))
    font = _load_font(font_size)

    max_text_width = int(video_w * 0.8)
    lines = _wrap_text(draw, text, font, max_text_width)

    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + 12
    total_height = line_height * len(lines)

    # Vị trí dọc ngẫu nhiên: giữa / trên / dưới -> đổi bố cục mỗi lần.
    vpos = random.choice(["center", "upper", "lower"])
    if vpos == "center":
        y0 = (video_h - total_height) // 2
    elif vpos == "upper":
        y0 = int(video_h * 0.15)
    else:
        y0 = int(video_h * 0.7)

    for i, line in enumerate(lines):
        w = draw.textbbox((0, 0), line, font=font)[2]
        x = (video_w - w) // 2
        y = y0 + i * line_height
        # Viền đen (stroke) để nổi trên nền sáng.
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                  stroke_width=max(2, font_size // 18), stroke_fill=(0, 0, 0, 220))

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

        # 2. Độ sáng.
        clip = clip.fx(vfx.colorx, random.uniform(0.97, 1.03))

        # 3. Độ tương phản nhẹ.
        clip = clip.fx(vfx.lum_contrast, 0, random.uniform(-8, 8), 128)

        # 4. Zoom/crop rất nhẹ (1-3%) -> đổi visual fingerprint mà mắt khó thấy.
        zoom = random.uniform(1.01, 1.03)
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
