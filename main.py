"""Tool tự động đăng Instagram — xoay vòng nhiều tài khoản.

Pipeline mỗi chu kỳ:
  chọn account (xoay vòng) -> lấy prompt & video từ hàng đợi ->
  sinh text AI (chống trùng theo lịch sử) -> xử lý video né trùng ->
  đăng Reels -> ghi lịch sử -> chờ ngẫu nhiên -> account tiếp theo.

Cấu hình:
  - config/accounts.json : danh sách tài khoản (xem accounts.example.json)
  - prompts.txt          : nhiều prompt, mỗi dòng 1 cái
  - inputs/              : nhiều video gốc
  - .env                 : GEMINI_API_KEY và giá trị mặc định
"""

import os
import random
import time

from dotenv import load_dotenv

from modules import history
from modules.account_manager import load_accounts
from modules.ai_generator import generate_ai_text
from modules.queue_manager import build_prompt_queue, build_video_queue
from modules.scheduler import random_sleep
from modules.video_processor import process_video_anti_duplicate

load_dotenv()

TEMP_OUTPUT = "temp_processed_video.mp4"
TEMP_COMPOSED = "temp_composed_video.mp4"
MAX_REGEN = 5  # Số lần sinh lại text nếu bị trùng lịch sử.
PUBLISHER = (os.getenv("PUBLISHER", "graph") or "graph").strip().lower()

# composite = tự ghép first-video + second-video + music. single = lấy 1 file trong inputs/.
VIDEO_SOURCE = (os.getenv("VIDEO_SOURCE", "composite") or "composite").strip().lower()
FIRST_DIR = os.getenv("FIRST_VIDEO_DIR", r"E:\Hung\drop-shipping\first-video")
SECOND_DIR = os.getenv("SECOND_VIDEO_DIR", r"E:\Hung\drop-shipping\second-video")
BUILD_MUSIC_DIR = os.getenv("BUILD_MUSIC_DIR", r"E:\Hung\drop-shipping\music")
SECOND_COUNT = int(os.getenv("SECOND_COUNT", "3"))

# Mỗi video tạo ra được lưu lại đây để tiện quan sát (không tự xoá).
OUTPUT_DIR = os.getenv("OUTPUT_DIR", r"E:\Hung\drop-shipping\output")


def _output_path(username: str) -> str:
    """Tạo tên file duy nhất trong OUTPUT_DIR: <user>_<ngày_giờ>_<mã>.mp4"""
    import time
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rand = os.urandom(2).hex()
    safe_user = "".join(c for c in username if c.isalnum() or c in "-_") or "acc"
    return os.path.join(OUTPUT_DIR, f"{safe_user}_{stamp}_{rand}.mp4")


def _publish(account: dict, video_path: str, caption: str) -> str:
    """Đăng video bằng publisher đã cấu hình (graph = chính thức, instagrapi = private)."""
    if PUBLISHER == "graph":
        from modules.graph_publisher import publish_reel
        from modules.media_host import upload_public

        # Graph API cần URL public: upload -> đăng -> dọn file trên hosting.
        public_url, cleanup = upload_public(video_path)
        try:
            return publish_reel(
                ig_user_id=account["ig_user_id"],
                access_token=account["access_token"],
                video_url=public_url,
                caption=caption,
            )
        finally:
            cleanup()

    from modules.instagram_publisher import publish_to_instagram
    return publish_to_instagram(
        video_path, caption,
        username=account["username"], password=account["password"],
        session_file=account["session_file"],
    )


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "y")


def _unique_ai_text(username: str, prompt: str) -> str:
    """Sinh text AI, thử lại tối đa MAX_REGEN lần nếu trùng nội dung account đã đăng."""
    text = generate_ai_text(prompt)
    attempts = 1
    while history.is_duplicate_text(username, text) and attempts < MAX_REGEN:
        print(f"   ↻ Text trùng lịch sử, sinh lại ({attempts}/{MAX_REGEN})...")
        text = generate_ai_text(prompt)
        attempts += 1
    return text


