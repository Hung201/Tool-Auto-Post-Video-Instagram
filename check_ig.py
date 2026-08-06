"""Kiểm tra token Instagram Graph API trong .env còn sống & đủ quyền đăng không.
KHÔNG đăng gì cả — chỉ gọi các API đọc.

Chạy sau khi thay IG_ACCESS_TOKEN mới:
    python check_ig.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://graph.facebook.com/v21.0"
TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")

NEEDED = {"instagram_basic", "instagram_content_publish",
          "pages_show_list", "pages_read_engagement"}


def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{BASE}/{path}", params=params, timeout=30)
    return r.status_code, r.json()


def main():
    print("=" * 55)
    if not TOKEN:
        print("❌ Thiếu IG_ACCESS_TOKEN trong .env"); return
    print(f"  Token : ...{TOKEN[-6:]}")
    print(f"  IG ID : {IG_USER_ID or '(chưa đặt)'}")
    print("=" * 55)

    # 1) Token có gọi được API không
    code, data = get("me", fields="id,name")
    if "error" in data:
        print(f"\n❌ Token KHÔNG dùng được: {data['error'].get('message')}")
        print("   -> Tạo token mới (xem hướng dẫn), đảm bảo bạn là Admin của app.")
        return
    print(f"\n✅ Token sống. Tài khoản Facebook: {data.get('name')} (id {data.get('id')})")

    # 2) Quyền đã cấp
    code, perms = get("me/permissions")
    granted = {p["permission"] for p in perms.get("data", []) if p.get("status") == "granted"}
    print("\n📋 Quyền đã cấp:")
    for p in sorted(NEEDED):
        print(f"   {'✅' if p in granted else '❌ THIẾU'}  {p}")
    missing = NEEDED - granted
    if missing:
        print(f"\n⚠️  Thiếu quyền: {', '.join(sorted(missing))} -> tạo lại token và tích đủ.")

    # 3) Truy cập được tài khoản IG business không
    if IG_USER_ID:
        code, ig = get(IG_USER_ID, fields="username,followers_count")
        if "error" in ig:
            print(f"\n❌ Không truy cập được IG_USER_ID: {ig['error'].get('message')}")
            print("   -> Kiểm tra IG_USER_ID có đúng là Instagram Business Account ID không.")
        else:
            print(f"\n✅ IG Business: @{ig.get('username')} "
                  f"({ig.get('followers_count', '?')} followers)")

    if not missing and IG_USER_ID:
        print("\n🎉 Có vẻ ổn! Có thể chạy: python test_post.py")


if __name__ == "__main__":
    main()
