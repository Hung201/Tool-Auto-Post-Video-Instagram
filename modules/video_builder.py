"""Ghép video đầu vào tự động cho tool đăng Instagram.

Quy trình:
  1) Lấy NGẪU NHIÊN 1 clip mở đầu trong first-video/
  2) Lấy NGẪU NHIÊN 2 clip trong second-video/ (không trùng nhau)
  3) Chuẩn hoá tất cả về cùng khung dọc 9:16 (1080x1920) rồi ghép nối
  4) Lấy NGẪU NHIÊN 1 file nhạc trong music/, cắt/lặp đúng bằng độ dài video
  5) Ghi ra 1 file tạm (đã có nhạc). Bước né-trùng + overlay text do
     video_processor.process_video_anti_duplicate xử lý ở bước sau.

CHỐNG TRÙNG: mỗi tổ hợp (mở đầu + 2 clip) được ghi vào used_combos.json và
tránh lặp lại cho tới khi dùng hết mọi tổ hợp mới reset -> mỗi video đăng lên
là một tổ hợp khác nhau.
"""

import glob
import itertools
import json
import os
import random

from . import _compat  # noqa: F401  (vá Pillow>=10 cho moviepy trước khi resize)
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips
import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx

VIDEO_EXTS = ("*.mp4", "*.mov", "*.mkv", "*.avi", "*.webm")
MUSIC_EXTS = ("*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg")
COMBO_STATE = "used_combos.json"


# ----------------------------------------------------------------- liệt kê file
def _list_files(directory: str, exts) -> list:
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(directory, ext)))
    return sorted(files)


# --------------------------------------------------------- chống trùng tổ hợp
def _load_used() -> set:
    if not os.path.isfile(COMBO_STATE):
        return set()
    try:
        with open(COMBO_STATE, "r", encoding="utf-8") as f:
            return set(tuple(x) for x in json.load(f))
    except (json.JSONDecodeError, OSError, ValueError):
        return set()


def _save_used(used: set) -> None:
    with open(COMBO_STATE, "w", encoding="utf-8") as f:
        json.dump([list(x) for x in used], f, ensure_ascii=False, indent=2)


def _order_matters() -> bool:
    """True (mặc định): (A,B) khác (B,A) -> gấp đôi số tổ hợp."""
    return (os.getenv("SECOND_ORDER_MATTERS", "true").strip().lower()
            in ("1", "true", "yes", "y"))


def _combo_signature(first: str, seconds: list) -> tuple:
    names = [os.path.basename(s) for s in seconds]
    if not _order_matters():
        names = sorted(names)  # coi (A,B) == (B,A)
    return (os.path.basename(first),) + tuple(names)  # có thứ tự -> (A,B) != (B,A)


def _total_combos(n_first: int, n_second: int, k: int) -> int:
    if n_second < k:
        return 0
    if _order_matters():
        # Hoán vị P(n,k) = n*(n-1)*...*(n-k+1)  -> có thứ tự
        return n_first * len(list(itertools.permutations(range(n_second), k)))
    # Tổ hợp C(n,k) -> không thứ tự
    return n_first * len(list(itertools.combinations(range(n_second), k)))


def pick_unique_combo(first_dir: str, second_dir: str, second_count: int = 2):
    """Chọn tổ hợp (mở đầu, [2 clip]) chưa dùng. Reset khi đã dùng hết."""
    firsts = _list_files(first_dir, VIDEO_EXTS)
    seconds = _list_files(second_dir, VIDEO_EXTS)
    if not firsts:
        raise FileNotFoundError(f"Không có video mở đầu trong: {first_dir}")
    if len(seconds) < second_count:
        raise FileNotFoundError(
            f"Cần ≥{second_count} clip trong {second_dir} (đang có {len(seconds)})"
        )

    total = _total_combos(len(firsts), len(seconds), second_count)
    used = _load_used()
    if len(used) >= total:
        print("♻️  Đã dùng hết mọi tổ hợp video -> reset danh sách chống trùng.")
        used = set()

    # Thử ngẫu nhiên tối đa nhiều lần để tránh trùng.
    for _ in range(2000):
        first = random.choice(firsts)
        pick = random.sample(seconds, second_count)
        sig = _combo_signature(first, pick)
        if sig not in used:
            used.add(sig)
            _save_used(used)
            return first, pick
    # Hiếm khi tới đây; lấy đại 1 tổ hợp.
    first = random.choice(firsts)
    return first, random.sample(seconds, second_count)


