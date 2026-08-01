# 📘 HƯỚNG DẪN SỬ DỤNG (dễ hiểu)

Tool này **tự ghép video → chèn chữ né trùng → sinh caption bằng AI → đăng lên Instagram theo lịch**, và lưu lại mọi video để bạn xem.

---

## 1. Cài đặt (làm 1 lần)

**Bước 1 — Cài FFmpeg** (bắt buộc, để xử lý video):
```bash
winget install Gyan.FFmpeg
```
Kiểm tra đã cài được chưa:
```bash
ffmpeg -version
```

**Bước 2 — Cài thư viện Python:**
```bash
pip install -r requirements.txt
```

**Bước 3 — Tạo file cấu hình:** copy `.env.example` thành `.env`, rồi mở `.env` bằng Notepad và điền thông tin (xem mục 3).

---

## 2. Các thư mục video (đặt ở `E:\Hung\drop-shipping`)

| Thư mục | Dùng để làm gì |
|---|---|
| `first-video\` | Các clip **mở đầu** (video luôn bắt đầu bằng 1 clip ngẫu nhiên ở đây) |
| `second-video\` | Các clip **tiếp theo** (lấy ngẫu nhiên 2 clip nối sau clip mở đầu) |
| `music\` | Các file **nhạc nền** (chọn ngẫu nhiên, tự cắt đúng độ dài video) |
| `output\` | Nơi **lưu mọi video đã tạo** — tự sinh ra, để bạn xem lại |

> 💡 Càng nhiều clip trong `second-video` và càng nhiều nhạc trong `music` thì video càng ít trùng.

---

## 3. Điền gì trong file `.env`

| Dòng | Ý nghĩa |
|---|---|
| `PUBLISHER=graph` | Cách đăng: `graph` = API chính thức của Instagram (khuyên dùng) |
| `IG_USER_ID=...` | ID tài khoản Instagram Business (lấy từ Meta for Developers) |
| `IG_ACCESS_TOKEN=...` | Token đăng bài (lấy từ Meta for Developers) |
| `ANTHROPIC_API_KEY` | Đã có sẵn trong máy → dùng Claude sinh caption. Không cần điền lại |
| `MEDIA_HOST=cloudinary` + `CLOUDINARY_URL=...` | Nơi chứa video công khai để Instagram tải về (tạo tài khoản Cloudinary free) |
| `VIDEO_SOURCE=composite` | `composite` = tự ghép video. `single` = lấy 1 file có sẵn |
| `FADE_DURATION=0.5` | Độ mượt chuyển cảnh (giây). `0` = cắt thẳng nhanh |
| `SECOND_COUNT=2` | Số clip tiếp theo (2 = mở đầu + 2 clip) |
| `MIN_HOURS` / `MAX_HOURS` | Khoảng chờ ngẫu nhiên giữa 2 bài (giờ) |
| `RUN_MODE=loop` | `loop` = chạy liên tục. `once` = đăng 1 bài rồi thoát (để test) |

Nhiều tài khoản thì copy `config\accounts.example.json` → `config\accounts.json` và điền danh sách.

---

## 4. 🧪 Các lệnh TEST (chỉ tạo video, KHÔNG đăng)

Dùng để xem video trông thế nào trước khi đăng thật.

| Lệnh | Làm gì |
|---|---|
| `python build_test.py --open` | **Tạo 1 video mẫu rồi tự mở lên xem.** Lệnh hay dùng nhất |
| `python build_test.py` | Tạo video mẫu, lưu vào `output\`, không tự mở |
| `python build_test.py --ai --open` | Tạo video **dùng Claude viết caption thật** rồi mở xem |
| `python build_test.py --text "Cưng quá 🐾" --open` | Tạo video với dòng chữ bạn tự nhập |
| `python build_test.py --stats` | Chỉ **xem còn bao nhiêu tổ hợp video chưa dùng** (không tạo video) |

> Video test được lưu vào `E:\Hung\drop-shipping\output\test_....mp4`

---

## 5. 🚀 Các lệnh CHẠY THẬT (có đăng lên Instagram)

Sửa `RUN_MODE` trong `.env` trước, rồi chạy:

```bash
python main.py
```

| `RUN_MODE` trong `.env` | Kết quả khi chạy `python main.py` |
|---|---|
| `RUN_MODE=once` | **Đăng đúng 1 bài rồi dừng** — dùng để thử đăng thật lần đầu |
| `RUN_MODE=loop` | **Chạy mãi**: cứ 1–2h lại tự ghép video mới + đăng 1 bài, lặp liên tục |

Muốn **dừng** khi đang chạy `loop`: bấm `Ctrl + C` trong cửa sổ lệnh.

---

## 6. Mỗi lần chạy tool làm gì (tự động)

```
1. Chọn ngẫu nhiên: 1 clip mở đầu + 2 clip tiếp theo + 1 nhạc  (không trùng lần trước)
2. Ghép lại, chuyển cảnh fade cho mượt, cắt nhạc đúng độ dài
3. Chỉnh nhẹ tốc độ/độ sáng + xoá metadata  → né bộ quét trùng của Instagram
4. Claude viết 1 câu caption mới (không trùng caption đã đăng)
5. Chèn caption lên video
6. LƯU video vào  E:\Hung\drop-shipping\output\
7. Đăng lên Instagram
8. Chờ ngẫu nhiên 1–2h  → quay lại bước 1
```

---

## 7. Các file kết quả (tự sinh ra)

| File | Nội dung |
|---|---|
| `E:\Hung\drop-shipping\output\*.mp4` | Tất cả video đã tạo (để bạn xem) |
| `history.json` | Lịch sử: đã đăng bài nào, caption gì, lúc nào |
| `used_combos.json` | Ghi nhớ tổ hợp video đã dùng để **không tạo trùng** |
| `sessions\` | Phiên đăng nhập (chỉ khi dùng `instagrapi`) |

---

## 8. Thứ tự khuyên làm lần đầu

```
1) pip install -r requirements.txt          # cài thư viện
2) python build_test.py --stats             # kiểm tra thấy đủ video/nhạc chưa
3) python build_test.py --open              # xem thử 1 video có ưng không
4) (điền .env: token Instagram + Cloudinary)
5) đặt RUN_MODE=once  →  python main.py      # thử đăng thật 1 bài
6) đặt RUN_MODE=loop  →  python main.py      # bật chạy tự động liên tục
```

---

## 9. Mẹo tránh trùng & an toàn tài khoản

- **Thêm nhạc** vào `music\` (đang có 1 bài) → 4–5 bài là an toàn hẳn.
- **Thêm clip** vào `second-video\` → số tổ hợp tăng vọt (xem bằng `--stats`).
- Tài khoản mới: để `MIN_HOURS=3`, `MAX_HOURS=5` trong 1–2 tuần đầu cho "ấm".
- Graph API cho tối đa 50 bài/ngày mỗi tài khoản — lịch 1–2h/bài nằm trong giới hạn.
