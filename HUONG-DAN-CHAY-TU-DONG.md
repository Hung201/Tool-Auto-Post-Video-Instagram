# 🔁 HƯỚNG DẪN CHẠY TOOL TỰ ĐỘNG (không cần deploy)

Chạy ngay trên **máy tính của bạn** — không thuê server, không deploy.

> ⚠️ **Điều kiện:** máy phải **BẬT + có mạng** thì tool mới chạy. Máy tắt/ngủ → tool dừng.
> Cần chạy 24/7 kể cả khi tắt máy → phải dùng server (đó mới là "deploy").

---

## BƯỚC 0 — Chuẩn bị (làm 1 lần)
Trong `.env` đặt:
```
RUN_MODE=loop
```
Cài thư viện múi giờ (cho tính năng giờ vàng):
```bash
pip install tzdata
```

---

## CÁCH 1 — Đơn giản nhất: chạy trong terminal
Mở terminal ở thư mục tool, chạy:
```bash
python main.py
```
- Tool chạy liên tục: canh giờ vàng US → ghép video → đăng → chờ ngẫu nhiên → lặp.
- **Giữ cửa sổ mở.** Đóng cửa sổ = tool dừng.
- Dừng: bấm `Ctrl + C`.

👉 Hợp để **test/chạy thử vài ngày**. Nhược điểm: đóng máy/cửa sổ là dừng.

---

## CÁCH 2 — Tự động hẳn (KHUYÊN DÙNG): file .bat + tự khởi động lại
Đã có sẵn file **`run_tool.bat`** — nó chạy tool và **tự bật lại nếu lỗi/crash**, ghi log vào `logs\tool.log`.

**Chạy thủ công:** nháy đúp `run_tool.bat` (hoặc chạy trong terminal). Tool chạy nền, tự phục hồi.

### Cho tự chạy MỖI KHI BẬT MÁY — dùng Task Scheduler
1. Bấm **Start** → gõ **Task Scheduler** → mở.
2. Bên phải bấm **Create Task** (không phải "Basic Task").
3. Tab **General:**
   - Name: `Instagram Auto Poster`
   - Chọn **Run whether user is logged on or not**
   - Tích **Run with highest privileges**
4. Tab **Triggers** → **New** → Begin the task: **At startup** (hoặc **At log on**) → OK
5. Tab **Actions** → **New**:
   - Action: **Start a program**
   - Program/script: `E:\Hung\tool-dang-insta-tu-dong\run_tool.bat`
   - Start in: `E:\Hung\tool-dang-insta-tu-dong`
6. Tab **Settings:**
   - Tích **If the task fails, restart every: 1 minute**
   - Bỏ tích **Stop the task if it runs longer than...** (để nó chạy mãi)
7. Bấm **OK** (có thể hỏi mật khẩu Windows).

→ Từ giờ, cứ **bật máy là tool tự chạy**, không cần mở gì cả. Lỗi thì tự bật lại.

---

## BƯỚC QUAN TRỌNG — Đừng để máy ngủ
Nếu máy ngủ (sleep) thì tool dừng. Tắt sleep:
- **Settings → System → Power** → **Screen and sleep** → đặt **Sleep = Never** (khi cắm điện).
- Laptop: cắm sạc, đặt "When plugged in, PC goes to sleep = Never".

---

## Theo dõi tool đang chạy
- Xem log: mở file **`logs\tool.log`** (Cách 2) — thấy bài đã đăng, lỗi (nếu có).
- Xem video đã tạo: thư mục **`E:\Hung\drop-shipping\output`**.
- Xem lịch sử: **`history.json`**.

---

## Dừng tool
- Cách 1: `Ctrl + C` trong cửa sổ.
- Cách 2 (Task Scheduler): mở Task Scheduler → tìm task → **End** / **Disable**. Và tắt cửa sổ `run_tool.bat` nếu đang mở.

---

## Tóm tắt lựa chọn
| Cách | Ưu | Nhược |
|---|---|---|
| **1. Terminal** | Đơn giản, thấy log trực tiếp | Đóng cửa sổ/máy = dừng |
| **2. .bat + Task Scheduler** | Tự chạy khi bật máy, tự phục hồi lỗi | Cần set 1 lần; máy vẫn phải bật |

> Muốn chạy **kể cả khi tắt máy** → chỉ còn cách thuê **VPS giá rẻ** (~vài $/tháng) rồi copy tool lên đó chạy — nhưng đó là "deploy", nằm ngoài yêu cầu hiện tại.
