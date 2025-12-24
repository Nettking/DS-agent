import json, os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from json_utils import extract_json_object
from localai_client import chat_completion
from schema import ContentOut, PricingOut, ResearchOut, State

load_dotenv()
STATE_PATH = os.getenv("STATE_PATH","/app/app/data/state.json")
PROMPTS = Path(__file__).parent / "prompts"

SYSTEM_PROMPT = "Du returnerer KUN gyldig JSON. Ingen ekstra tekst."


def log_event(state, message: str, level: str = "info"):
    state.audit_log.append(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "stage": state.stage,
            "message": message,
        }
    )


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

class ModelOutputError(ValueError):
    def __init__(self, message: str, raw: str | None = None):
        super().__init__(message)
        self.raw = raw


def run_agent(prompt_name, input_json):
    prompt = (PROMPTS / prompt_name).read_text()
    user = prompt.format(input_json=json.dumps(input_json, ensure_ascii=False))
    raw = chat_completion(SYSTEM_PROMPT, user, temperature=0.0)
    try:
        return extract_json_object(raw), raw
    except Exception as err:
        raise ModelOutputError(f"Failed to parse model output: {err}", raw=raw) from err

def step_research(state: State) -> State:
    if state.stage != "INIT":
        return state
    output, _raw = run_agent("research.txt", state.model_dump())
    research = ResearchOut(**output)
    updated = state.model_copy(deep=True)
    updated.research = research
    updated.stage = "RESEARCH_DONE" if research.next == "PRICING" else "STOPPED"
    return updated

def step_pricing(state: State) -> State:
    if state.stage != "RESEARCH_DONE":
        return state
    output, _raw = run_agent("pricing.txt", state.model_dump())
    pricing = PricingOut(**output)
    updated = state.model_copy(deep=True)
    updated.pricing = pricing
    updated.stage = "PRICING_DONE" if pricing.next == "CONTENT" else "STOPPED"
    return updated

def step_content(state: State) -> State:
    if state.stage != "PRICING_DONE":
        return state
    output, _raw = run_agent("content.txt", state.model_dump())
    content = ContentOut(**output)
    updated = state.model_copy(deep=True)
    updated.content = content
    updated.stage = "HUMAN_REVIEW"
    return updated

def main():
    s = load_state()

    try:
        if s.stage == "INIT":
            s = step_research(s)

        if s.stage == "RESEARCH_DONE":
            s = step_pricing(s)

        if s.stage == "PRICING_DONE":
            s = step_content(s)
    except Exception as err:
        raw_head = None
        if hasattr(err, "raw") and err.raw:
            raw_head = repr(err.raw[:500])
        message = f"Error while running step: {err}"
        if raw_head:
            message = f"{message} | raw_head={raw_head}"
        log_event(s, message, level="error")
        save_state(s)
        print(message)
        return

    save_state(s)
    print("Stage:", s.stage)

if __name__=="__main__":
    main()
