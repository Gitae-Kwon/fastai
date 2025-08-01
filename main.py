from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
import os, http.client, json, uuid

load_dotenv()

# 콘솔에서 본 Host/Path
HOST = "clovastudio.apigw.ntruss.com"
PATH = "/testapp/v1/summarization"   # ← 워크스페이스 ID로 변경

app = FastAPI(title="Clova Summarizer API")   # ★ 딱 한 번만 선언

# ─── CompletionExecutor ─────────────────────────────────────
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

# 헬스체크는 /health 로 이동 (선택)
@app.get("/health")
def health():
    return {"status": "ok"}

# 요약 엔드포인트
@app.post("/summarize")
def summarize(text: str):
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="빈 텍스트")

    api_key = os.getenv("CLOVA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API 키 없음")

    executor = CompletionExecutor(api_key=api_key)
    payload = {
        "texts": [text],
        "segMinSize": 300,
        "segMaxSize": 1000,
        "includeAiFilters": False,
        "autoSentenceSplitter": True,
        "segCount": -1
    }
    result = executor.execute(payload)

    if result.get("status", {}).get("code") == "20000":
        return {"summary": result["result"]["text"]}

    raise HTTPException(status_code=500, detail=result)

# ★★★ 파일 최하단에 Static mount (app 정의 후 ‘마지막’)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
