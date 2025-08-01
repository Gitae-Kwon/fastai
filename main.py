from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os, http.client, json, uuid
# ↓↓↓ 새로 추가 ↓↓↓
from fastapi.staticfiles import StaticFiles
# ────────────────────────────────────────────

load_dotenv()
app = FastAPI(title="Clova Summarizer API")

# 콘솔에서 본 Host/Path
HOST = "clovastudio.apigw.ntruss.com"
PATH = "/testapp/v1/summarization"    # ← 반드시 내 워크스페이스 ID로 교체

app = FastAPI(title="Clova Summarizer API")

class CompletionExecutor:
    def __init__(self, api_key: str, request_id: str | None = None):
        self.api_key = api_key
        self.request_id = request_id or str(uuid.uuid4())

    def execute(self, payload: dict) -> dict:
        headers = {
            "Content-Type": "application/json",
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id
        }
        conn = http.client.HTTPSConnection(HOST)
        conn.request("POST", PATH, json.dumps(payload), headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        conn.close()
        return data

@app.get("/")
def root():
    return {"message": "FastAPI is live 🎉"}

@app.post("/summarize")
def summarize(text: str):
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="입력 텍스트가 비어 있습니다.")

    api_key = os.getenv("CLOVA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API 키가 설정되지 않았습니다.")

    executor = CompletionExecutor(api_key=api_key)
    payload = {
        "texts": [text],
        "segMinSize": 300,
        "includeAiFilters": False,
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000
    }
    result = executor.execute(payload)

    if result.get("status", {}).get("code") == "20000" and "text" in result.get("result", {}):
        return {"summary": result["result"]["text"]}

    raise HTTPException(status_code=500, detail=result)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
