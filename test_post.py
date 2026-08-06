"""Đăng NGAY 1 video lên Instagram để test (bỏ qua lịch chờ).

Luồng: ghép video -> sinh caption AI -> né trùng -> XÁC NHẬN -> đăng.

Chạy:
    python test_post.py            # tạo video + hỏi xác nhận rồi đăng
    python test_post.py --yes      # đăng luôn, không hỏi
    python test_post.py --text "Funny caption"   # tự nhập caption
    python test_post.py --no-post  # chỉ tạo video (xem trước), KHÔNG đăng
"""

import argparse
import os

from dotenv import load_dotenv

load_dotenv()

from modules import history
from modules.account_manager import load_accounts
from modules.ai_generator import generate_ai_text
from modules.video_builder import build_composite_video
from modules.video_processor import process_video_anti_duplicate
from main import (  # tái dùng logic sẵn có của tool
    _publish, _output_path, PUBLISHER,
    FIRST_DIR, SECOND_DIR, BUILD_MUSIC_DIR, SECOND_COUNT,
)

TEMP_COMPOSED = "temp_test_composed.mp4"


def main():
    ap = argparse.ArgumentParser(description="Đăng ngay 1 video test lên Instagram")
    ap.add_argument("--yes", action="store_true", help="Đăng luôn, không hỏi xác nhận")
    ap.add_argument("--text", default=None, help="Tự nhập caption (bỏ qua AI)")
    ap.add_argument("--no-post", action="store_true", help="Chỉ tạo video, không đăng")
    args = ap.parse_args()

    account = load_accounts()[0]
    username = account["username"]
    print("=" * 55)
    print(f"  Tài khoản : {username}")
    print(f"  Publisher : {PUBLISHER}")
    print("=" * 55)

    # 1) Ghép video (mở đầu + clip + nhạc)
    print("\n🧩 Đang ghép video...")
    build_composite_video(FIRST_DIR, SECOND_DIR, BUILD_MUSIC_DIR,
                          TEMP_COMPOSED, second_count=SECOND_COUNT)

    # 2) Caption
    if args.text:
        ai_text = args.text
    else:
        print("🤖 Đang sinh caption bằng AI...")
        ai_text = generate_ai_text(os.getenv(
            "PROMPT_TEXT",
            "Write ONE funny English hook (max 10 words) about needing a pet grooming brush."))
    print(f'📝 Caption: "{ai_text}"')

    # 3) Chèn text + né trùng -> lưu output
    out_path = _output_path(username)
    print("🎬 Đang chèn text & né trùng lặp...")
    process_video_anti_duplicate(TEMP_COMPOSED, out_path, ai_text, use_random_music=False)
    print(f"💾 Đã lưu video: {out_path}")
    if os.path.exists(TEMP_COMPOSED):
        os.remove(TEMP_COMPOSED)

    caption = f"{ai_text}\n\n{account['hashtags']}"

    if args.no_post:
        print("\n⏹️  --no-post: chỉ tạo video, KHÔNG đăng. Mở file trên để xem trước.")
        return

    # 4) Xác nhận trước khi đăng (đăng thật là hành động không thể thu hồi)
    if not args.yes:
        print("\n" + "-" * 55)
        print(f"➡️  SẮP ĐĂNG lên Instagram: @{username}")
        print(f"    Caption:\n{caption}")
        print("-" * 55)
        ans = input("Xác nhận ĐĂNG? (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            print("Đã huỷ. Video vẫn lưu ở thư mục output để bạn xem.")
            return

    # 5) Đăng
    print("\n🚀 Đang đăng lên Instagram...")
    media_pk = _publish(account, out_path, caption)
    history.record_post(username, out_path, ai_text, media_pk, caption)
    print(f"\n✅ ĐĂNG THÀNH CÔNG! Media ID: {media_pk}")


if __name__ == "__main__":
    main()
