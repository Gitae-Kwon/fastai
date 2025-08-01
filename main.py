from fastapi import FastAPI, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os, http.client, json, uuid

load_dotenv()

# 콘솔 REST API 문서에서 확인한 값으로 교체
HOST = "clovastudio.apigw.ntruss.com"
PATH = "/testapp/v1/summarization"         # ← testapp 부분을 워크스페이스 ID로

app = FastAPI(title="Clova Summarizer API")

# ────────────────────── Clova 호출 래퍼 ──────────────────────
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
# ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summarize")
def summarize(text: str = Form(...)):                 # ← 프런트에서 보내는 form-data 받기
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="빈 텍스트")

    api_key = os.getenv("CLOVA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API 키 없음")

    executor = CompletionExecutor(api_key)
    payload = {
        "texts": [text],
        "segMinSize": 300,
        "segMaxSize": 1000,
        "includeAiFilters": False,
        "autoSentenceSplitter": True,
        "segCount": -1
    }
    result = executor.execute(payload)

    if result.get("status", {}).get("code") == "20000" and "text" in result["result"]:
        return {"summary": result["result"]["text"]}

    raise HTTPException(status_code=500, detail=result)

# HTML 정적 페이지 서빙
app.mount("/", StaticFiles(directory="static", html=True), name="static")
