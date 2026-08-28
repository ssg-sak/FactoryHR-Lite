import json
import os
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings

MISSING_API_KEY_DETAIL = "AI 기능을 사용하려면 GEMINI_API_KEY가 필요합니다."

SYSTEM_PROMPT = """당신은 FactoryHR Lite의 reporting assistant입니다.
제공된 KPI JSON만 근거로 한국어 요약을 작성합니다.

규칙:
- 제공된 KPI 이외의 사실을 만들지 않습니다.
- 원인을 단정하지 않습니다.
- 상관관계를 인과관계로 표현하지 않습니다.
- 직원을 개인적으로 평가하지 않습니다.
- 해고/채용 같은 인사 결정을 추천하지 않습니다.
- 민감한 개인 특성을 추론하지 않습니다.
- 조직 수준에서 관찰 가능한 패턴만 설명합니다.
- 반드시 additional_data_needed와 cannot_conclude를 채웁니다.
- 의사결정자가 아니라 리포팅 보조자입니다.

출력은 다음 JSON만 반환합니다:
{
  "observations": ["관찰된 패턴"],
  "additional_data_needed": ["추가 확인이 필요한 데이터"],
  "cannot_conclude": ["현재 데이터로 판단할 수 없는 것"]
}
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "observations": {"type": "array", "items": {"type": "string"}},
        "additional_data_needed": {"type": "array", "items": {"type": "string"}},
        "cannot_conclude": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["observations", "additional_data_needed", "cannot_conclude"],
}


def get_gemini_api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or settings.gemini_api_key or "").strip()


def _require_string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise HTTPException(
            status_code=502, detail=f"Gemini response field '{field}' is invalid"
        )
    return [item.strip() for item in value if item.strip()]


def _parse_model_json(raw: str) -> dict[str, list[str]]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502, detail="Gemini response was not valid JSON"
        ) from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Gemini response was not an object")
    return {
        "observations": _require_string_list(data.get("observations"), "observations"),
        "additional_data_needed": _require_string_list(
            data.get("additional_data_needed"), "additional_data_needed"
        ),
        "cannot_conclude": _require_string_list(
            data.get("cannot_conclude"), "cannot_conclude"
        ),
    }


def generate_ai_summary(payload: dict[str, Any]) -> dict[str, list[str]]:
    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail=MISSING_API_KEY_DETAIL)

    model = settings.gemini_model
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "다음 구조화 KPI만 사용하세요. 직원 원문 데이터는 포함되어 있지 않습니다.\n"
                            + json.dumps(payload, ensure_ascii=False, default=str)
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    try:
        response = httpx.post(url, params={"key": api_key}, json=body, timeout=45.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Gemini API request failed") from exc
    if response.status_code >= 400:
        message = ""
        try:
            err = response.json().get("error", {})
            if isinstance(err, dict):
                message = str(err.get("message") or "")
        except (ValueError, TypeError):
            message = ""
        detail = "Gemini API returned an error. Check GEMINI_API_KEY and model name."
        if message:
            detail = f"Gemini API error ({response.status_code}): {message[:300]}"
        raise HTTPException(status_code=502, detail=detail)
    try:
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502, detail="Gemini API response was missing text"
        ) from exc
    return _parse_model_json(text)
