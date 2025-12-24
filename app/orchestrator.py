import json, os
from pathlib import Path
from dotenv import load_dotenv
from schema import State, ResearchOut, PricingOut, ContentOut
from localai_client import chat_completion

load_dotenv()
STATE_PATH = os.getenv("STATE_PATH","/app/app/data/state.json")
PROMPTS = Path(__file__).parent / "prompts"

SYSTEM_PROMPT = "Du returnerer KUN gyldig JSON. Ingen ekstra tekst."

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
    return json.loads(raw.strip().strip("`").replace("json","",1))

def main():
    s = load_state()

    if s.stage=="INIT":
        out = ResearchOut(**run_agent("research.txt", s.model_dump()))
        s.research = out
        s.stage = "RESEARCH_DONE" if out.next=="PRICING" else "STOPPED"

    if s.stage=="RESEARCH_DONE":
        out = PricingOut(**run_agent("pricing.txt", s.model_dump()))
        s.pricing = out
        s.stage = "PRICING_DONE" if out.next=="CONTENT" else "STOPPED"

    if s.stage=="PRICING_DONE":
        out = ContentOut(**run_agent("content.txt", s.model_dump()))
        s.content = out
        s.stage = "HUMAN_REVIEW"

    save_state(s)
    print("Stage:", s.stage)

if __name__=="__main__":
    main()
