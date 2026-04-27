import re
from typing import Any, Dict, List, Optional

def parse_ai_output(raw_text: str) -> List[Dict[str, str]]:
    if not raw_text:
        return []

    q_pattern = r"<(?:[Qq]uestion)>(.*?)(?:</[Qq]uestion>|(?=<[Qq]uestion>|<[Aa]nswer>|$))"
    a_pattern = r"<(?:[Aa]nswer)>(.*?)(?:</[Aa]nswer>|(?=<[Qq]uestion>|<[Aa]nswer>|$))"

    questions = re.findall(q_pattern, raw_text, re.DOTALL)
    answers = re.findall(a_pattern, raw_text, re.DOTALL)

    if not questions:
        return [{"question": raw_text.strip(), "answer": ""}]

    out: List[Dict[str, str]] = []
    for i, q_raw in enumerate(questions):
        a_raw = answers[i] if i < len(answers) else ""
        out.append(
            {
                "question": re.sub(r"</?[Qq]uestion/?>", "", q_raw).strip(),
                "answer": re.sub(r"</?[Aa]nswer/?>", "", a_raw).strip(),
            }
        )
    return out