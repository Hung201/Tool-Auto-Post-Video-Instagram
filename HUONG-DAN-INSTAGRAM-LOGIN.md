# 🟣 ĐĂNG BẰNG INSTAGRAM LOGIN API (KHÔNG cần Facebook Page)

Đây là API **chính thống của Meta** để đăng Reels **mà không cần Facebook Page**, không cần business account. Chỉ cần Instagram là **Professional** (Business/Creator).

Chạy trên `graph.instagram.com`. Trong tool: đặt `PUBLISHER=instagram`.

---

## PHẦN 0 — Điều kiện
- Instagram `@triskovateam` là **Professional** (bạn đã có).
- **Không cần** Facebook Page, **không cần** liên kết Page.
- Vẫn cần **Cloudinary** (đưa video lên URL công khai — bạn đã có).

---

## PHẦN 1 — Thêm sản phẩm Instagram vào app

1. Vào [developers.facebook.com](https://developers.facebook.com) → **My Apps** → chọn app **Triskova**.
2. Menu trái → **Add Product** → tìm **Instagram** → **Set up**.
3. Chọn mục **API setup with Instagram login** (Instagram API with Instagram Login).

---

## PHẦN 2 — Thêm tài khoản & lấy token

Trong trang **API setup with Instagram login**:
1. Cuộn tới mục **"2. Generate access tokens"**.
2. Bấm **Add account** → đăng nhập Instagram `@triskovateam` → cho phép các quyền
   (`instagram_business_basic`, `instagram_business_content_publish`...).
3. Sau khi thêm, bấm **Generate token** cho tài khoản đó → **copy token** (chuỗi `IGAA...`).

> Token này là **Instagram User Access Token**, KHÁC token Facebook (`EAAT...`).

---

## PHẦN 3 — Lấy IG_USER_ID (kiểu Instagram Login)

Chạy lệnh (thay `TOKEN` = token vừa copy):
```bash
PYTHONIOENCODING=utf-8 python -c "import requests;T='TOKEN';print(requests.get('https://graph.instagram.com/v21.0/me',params={'fields':'user_id,username','access_token':T}).json())"
```
Kết quả:
```
{'user_id': '178414xxxxxxxxx', 'username': 'triskovateam'}
```
→ Lấy số **`user_id`** làm `IG_USER_ID`.

---

## PHẦN 4 — (Khuyên) Đổi token dài hạn 60 ngày

Token vừa tạo sống ngắn. Đổi sang 60 ngày (thay `APP_SECRET` + `TOKEN`):
```bash
PYTHONIOENCODING=utf-8 python -c "import requests;print(requests.get('https://graph.instagram.com/access_token',params={'grant_type':'ig_exchange_token','client_secret':'APP_SECRET','access_token':'TOKEN'}).json())"
```
`APP_SECRET` lấy ở: App Dashboard → **App settings → Basic → App secret**.
Lấy `access_token` trả về → dùng token này cho `.env`.

---

## PHẦN 5 — Điền `.env`

```
PUBLISHER=instagram
IG_USER_ID=178414xxxxxxxxx        ← user_id ở Phần 3
IG_ACCESS_TOKEN=IGAA...            ← token Instagram (Phần 2 hoặc token 60 ngày Phần 4)

# Cloudinary (giữ như cũ)
MEDIA_HOST=cloudinary
CLOUDINARY_CLOUD_NAME=zqebfg1p
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## PHẦN 6 — Đăng thử
```bash
python test_post.py
```
Thấy `✅ ĐĂNG THÀNH CÔNG! Media ID: ...` là xong.

---

## Khác biệt so với đường Facebook Page
| | Facebook Graph API | **Instagram Login API** |
|---|---|---|
| Cần Facebook Page | ✅ Có | ❌ **Không** |
| Cần business account | ✅ (dễ dính hạn chế) | ❌ Không |
| Token | `EAAT...` (Facebook) | `IGAA...` (Instagram) |
| Domain | graph.facebook.com | graph.instagram.com |
| `PUBLISHER` trong .env | `graph` | `instagram` |
