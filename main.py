# main.py
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os, http.client, json, uuid

# 1) .env (로컬) 파일 읽기 ─ 배포 환경에서는 무시
load_dotenv()

app = FastAPI(title="Clova Summarizer API", version="1.0.0")

# ─────────────────────────────────────────────────────────────
# 2) Clova API 래퍼 클래스
# ─────────────────────────────────────────────────────────────
class CompletionExecutor:
    def __init__(self, host: str, api_key: str, request_id: str | None = None):
        self.host = host
        self.api_key = api_key
        self.request_id = request_id or str(uuid.uuid4())

    def execute(self, payload: dict) -> dict:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",   # nv- 로 시작하는 키
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id
        }
        conn = http.client.HTTPSConnection(self.host)
        conn.request("POST", "/v1/api-tools/summarization/v2",
                     json.dumps(payload), headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        conn.close()
        return data
# ─────────────────────────────────────────────────────────────

# 3) 루트 헬스체크 (선택)
@app.get("/")
def root():
    return {"message": "FastAPI is live 🎉"}

# 4) 요약 엔드포인트
@app.post("/summarize")
def summarize(text: str):
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="입력 텍스트가 비어 있습니다.")

    api_key = os.getenv("CLOVA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="서버에 API 키가 설정되지 않았습니다.")

    executor = CompletionExecutor(
        host="clovastudio.stream.ntruss.com",
        api_key=api_key
    )

    payload = {
        "texts": [text],
        "segMinSize": 300,
        "includeAiFilters": False,
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000
    }
    result = executor.execute(payload)

    # 성공 코드 20000 + text 필드 확인
    if result.get("status", {}).get("code") == "20000" and "text" in result.get("result", {}):
        return {"summary": result["result"]["text"]}

    # 실패 시 전체 응답을 detail 로 넘겨 주면 디버깅 쉽다
    raise HTTPException(status_code=500, detail=result)
