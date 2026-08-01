"""Hàng đợi xoay vòng cho video gốc và prompt.

- Trộn danh sách rồi lấy lần lượt; hết thì trộn lại (không lặp ngay item vừa dùng).
- Video: quét inputs/. Prompt: từ prompt_file của account, hoặc prompts.txt, hoặc
  prompt đơn trong .env.
"""

import glob
import os
import random


class CyclingQueue:
    """Lấy lần lượt các phần tử theo thứ tự ngẫu nhiên, tránh lặp liền nhau."""

    def __init__(self, items):
        self._items = list(items)
        self._pool = []
        self._last = None

    def __len__(self):
        return len(self._items)

    def next(self):
        if not self._items:
            return None
        if not self._pool:
            self._pool = self._items[:]
            random.shuffle(self._pool)
            # Tránh phần tử đầu trùng phần tử vừa dùng (khi có >1 item).
            if len(self._pool) > 1 and self._pool[0] == self._last:
                self._pool.append(self._pool.pop(0))
        item = self._pool.pop(0)
        self._last = item
        return item


def build_video_queue(inputs_dir: str = "inputs") -> CyclingQueue:
    files = []
    for ext in ("*.mp4", "*.mov", "*.mkv", "*.avi"):
        files.extend(glob.glob(os.path.join(inputs_dir, ext)))
    return CyclingQueue(sorted(files))


def _load_prompts_from_file(path: str) -> list:
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        # Mỗi dòng 1 prompt; bỏ dòng trống và dòng bắt đầu bằng '#'.
        return [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]


def build_prompt_queue(account: dict) -> CyclingQueue:
    """Ưu tiên: prompt_file của account -> prompts.txt -> prompt đơn của account."""
    prompts = _load_prompts_from_file(account.get("prompt_file"))
    if not prompts:
        prompts = _load_prompts_from_file("prompts.txt")
    if not prompts and account.get("prompt"):
        prompts = [account["prompt"]]
    if not prompts:
        prompts = ["Viết 1 câu trích dẫn truyền cảm hứng ngắn gọn dưới 15 từ."]
    return CyclingQueue(prompts)
