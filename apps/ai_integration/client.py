import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings


class GeminiError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _extract_output_text(payload):
    """Lấy phần văn bản JSON từ phản hồi Gemini generateContent."""

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini không trả về candidate.")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text") for part in parts if isinstance(part.get("text"), str)]
    if not texts:
        raise ValueError("Gemini không trả về nội dung văn bản.")
    return "".join(texts)


def chat_completion(prompt):
    """Gọi Gemini REST API và yêu cầu kết quả là một JSON object."""

    if not settings.GEMINI_API_KEY:
        raise GeminiError("NOT_CONFIGURED")
    body = json.dumps(
        {
            "systemInstruction": {
                "parts": [{"text": "Bạn là trợ lý cho SPK Hotel. Luôn trả lời bằng một JSON object hợp lệ."}]
            },
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
    ).encode("utf-8")
    model = quote(settings.GEMINI_MODEL.removeprefix("models/"), safe="-._")
    request = Request(
        f"{settings.GEMINI_BASE_URL.rstrip('/')}/v1beta/models/{model}:generateContent",
        data=body,
        headers={
            "x-goog-api-key": settings.GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.GEMINI_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _extract_output_text(payload)
    except (TimeoutError, socket.timeout):
        raise GeminiError("TIMEOUT")
    except HTTPError as error:
        raise GeminiError(f"HTTP_{error.code}")
    except (URLError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        raise GeminiError("API_ERROR")
