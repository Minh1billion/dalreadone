from app.llm.llm_engine import call_json
from app.llm.chains.eda.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.llm.chains.eda.context_builder import build_context

import json

def analyze(eda_report: dict) -> dict:
    context = build_context(eda_report)
    prompt = USER_PROMPT_TEMPLATE.format(context=json.dumps(context, ensure_ascii=False))
    raw = call_json(prompt=prompt, system=SYSTEM_PROMPT)
    return json.loads(raw)