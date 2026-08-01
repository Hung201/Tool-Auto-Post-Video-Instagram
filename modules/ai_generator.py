"""Module sinh nội dung text bằng AI.

Mặc định dùng Claude (Anthropic API) với ANTHROPIC_API_KEY có sẵn trong môi trường.
Vẫn hỗ trợ Google Gemini qua AI_PROVIDER=gemini.

Mỗi lần gọi trả về một câu độc bản dựa trên prompt -> đảm bảo caption/overlay
không bị trùng lặp giữa các lần đăng.
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


def _generate_anthropic(prompt: str) -> str:
    import anthropic  # import trong hàm để không bắt buộc cài nếu dùng Gemini

    # SDK tự đọc ANTHROPIC_API_KEY từ môi trường (không hardcode key).
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Thiếu ANTHROPIC_API_KEY trong môi trường.")

    client = anthropic.Anthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")

    resp = client.messages.create(
        model=model,
        max_tokens=1024,  # đủ chỗ cho thinking (bật mặc định trên Opus 5) + câu trả lời ngắn
        output_config={"effort": "low"},  # tác vụ đơn giản -> tiết kiệm token
        messages=[{"role": "user", "content": f"{prompt}\n\n{_INSTRUCTION}"}],
    )

    if resp.stop_reason == "refusal":
        raise RuntimeError("Yêu cầu bị AI từ chối (refusal).")

    text = next((b.text for b in resp.content if b.type == "text"), "")
    return _clean(text)


def _generate_gemini(prompt: str) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY trong file .env")

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model, contents=f"{prompt}\n\n{_INSTRUCTION}"
    )
    return _clean(response.text)


def generate_ai_text(prompt: str) -> str:
    """Sinh một câu text ngắn từ AI dựa trên prompt.

    Chọn provider qua AI_PROVIDER: anthropic (mặc định) | gemini.
    Ném exception nếu lỗi để caller xử lý retry.
    """
    provider = (os.getenv("AI_PROVIDER", "anthropic") or "anthropic").strip().lower()
    if provider == "gemini":
        return _generate_gemini(prompt)
    return _generate_anthropic(prompt)
