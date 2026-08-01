"""Module sinh nội dung text bằng AI, có TỰ CHUYỂN DỰ PHÒNG (fallback).

Mặc định dùng Claude (Anthropic). Nếu Claude lỗi/hết hạn mức, tự chuyển sang
Gemini (nếu có GEMINI_API_KEY) và ngược lại.

Thứ tự ưu tiên lấy từ AI_PROVIDER (mặc định anthropic).
"""

import os

_INSTRUCTION = (
    "Chỉ trả về đúng nội dung câu nói, không kèm dấu ngoặc kép, "
    "không đánh số, không lời dẫn hay giải thích."
)


def _clean(text: str) -> str:
    text = (text or "").strip().strip('"').strip("'").strip()
    if not text:
        raise RuntimeError("AI trả về nội dung rỗng")
    return text


def has_key(provider: str) -> bool:
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _generate_anthropic(prompt: str) -> str:
    import anthropic  # import trong hàm để không bắt buộc cài nếu chỉ dùng Gemini

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Thiếu ANTHROPIC_API_KEY")

    client = anthropic.Anthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
    base = dict(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": f"{prompt}\n\n{_INSTRUCTION}"}],
    )

    try:
        # 'effort' giúp tiết kiệm token nhưng chỉ có ở model mới.
        resp = client.messages.create(**base, output_config={"effort": "low"})
    except anthropic.BadRequestError as e:
        if "effort" in str(e).lower():
            resp = client.messages.create(**base)  # model cũ -> bỏ effort
        else:
            raise

    if resp.stop_reason == "refusal":
        raise RuntimeError("Yêu cầu bị Claude từ chối (refusal).")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return _clean(text)


def _generate_gemini(prompt: str) -> str:
    from google import genai

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Thiếu GEMINI_API_KEY")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model, contents=f"{prompt}\n\n{_INSTRUCTION}"
    )
    return _clean(response.text)


_GENERATORS = {"anthropic": _generate_anthropic, "gemini": _generate_gemini}


def generate_with_provider(provider: str, prompt: str) -> str:
    """Sinh text bằng đúng 1 provider chỉ định (không fallback)."""
    provider = provider.strip().lower()
    if provider not in _GENERATORS:
        raise ValueError(f"Provider không hợp lệ: {provider}")
    return _GENERATORS[provider](prompt)


def generate_ai_text(prompt: str) -> str:
    """Sinh text; nếu provider chính lỗi -> tự chuyển sang provider còn lại.

    Ném exception chỉ khi TẤT CẢ provider có key đều lỗi.
    """
    primary = (os.getenv("AI_PROVIDER", "anthropic") or "anthropic").strip().lower()
    order = [primary, "gemini" if primary != "gemini" else "anthropic"]

    last_error = None
    for provider in order:
        if not has_key(provider):
            continue
        try:
            text = generate_with_provider(provider, prompt)
            if provider != primary:
                print(f"   ↪️  Đã tự chuyển sang {provider.upper()} (dự phòng).")
            return text
        except Exception as e:
            last_error = e
            print(f"   ⚠️  {provider.upper()} lỗi: {e} -> thử provider khác...")

    raise RuntimeError(f"Tất cả AI provider đều lỗi. Lỗi cuối: {last_error}")
