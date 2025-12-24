import json


def extract_json_object(raw: str) -> dict:
    """Extract and parse the first JSON object from a raw model response.

    The function strips whitespace, removes common code fences, and then parses
    the substring between the first opening brace and the last closing brace.
    """

    s = (raw or "").strip()
    if "```" in s:
        s = s.replace("```json", "").replace("```JSON", "").replace("```", "").strip()

    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(s[first : last + 1])

    raise ValueError(f"No JSON object found in model output. Head={s[:500]!r}")
