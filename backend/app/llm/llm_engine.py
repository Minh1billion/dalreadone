from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.config import Config

llm = ChatGroq(api_key=Config.GROQ_API_KEY, model=Config.GROQ_MODEL_ID)

def call(prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))
    
    return llm.invoke(messages).content

def call_json(prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))
    
    return llm.bind(response_format={"type": "json_object"}).invoke(messages).content

if __name__ == "__main__":
    import json
    from pprint import pprint
    from app.llm.llm_engine import call_json
    from app.llm.chains.eda.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
    from app.llm.chains.eda.context_builder import build_context
 
    path = "../eda_Future of Jobs AI Dataset.csv.json"
 
    def analyze(eda_report: dict) -> dict:
        context = build_context(eda_report)
        prompt = USER_PROMPT_TEMPLATE.format(context=json.dumps(context, ensure_ascii=False))
        raw = call_json(prompt=prompt, system=SYSTEM_PROMPT)
        return json.loads(raw)
 
    with open(path) as f:
        eda_report = json.load(f)
 
    result = analyze(eda_report)
    pprint(result)
    
    with open("analysis_result.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)