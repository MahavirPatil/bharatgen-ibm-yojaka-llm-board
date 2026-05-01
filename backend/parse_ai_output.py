import json
import re
from typing import Any, Dict, List


def _strip_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned


def _extract_json_payload(raw_text: str) -> Any:
    cleaned = _strip_code_fences(raw_text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    array_match = re.search(r"\[[\s\S]*\]", cleaned)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except Exception:
            pass

    object_match = re.search(r"\{[\s\S]*\}", cleaned)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except Exception:
            pass

    return None


def parse_ai_output(raw_text: str) -> List[Dict[str, Any]]:
    if not raw_text:
        return []

    parsed_json = _extract_json_payload(raw_text)
    if isinstance(parsed_json, dict):
        if isinstance(parsed_json.get("questions"), list):
            parsed_json = parsed_json["questions"]
        else:
            parsed_json = [parsed_json]

    if isinstance(parsed_json, list):
        normalized: List[Dict[str, Any]] = []
        for item in parsed_json:
            if not isinstance(item, dict):
                continue
            rubric = item.get("rubric")
            answer = item.get("answer", "")
            if not answer and isinstance(rubric, dict):
                answer = rubric.get("answer", "")
            normalized.append(
                {
                    "question": str(item.get("question", "")).strip(),
                    "answer": str(answer or "").strip(),
                    "rubric": rubric,
                }
            )
        if normalized:
            return normalized

    q_pattern = r"<(?:[Qq]uestion)>(.*?)(?:</[Qq]uestion>|(?=<[Qq]uestion>|<[Aa]nswer>|$))"
    a_pattern = r"<(?:[Aa]nswer)>(.*?)(?:</[Aa]nswer>|(?=<[Qq]uestion>|<[Aa]nswer>|$))"

    questions = re.findall(q_pattern, raw_text, re.DOTALL)
    answers = re.findall(a_pattern, raw_text, re.DOTALL)

    if not questions:
        return [{"question": raw_text.strip(), "answer": ""}]

    out: List[Dict[str, Any]] = []
    for i, q_raw in enumerate(questions):
        a_raw = answers[i] if i < len(answers) else ""
        out.append(
            {
                "question": re.sub(r"</?[Qq]uestion/?>", "", q_raw).strip(),
                "answer": re.sub(r"</?[Aa]nswer/?>", "", a_raw).strip(),
            }
        )
    return out