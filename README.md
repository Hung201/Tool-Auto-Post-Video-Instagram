# Instagram Auto Poster 🎬🤖

Tool tự động: **Sinh text bằng AI → Xử lý video né trùng lặp → Chờ ngẫu nhiên 1–2h → Đăng Reels lên Instagram**, chạy lặp liên tục.

Mặc định dùng **Instagram Graph API chính thức của Meta** (`PUBLISHER=graph`). Vẫn giữ tùy chọn `instagrapi` (private API) nếu cần.

## ⚡ Cách đăng bài (quan trọng)

**Graph API chính thức KHÔNG nhận file video local** — video phải nằm ở một **URL public HTTPS**, rồi Instagram tự tải về. Vì vậy luồng đăng là:

```
video đã xử lý → upload lên media host (Cloudinary/web của bạn) → gửi URL cho Graph API → publish → xoá file tạm trên host
```

### Điều kiện dùng Graph API
1. Tài khoản Instagram phải là **Business** hoặc **Creator**.
2. IG đó **liên kết với 1 Facebook Page**.
3. Tạo app tại [Meta for Developers](https://developers.facebook.com) → lấy:
   - **`ig_user_id`** = Instagram Business Account ID.
   - **`access_token`** = Long-lived Page Access Token, có quyền `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`.

> Lấy nhanh: dùng [Graph API Explorer](https://developers.facebook.com/tools/explorer/) để lấy token, rồi gọi `GET /me/accounts` → `GET /{page_id}?fields=instagram_business_account` để ra `ig_user_id`. Đổi token sang long-lived (60 ngày) để đỡ phải cấp lại thường xuyên.

### Media host (chọn 1)
- **Cloudinary** (khuyên dùng): tạo tài khoản free tại cloudinary.com, copy `CLOUDINARY_URL` vào `.env`. Tool tự upload rồi tự xoá sau khi đăng.
- **public_dir**: nếu bạn có sẵn web server, đặt `PUBLIC_BASE_URL` + `PUBLIC_SERVE_DIR`, tool copy file vào thư mục đó.

## Cấu trúc

```
tool-dang-insta-tu-dong/
├── main.py                        # Orchestrator: xoay vòng account + hàng đợi
├── modules/
│   ├── ai_generator.py            # Sinh text bằng Claude (mặc định) / Gemini
│   ├── video_processor.py         # Né trùng lặp: visual + audio + hash/metadata
│   ├── scheduler.py               # Chờ ngẫu nhiên
│   ├── account_manager.py         # Nạp & xoay vòng nhiều tài khoản
│   ├── queue_manager.py           # Hàng đợi video + prompt (không lặp liền nhau)
│   ├── history.py                 # Ghi lịch sử + chống trùng nội dung
│   ├── graph_publisher.py         # Đăng Reels qua Graph API CHÍNH THỨC
│   ├── media_host.py              # Đưa video lên URL public (cho Graph API)
│   └── instagram_publisher.py     # (tùy chọn) đăng qua instagrapi private API
├── config/accounts.example.json   # Mẫu cấu hình nhiều tài khoản
├── prompts.txt                    # Nhiều prompt (mỗi dòng 1 cái)
├── inputs/                        # Nhiều video gốc
├── music/                         # (tùy chọn) nhạc nền
├── sessions/                      # session.json tự tạo cho từng account
├── history.json                   # Lịch sử bài đã đăng (tự tạo)
├── requirements.txt
└── .env.example
```

## 3 tính năng nâng cao

**1. Xoay vòng nhiều tài khoản** — Copy `config/accounts.example.json` → `config/accounts.json`, khai báo danh sách account (mỗi cái có thể có hashtags / prompt / lịch / nhạc riêng). Tool đăng luân phiên từng account; mỗi account có **session riêng** trong `sessions/<user>.json`. Không có file này thì tự fallback về 1 account trong `.env`.

**2. Hàng đợi video + prompt** — Bỏ nhiều video vào `inputs/` và nhiều prompt vào `prompts.txt`. Tool xoay vòng ngẫu nhiên, **không lặp lại item vừa dùng**. Account có thể trỏ `prompt_file` riêng.

**3. Lịch sử chống trùng** — Mỗi bài được ghi vào `history.json` (thời gian, account, video, text, media_pk). Trước khi đăng, nếu text AI trùng nội dung account đó đã đăng (đã chuẩn hoá bỏ dấu câu/hoa-thường), tool **tự sinh lại** tối đa 5 lần.

## Cài đặt

**1. Cài FFmpeg** (bắt buộc — moviepy cần để encode video):
- Windows: tải tại https://www.gyan.dev/ffmpeg/builds/ và thêm `bin` vào PATH, hoặc `winget install Gyan.FFmpeg`.
- Kiểm tra: `ffmpeg -version`.

**2. Cài thư viện Python:**

```bash
pip install -r requirements.txt
```

**3. Tạo file cấu hình:**
- Copy `.env.example` → `.env`. Sinh text dùng **Claude** (`AI_PROVIDER=anthropic`) đọc `ANTHROPIC_API_KEY` từ môi trường (hoặc thêm vào `.env`). Điền `MEDIA_HOST` + Cloudinary, và (nếu 1 account) `IG_USER_ID` + `IG_ACCESS_TOKEN`.
- Nhiều tài khoản: copy `config/accounts.example.json` → `config/accounts.json`, mỗi account điền `ig_user_id` + `access_token` riêng.

**4. Bỏ video gốc vào `inputs/` và chỉnh prompt trong `prompts.txt`.**

## Chạy

```bash
python main.py
```

- Test 1 lần trước: đặt `RUN_MODE=once` trong `.env` để chạy thử một bài rồi thoát.
- Chạy tự động liên tục: đặt `RUN_MODE=loop`.

## Cơ chế né trùng lặp (Anti-Duplicate)

| Yếu tố Instagram quét | Cách tool xử lý |
|---|---|
| **Hash / Metadata** | Re-encode + `-map_metadata -1` (xoá sạch Exif), bitrate ngẫu nhiên → đổi MD5 |
| **Visual** | Text overlay đổi vị trí/kích thước, tốc độ ±1–2%, brightness/contrast, zoom-crop nhẹ |
| **Audio** | Đổi tốc độ audio theo video, hoặc thay nhạc nền ngẫu nhiên (`USE_RANDOM_MUSIC=true`) |

Text được render bằng **PIL** nên **không cần cài ImageMagick** (khác với `TextClip` mặc định của moviepy).

## Lưu ý ⚠️

**Khi dùng Graph API (`PUBLISHER=graph`) — an toàn, được Meta cho phép:**
- **Access token hết hạn**: Long-lived token sống ~60 ngày. Hết hạn phải cấp lại (cân nhắc thêm cron tự refresh token).
- **Giới hạn đăng**: Graph API cho **tối đa 50 bài/24h** mỗi tài khoản. Lịch 1–2h/bài (~12–24 bài/ngày) nằm trong giới hạn.
- **Yêu cầu**: tài khoản phải là Business/Creator + liên kết Facebook Page. Reels: MP4/MOV, tỷ lệ khuyến nghị 9:16, ≤ 15 phút, ≤ 1GB.
- Video phải công khai đủ lâu để Instagram tải về (tool tự chờ `status=FINISHED` rồi mới xoá).

**Nếu dùng `instagrapi` (`PUBLISHER=instagrapi`) — private API, KHÔNG chính thức:**
- Cài thêm: `pip install instagrapi`.
- Tool tự lưu `sessions/<user>.json` để giảm checkpoint/2FA. Có rủi ro vi phạm ToS → tự chịu trách nhiệm.
- Với acc mới nên giãn `MIN_HOURS=3`, `MAX_HOURS=5` trong 1–2 tuần đầu để "ấm" tài khoản.