def _prepare_source_video(account: dict, video_queue):
    """Trả về (đường_dẫn_video_gốc, đã_có_nhạc_chưa).

    composite: tự ghép first-video + second-video + music (đã có nhạc).
    single   : lấy 1 file trong hàng đợi inputs/ (chưa có nhạc riêng).
    """
    if VIDEO_SOURCE == "composite":
        from modules.video_builder import build_composite_video
        print("🧩 Đang ghép video (mở đầu + 2 clip + nhạc)...")
        build_composite_video(FIRST_DIR, SECOND_DIR, BUILD_MUSIC_DIR,
                              TEMP_COMPOSED, second_count=SECOND_COUNT)
        return TEMP_COMPOSED, True

    video_input = video_queue.next()
    if not video_input:
        raise FileNotFoundError("Hàng đợi video rỗng — hãy bỏ file vào thư mục inputs/")
    return video_input, False


def run_cycle(account: dict, video_queue, prompt_queues: dict) -> None:
    """Một chu kỳ đăng bài cho 1 account."""
    username = account["username"]
    prompt = prompt_queues[username].next()

    print(f"\n===== [{username}] bài #{history.posts_count(username) + 1} =====")
    print(f"💬 Prompt    : {prompt}")

    video_input, has_music = _prepare_source_video(account, video_queue)
    print(f"🎞️  Video gốc : {video_input}")

    print("🤖 Đang sinh text từ AI...")
    ai_text = _unique_ai_text(username, prompt)
    print(f'   Text: "{ai_text}"')

    print("🎬 Đang xử lý video (né trùng lặp)...")
    out_path = _output_path(username)
    # Nếu composite đã có nhạc thì giữ nguyên (use_random_music=False).
    process_video_anti_duplicate(
        video_input, out_path, ai_text,
        use_random_music=(False if has_music else account["use_random_music"]),
        music_dir=os.getenv("MUSIC_DIR", "music"),
    )
    print(f"💾 Đã lưu video: {out_path}")

    caption = f"{ai_text}\n\n{account['hashtags']}"
    media_pk = _publish(account, out_path, caption)

    # Ghi lịch sử với đường dẫn video đã lưu (giữ lại để quan sát).
    history.record_post(username, out_path, ai_text, media_pk, caption)

    # Chỉ dọn file tạm ghép; video output GIỮ LẠI trong OUTPUT_DIR.
    if os.path.exists(TEMP_COMPOSED):
        os.remove(TEMP_COMPOSED)


def main() -> None:
    run_mode = os.getenv("RUN_MODE", "loop").strip().lower()
    delay_first = _get_bool("DELAY_BEFORE_FIRST", False)

    accounts = load_accounts()
    video_queue = build_video_queue(os.getenv("INPUTS_DIR", "inputs"))
    prompt_queues = {acc["username"]: build_prompt_queue(acc) for acc in accounts}

    api_label = "Graph API (chính thức)" if PUBLISHER == "graph" else "instagrapi (private)"
    print("=" * 60)
    print("  INSTAGRAM AUTO POSTER (multi-account)")
    src_label = "composite (tự ghép)" if VIDEO_SOURCE == "composite" else f"single ({len(video_queue)} file)"
    print(f"  Publisher: {api_label}")
    print(f"  Tài khoản: {', '.join(a['username'] for a in accounts)}")
    print(f"  Nguồn video: {src_label} | Mode: {run_mode}")
    print("=" * 60)

    if run_mode == "once":
        # Đăng đúng 1 bài cho mỗi account rồi thoát (để test).
        for acc in accounts:
            try:
                run_cycle(acc, video_queue, prompt_queues)
            except Exception as e:
                print(f"❌ [{acc['username']}] lỗi: {e}")
        print("✔️  Xong (chế độ once).")
        return

    idx = 0
    first = True
    while True:
        account = accounts[idx % len(accounts)]
        try:
            if not first or delay_first:
                random_sleep(account["min_hours"], account["max_hours"])
            first = False
            run_cycle(account, video_queue, prompt_queues)
        except KeyboardInterrupt:
            print("\n⏹️  Dừng bởi người dùng.")
            break
        except Exception as e:
            print(f"❌ [{account['username']}] Có lỗi: {e}")
            print("   Chờ 5 phút rồi chuyển account/vòng tiếp theo...")
            time.sleep(300)
        finally:
            idx += 1


if __name__ == "__main__":
    main()
