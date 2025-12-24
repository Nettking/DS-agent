import json, os
from pathlib import Path
from dotenv import load_dotenv
from schema import ContentOut, PricingOut, ResearchOut, State
from localai_client import chat_completion

load_dotenv()
STATE_PATH = os.getenv("STATE_PATH","/app/app/data/state.json")
PROMPTS = Path(__file__).parent / "prompts"

SYSTEM_PROMPT = "Du returnerer KUN gyldig JSON. Ingen ekstra tekst."


def extract_json_object(raw: str) -> dict:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.replace("```json", "").replace("```", "").strip()
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(s[first : last + 1])
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to parse JSON object from model output. Head: {s[:300]!r}") from err
    raise ValueError(f"No JSON object found in model output. Head: {s[:300]!r}")

def load_state():
    p = Path(STATE_PATH)
    if p.exists():
        return State(**json.loads(p.read_text()))
    s = State()
    save_state(s)
    return s

def save_state(state):
    p = Path(STATE_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(state.model_dump_json(indent=2))

def run_agent(prompt_name, input_json):
    prompt = (PROMPTS/prompt_name).read_text()
    user = prompt.format(input_json=json.dumps(input_json,ensure_ascii=False))
    raw = chat_completion(SYSTEM_PROMPT,user)
    return extract_json_object(raw)

def step_research(state: State) -> State:
    if state.stage != "INIT":
        return state
    output = run_agent("research.txt", state.model_dump())
    research = ResearchOut(**output)
    updated = state.model_copy(deep=True)
    updated.research = research
    updated.stage = "RESEARCH_DONE" if research.next == "PRICING" else "STOPPED"
    return updated

def step_pricing(state: State) -> State:
    if state.stage != "RESEARCH_DONE":
        return state
    output = run_agent("pricing.txt", state.model_dump())
    pricing = PricingOut(**output)
    updated = state.model_copy(deep=True)
    updated.pricing = pricing
    updated.stage = "PRICING_DONE" if pricing.next == "CONTENT" else "STOPPED"
    return updated

def step_content(state: State) -> State:
    if state.stage != "PRICING_DONE":
        return state
    output = run_agent("content.txt", state.model_dump())
    content = ContentOut(**output)
    updated = state.model_copy(deep=True)
    updated.content = content
    updated.stage = "HUMAN_REVIEW"
    return updated

def main():
    s = load_state()

    if s.stage=="INIT":
        s = step_research(s)

    if s.stage=="RESEARCH_DONE":
        s = step_pricing(s)

    if s.stage=="PRICING_DONE":
        s = step_content(s)

    save_state(s)
    print("Stage:", s.stage)

if __name__=="__main__":
    main()
