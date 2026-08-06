# 🔑 HƯỚNG DẪN LẤY IG_USER_ID + IG_ACCESS_TOKEN (chi tiết A–Z)

Tool đăng qua **Instagram Graph API** cần 2 thứ trong `.env`:
- `IG_ACCESS_TOKEN` — token có quyền đăng bài
- `IG_USER_ID` — **Instagram Business Account ID** (dạng `17841...`), KHÔNG phải Facebook Page ID

> ⚠️ Hiện tại `IG_USER_ID` của bạn đang là **Page ID `1209104595620298`** (sai) và Page "Triskova" **chưa nối Instagram** → đó là lý do đăng lỗi. Làm Phần 0 trước.

---

## PHẦN 0 — Điều kiện bắt buộc (đang thiếu)

### 0.1 Chuyển Instagram sang Professional
Trên app **Instagram** (`@Triskova`):
1. Vào trang cá nhân → **☰ (menu)** → **Settings and privacy**
2. Tìm **Account type and tools** → **Switch to professional account**
3. Chọn **Business** (hoặc Creator) → làm theo hướng dẫn tới hết.

### 0.2 Nối Instagram với Facebook Page "Triskova"
Cách chắc nhất qua **Meta Business Suite** (máy tính):
1. Mở [business.facebook.com](https://business.facebook.com)
2. Góc trái chọn đúng tài khoản chứa **Page Triskova**
3. Bấm **Settings (⚙️)** ở góc dưới trái → **Accounts** → **Instagram accounts**
4. Bấm **Add** → **Log in** bằng tài khoản Instagram `@Triskova` → xác nhận kết nối
5. Đảm bảo Instagram này gắn với **Page Triskova** (mục "Connected assets")

> Điều kiện: bạn phải là **Admin** của Page Triskova, và Instagram đã là **Professional** (bước 0.1).

Xong Phần 0 mới sang được Phần 2 (lấy IG_USER_ID).

---

## PHẦN 1 — Lấy IG_ACCESS_TOKEN

1. Mở [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Mục **Meta App** (bên phải) chọn app của bạn (**Triskova**)
3. **User or Page**: để **User Token**
4. Bấm **Add a Permission**, tích đủ 5 quyền:
   - `instagram_basic`
   - `instagram_content_publish`  ← quan trọng nhất
   - `pages_show_list`
   - `pages_read_engagement`
   - `business_management`
5. Bấm **Generate Access Token** → đăng nhập → **chấp nhận TẤT CẢ quyền**
6. Copy chuỗi token trong ô **Access Token** (bắt đầu bằng `EAAT...`)

> Token này chỉ sống ~1–2 tiếng. Muốn dùng lâu dài xem **Phần 4** (đổi 60 ngày).

---

## PHẦN 2 — Lấy IG_USER_ID đúng (17841...)

Sau khi đã nối IG với Page (Phần 0), chạy lệnh sau trong thư mục tool.
**Thay `TOKEN_CUA_BAN`** bằng token vừa copy ở Phần 1:

```bash
PYTHONIOENCODING=utf-8 python -c "import requests;T='TOKEN_CUA_BAN';print(requests.get('https://graph.facebook.com/v21.0/me/accounts',params={'fields':'name,instagram_business_account{id,username}','access_token':T}).json())"
```

Kết quả sẽ dạng:
```
{'data': [{'name': 'Triskova',
           'instagram_business_account': {'id': '17841400000000000', 'username': 'triskova'},
           'id': '1209104595620298'}]}
```

→ Lấy số **`instagram_business_account.id`** (dạng `17841...`). **Đó chính là IG_USER_ID đúng.**

> Nếu KHÔNG thấy `instagram_business_account` → IG chưa nối xong với Page (làm lại Phần 0).

---

## PHẦN 3 — Điền vào file `.env`

```
IG_USER_ID=17841400000000000        ← id 17841... ở Phần 2 (KHÔNG dùng 1209104595620298)
IG_ACCESS_TOKEN=EAAT...              ← token ở Phần 1
IG_USERNAME=Triskova                 ← chỉ là nhãn hiển thị, để gì cũng được
```

---

## PHẦN 4 — (Khuyên) Đổi token dài hạn 60 ngày

Token Explorer hết hạn nhanh. Đổi sang loại sống 60 ngày:

1. Lấy **App ID** + **App Secret**: App Dashboard → **App settings → Basic**
2. Chạy (thay 3 chỗ IN HOA):

```bash
PYTHONIOENCODING=utf-8 python -c "import requests;print(requests.get('https://graph.facebook.com/v21.0/oauth/access_token',params={'grant_type':'fb_exchange_token','client_id':'APP_ID','client_secret':'APP_SECRET','fb_exchange_token':'TOKEN_NGAN'}).json())"
```

3. Lấy `access_token` trả về → dán vào `IG_ACCESS_TOKEN` trong `.env`.

---

## PHẦN 5 — Kiểm tra & đăng

```bash
python check_ig.py       # xác nhận token + IG account OK
python test_post.py      # đăng thử 1 video
```

---

## Tóm tắt nhanh
| Trường | Lấy ở đâu |
|---|---|
| `IG_ACCESS_TOKEN` | Graph API Explorer → Generate Access Token (Phần 1) |
| `IG_USER_ID` | Chạy lệnh `/me/accounts` → `instagram_business_account.id` (Phần 2) |
| Điều kiện | IG là Professional + đã nối Facebook Page (Phần 0) |