# ------------------------------------------------------------- chuẩn hoá clip
def _normalize(clip, size):
    """Phủ đầy khung 9:16 rồi crop giữa (cover-crop), bỏ audio gốc."""
    tw, th = size
    scale = max(tw / clip.w, th / clip.h)
    clip = clip.fx(vfx.resize, scale)
    clip = clip.fx(vfx.crop, width=tw, height=th,
                   x_center=clip.w / 2, y_center=clip.h / 2)
    return clip.without_audio()


def _concat_with_fade(clips, fade: float):
    """Ghép các clip với crossfade + fade-in/out đầu-cuối.

    fade <= 0 -> cắt thẳng (nối liền, nhịp nhanh).
    """
    if fade <= 0 or len(clips) < 2:
        final = concatenate_videoclips(clips, method="compose")
    else:
        # Không để fade dài hơn nửa clip ngắn nhất.
        fade = min(fade, min(c.duration for c in clips) / 2)
        faded = [clips[0]]
        for c in clips[1:]:
            faded.append(c.crossfadein(fade))  # clip sau mờ hiện lên
        # padding âm -> các clip chồng lấn nhau đúng bằng thời gian fade.
        final = concatenate_videoclips(faded, method="compose", padding=-fade)

    if fade > 0:
        # Mở đầu tối -> sáng dần, kết thúc sáng -> tối dần cho gọn.
        final = final.fx(vfx.fadein, min(fade, final.duration / 2))
        final = final.fx(vfx.fadeout, min(fade, final.duration / 2))
    return final


# ------------------------------------------------------------------ nhạc nền
def _attach_music(clip, music_dir: str):
    music_files = _list_files(music_dir, MUSIC_EXTS)
    if not music_files:
        print("⚠️  Không có file nhạc -> video sẽ không có tiếng.")
        return clip, None
    music_path = random.choice(music_files)
    print(f"🎵 Nhạc nền: {os.path.basename(music_path)}")
    music = AudioFileClip(music_path)
    dur = clip.duration
    if music.duration < dur:
        music = afx.audio_loop(music, duration=dur)  # lặp cho đủ dài
    else:
        music = music.subclip(0, dur)                # cắt đúng độ dài video
    return clip.set_audio(music), music


# --------------------------------------------------------------- hàm chính
def build_composite_video(
    first_dir: str,
    second_dir: str,
    music_dir: str,
    output_path: str,
    target_size=(1080, 1920),
    fps: int = 30,
    second_count: int = 2,
) -> str:
    """Ghép video: 1 mở đầu + N clip second + nhạc. Trả về output_path."""
    first, seconds = pick_unique_combo(first_dir, second_dir, second_count)
    print(f"🎬 Mở đầu : {os.path.basename(first)}")
    for i, s in enumerate(seconds, 1):
        print(f"   Clip {i} : {os.path.basename(s)}")

    to_close = []
    try:
        raw = [VideoFileClip(p) for p in [first, *seconds]]
        to_close.extend(raw)
        clips = [_normalize(c, target_size) for c in raw]
        to_close.extend(clips)

        fade = float(os.getenv("FADE_DURATION", "0.5"))  # giây; 0 = cắt thẳng
        final = _concat_with_fade(clips, fade)
        to_close.append(final)

        final, music = _attach_music(final, music_dir)
        if music is not None:
            to_close.append(music)

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            fps=fps,
            threads=os.cpu_count() or 2,
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


def combo_stats(first_dir: str, second_dir: str, second_count: int = 2) -> dict:
    """Thống kê số tổ hợp có thể / đã dùng (để biết kho video đủ dày chưa)."""
    firsts = _list_files(first_dir, VIDEO_EXTS)
    seconds = _list_files(second_dir, VIDEO_EXTS)
    total = _total_combos(len(firsts), len(seconds), second_count)
    return {"firsts": len(firsts), "seconds": len(seconds),
            "total_combos": total, "used": len(_load_used()),
            "order_matters": _order_matters()}
