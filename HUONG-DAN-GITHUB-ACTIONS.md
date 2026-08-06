# 🚀 ĐẨY TOOL LÊN GITHUB ACTIONS (chạy tự động, miễn phí, không cần máy bật)

GitHub sẽ tự chạy tool theo giờ đã hẹn, đăng bài lên Instagram — **máy bạn không cần bật**.

Mọi thứ code + video + workflow đã chuẩn bị sẵn. Bạn chỉ cần: **đẩy lên GitHub + thêm secrets + bật chạy.**

---

## CHUẨN BỊ
- Tài khoản **GitHub** (miễn phí): [github.com](https://github.com)
- Cài **Git**: [git-scm.com/download/win](https://git-scm.com/download/win) — hoặc dùng **GitHub Desktop** cho dễ.
- Token Instagram (`IGAA...`), IG_USER_ID, Cloudinary — bạn đã có trong `.env`.

---

## BƯỚC 1 — Tạo repo private trên GitHub
1. Vào [github.com/new](https://github.com/new)
2. Repository name: `insta-auto-poster` (tùy ý)
3. Chọn **Private** ✅ (video + code không công khai)
4. **KHÔNG** tích "Add README"
5. Bấm **Create repository**
6. Copy dòng lệnh GitHub hiện ra (dạng `git remote add origin https://github.com/USERNAME/insta-auto-poster.git`)

---

## BƯỚC 2 — Đẩy code + video lên GitHub

Mở terminal (PowerShell) trong thư mục tool `E:\Hung\tool-dang-insta-tu-dong`, chạy lần lượt:

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USERNAME/insta-auto-poster.git
git push -u origin main
```
> Thay `USERNAME` bằng tên GitHub của bạn. Lần đầu push nó hỏi đăng nhập GitHub.

> ✅ File `.env` (chứa token) **KHÔNG** được đẩy lên (đã có trong `.gitignore`). Yên tâm.
> ✅ Thư mục `media/` (video) **được** đẩy lên — ~196MB, GitHub nhận tốt.

---

## BƯỚC 3 — Thêm Secrets (thông tin bí mật)

Vào repo trên GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Thêm lần lượt các secret sau (Name = tên, Secret = giá trị lấy từ file `.env` của bạn):

| Name | Lấy giá trị từ `.env` |
|---|---|
| `ANTHROPIC_API_KEY` | dòng `ANTHROPIC_API_KEY=...` |
| `IG_USER_ID` | `17841440957870490` |
| `IG_ACCESS_TOKEN` | token `IGAA...` |
| `CLOUDINARY_CLOUD_NAME` | `zqebfg1p` |
| `CLOUDINARY_API_KEY` | dòng `CLOUDINARY_API_KEY=...` |
| `CLOUDINARY_API_SECRET` | dòng `CLOUDINARY_API_SECRET=...` |
| `GEMINI_API_KEY` | (tùy chọn, nếu có — làm AI dự phòng) |

> Bí mật được GitHub mã hoá, không ai xem được, kể cả bạn (chỉ ghi đè).

---

## BƯỚC 4 — Chạy thử ngay (không chờ tới giờ)
1. Vào repo → tab **Actions**
2. Nếu hỏi "enable workflows" → bấm đồng ý
3. Bên trái chọn workflow **Auto Post Instagram**
4. Bên phải bấm **Run workflow** → **Run workflow** (màu xanh)
5. Chờ ~1-2 phút, bấm vào lần chạy để xem log
6. Thấy `✅ ĐĂNG THÀNH CÔNG! Media ID: ...` → vào Instagram kiểm tra 🎉

---

## BƯỚC 5 — Tự động theo lịch
Xong bước 4 là **cron tự chạy** rồi, không cần làm gì thêm. Lịch mặc định (giờ UTC, rơi vào giờ vàng Mỹ): **3 bài/ngày** lúc 17:00, 00:00, 02:00 UTC.

**Đổi số bài/ngày hoặc giờ:** sửa phần `cron` trong `.github/workflows/post.yml`:
```yaml
on:
  schedule:
    - cron: '0 17 * * *'   # mỗi dòng = 1 bài/ngày
    - cron: '0 0 * * *'
    - cron: '0 2 * * *'
```
Thêm/bớt dòng `- cron: '...'` (định dạng: `phút giờ * * *`, giờ UTC). Sửa xong `git add . && git commit -m "doi lich" && git push`.

---

## ⚠️ NHỮNG ĐIỀU QUAN TRỌNG

### 1. Thêm video mới sau này
Vì Actions chạy từ repo, thêm video mới phải đẩy lên GitHub:
```bash
# copy video mới vào media\second-video\ rồi:
git add media
git commit -m "them video moi"
git push
```

### 2. Token hết hạn sau ~60 ngày
Token `IGAA...` sống ~60 ngày. Khi hết, tạo token mới (Generate token trong app Meta) rồi **cập nhật secret `IG_ACCESS_TOKEN`** trên GitHub (Settings → Secrets → sửa). (Muốn tự động gia hạn, báo tôi thêm workflow refresh.)

### 3. Đừng chạy song song máy + Actions
Nếu vừa chạy `python main.py` trên máy vừa để Actions chạy → 2 nơi cùng sửa `used_combos.json` gây xung đột git. **Chọn 1 nơi** (khuyên: chỉ Actions).

### 4. Giới hạn miễn phí
Repo private: 2000 phút Actions/tháng. Mỗi lần chạy ~2-3 phút × 3 bài/ngày × 30 ngày ≈ 270 phút → **thừa sức**.

---

## Kiểm tra & theo dõi
- **Lịch sử chạy:** repo → tab **Actions** → xem từng lần (xanh = ok, đỏ = lỗi, bấm vào xem log).
- **Bài đã đăng:** file `history.json` trong repo (Actions tự cập nhật).
- **Lỗi:** bấm vào lần chạy đỏ → xem bước nào lỗi → gửi tôi log.

---

## Tóm tắt
```
1. Tạo repo private
2. git push (code + media)
3. Thêm 6 secrets
4. Actions → Run workflow (test)
5. Xong → cron tự chạy 3 bài/ngày vào giờ vàng Mỹ
```
Máy bạn tắt cũng không sao — GitHub lo hết. 🎉
