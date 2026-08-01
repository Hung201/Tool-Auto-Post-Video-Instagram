"""Test nhanh: ghép video từ first-video + second-video + music, chèn text né-trùng,
LƯU ra file và MỞ xem thử — KHÔNG đăng lên Instagram.

Chạy thẳng:
    python build_test.py                     # dùng câu text mẫu (không tốn API)
    python build_test.py --ai                # sinh text bằng AI (Claude/Gemini)
    python build_test.py --open              # tự mở video sau khi tạo (Windows)
    python build_test.py --text "Cưng quá!"  # tự nhập text overlay
    python build_test.py --stats             # chỉ in thống kê kho video/tổ hợp
"""

import argparse
import os

from dotenv import load_dotenv

from modules.video_builder import build_composite_video, combo_stats
from modules.video_processor import process_video_anti_duplicate

load_dotenv()

# Mặc định trỏ tới kho video của bạn; đổi trong .env nếu cần.
FIRST_DIR = os.getenv("FIRST_VIDEO_DIR", r"E:\Hung\drop-shipping\first-video")
SECOND_DIR = os.getenv("SECOND_VIDEO_DIR", r"E:\Hung\drop-shipping\second-video")
MUSIC_DIR = os.getenv("BUILD_MUSIC_DIR", r"E:\Hung\drop-shipping\music")
SECOND_COUNT = int(os.getenv("SECOND_COUNT", "3"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", r"E:\Hung\drop-shipping\output")

COMPOSED = "test_composed.mp4"


def _final_path():
    import time
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"test_{time.strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}.mp4")


def main():
    parser = argparse.ArgumentParser(description="Test tạo video ghép (không đăng)")
    parser.add_argument("--ai", action="store_true", help="(mặc định) Sinh text bằng AI")
    parser.add_argument("--sample", action="store_true",
                        help="Dùng câu mẫu cố định (không gọi AI, test nhanh)")
    parser.add_argument("--text", type=str, default=None, help="Tự nhập text overlay")
    parser.add_argument("--open", action="store_true", help="Mở video sau khi tạo")
    parser.add_argument("--stats", action="store_true", help="Chỉ in thống kê tổ hợp")
    args = parser.parse_args()

    stats = combo_stats(FIRST_DIR, SECOND_DIR, SECOND_COUNT)
    print("=" * 55)
    print(f"  Kho video: {stats['firsts']} mở đầu | {stats['seconds']} clip second")
    print(f"  Số tổ hợp có thể: {stats['total_combos']} | đã dùng: {stats['used']}")
    print("=" * 55)
    if args.stats:
        return

    # 1) Ghép video + nhạc
    print("\n🔧 Đang ghép video...")
    build_composite_video(FIRST_DIR, SECOND_DIR, MUSIC_DIR, COMPOSED,
                          second_count=SECOND_COUNT)

    # 2) Text overlay — MẶC ĐỊNH dùng AI (giống lúc đăng thật).
    if args.text:
        overlay = args.text
    elif args.sample:
        overlay = "Grooming your pet has never been this easy"
    else:
        print("🤖 Đang sinh text bằng AI...")
        from modules.ai_generator import generate_ai_text
        overlay = generate_ai_text(os.getenv(
            "PROMPT_TEXT",
            "Write ONE funny English hook (max 10 words) about needing a pet grooming brush."))
    print(f'📝 Text overlay: "{overlay}"')

    # 3) Né-trùng + chèn text (giữ nhạc đã ghép -> use_random_music=False)
    print("🎨 Đang chèn text & né trùng lặp...")
    final = _final_path()
    process_video_anti_duplicate(COMPOSED, final, overlay, use_random_music=False)

    if os.path.exists(COMPOSED):
        os.remove(COMPOSED)

    out = os.path.abspath(final)
    print(f"\n✅ Xong! Video test đã lưu: {out}")

    if args.open:
        try:
            os.startfile(out)  # Windows
        except Exception as e:
            print(f"(Không tự mở được: {e})")


if __name__ == "__main__":
    main()
