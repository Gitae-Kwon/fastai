from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline, Pipeline
import uvicorn

app = FastAPI()
# ────────────────────  CORS (프런트 ↔ 백엔드 서로 다른 도메인일 때) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 프로덕션에선 ["https://내-도메인"] 으로 좁히세요
    allow_methods=["*"],
    allow_headers=["*"],
)
# ────────────────────  summarizer 로드 (한 번만) ───────────────────────────────────────
# 작은 모델을 사용해야 Render free 인스턴스에서도 메모리/빌드 시간이 짧습니다
summarizer: Pipeline | None = None
def get_summarizer() -> Pipeline:
    global summarizer
    if summarizer is None:
        summarizer = pipeline(
            "summarization",
            model="ainize/kobart-news-summarization",   # 한글용 KoBART
            device=-1                                   # CPU
        )
    return summarizer
# ────────────────────  Request/Response 스키마 ────────────────────────────────────────
class SummaryResponse(BaseModel):
    summary: str
# ────────────────────  API 엔드포인트 ─────────────────────────────────────────────────
@app.post("/summarize", response_model=SummaryResponse)
def summarize(text: str = Form(...)):
    """
    📄 `multipart/form-data` 또는 `application/x-www-form-urlencoded` 로 넘어온
    `text` 필드를 요약해서 돌려줍니다.
    """
    text = text.strip()
    if not text:
        raise HTTPException(422, detail="텍스트를 보내 주세요.")
    try:
        result = get_summarizer()(text, max_length=120, min_length=30, do_sample=False)
        return {"summary": result[0]["summary_text"]}
    except Exception as e:
        # 디버깅용으로 에러도 같이 반환 (운영환경이면 로그만 남기고 숨기는 게 좋습니다)
        raise HTTPException(500, detail=f"요약 실패: {e}")

# ────────────────────  로컬 실행용 ────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
