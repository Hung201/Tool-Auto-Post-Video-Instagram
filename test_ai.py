"""Kiểm tra AI sinh text (đọc cấu hình từ .env), có fallback Claude <-> Gemini.

Chạy:
    python test_ai.py            # test theo cấu hình .env (có tự fallback)
    python test_ai.py gemini     # test RIÊNG Gemini (GEMINI_API_KEY)
    python test_ai.py anthropic  # test RIÊNG Claude (ANTHROPIC_API_KEY)
    python test_ai.py both        # test cả 2 provider
    python test_ai.py gemini 5   # test Gemini, sinh 5 câu
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _key_show(key):
    return (key[:6] + "..." + key[-4:]) if key else "(THIẾU)"


def test_provider(provider: str, prompt: str, n: int) -> bool:
    from modules.ai_generator import generate_with_provider, has_key

    model = (os.getenv("ANTHROPIC_MODEL", "claude-opus-5") if provider == "anthropic"
             else os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    key = os.getenv("ANTHROPIC_API_KEY") if provider == "anthropic" else os.getenv("GEMINI_API_KEY")

    print("\n" + "-" * 55)
    print(f"  Provider : {provider.upper()}  |  Model: {model}")
    print(f"  API key  : {_key_show(key)}")
    print("-" * 55)

    if not has_key(provider):
        print(f"  ⏭️  Bỏ qua (chưa có key trong .env).")
        return False

    ok = 0
    for i in range(1, n + 1):
        try:
            text = generate_with_provider(provider, prompt)
            print(f"  {i}. {text}")
            ok += 1
        except Exception as e:
            print(f"  ❌ Lỗi câu {i}: {e}")
            break

    if ok == n:
        print(f"  ✅ {provider.upper()} HOẠT ĐỘNG ({ok}/{n} câu).")
        return True
    print(f"  ❌ {provider.upper()} KHÔNG hoạt động.")
    return False


def main():
    args = [a.lower() for a in sys.argv[1:]]
    n = next((int(a) for a in args if a.isdigit()), 3)
    prompt = os.getenv("PROMPT_TEXT", "Viết 1 câu quote ngắn về thú cưng, dưới 12 từ.")

    print("=" * 55)
    print("  KIỂM TRA AI SINH TEXT (fallback Claude <-> Gemini)")
    print(f"  Prompt: {prompt}")
    print("=" * 55)

    try:
        from modules.ai_generator import generate_ai_text  # noqa
    except Exception as e:
        print(f"\n❌ Chưa cài thư viện. Chạy: pip install -r requirements.txt\n   {e}")
        return

    if "gemini" in args:
        test_provider("gemini", prompt, n)
    elif "anthropic" in args or "claude" in args:
        test_provider("anthropic", prompt, n)
    elif "both" in args:
        test_provider("anthropic", prompt, n)
        test_provider("gemini", prompt, n)
    else:
        # Theo .env: chạy generate_ai_text (tự fallback nếu provider chính lỗi)
        from modules.ai_generator import generate_ai_text
        primary = (os.getenv("AI_PROVIDER", "anthropic") or "anthropic").lower()
        print(f"\n🤖 Provider chính: {primary.upper()} (tự chuyển dự phòng nếu lỗi)\n")
        try:
            for i in range(1, n + 1):
                print(f"  {i}. {generate_ai_text(prompt)}")
            print(f"\n✅ AI ĐANG HOẠT ĐỘNG ({n} câu).")
        except Exception as e:
            print(f"\n❌ Tất cả provider đều lỗi: {e}")


if __name__ == "__main__":
    main()
