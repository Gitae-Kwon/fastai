from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline, Pipeline
import uvicorn

app = FastAPI()

# ───────── CORS ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 배포 시엔 ["https://내-도메인"] 로 제한하세요
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────── summarizer(한 번만 로드) ─────────
summarizer: Pipeline | None = None
def get_summarizer() -> Pipeline:
    global summarizer
    if summarizer is None:
        summarizer = pipeline(
            "summarization",
            model="ainize/kobart-news-summarization",
            device=-1           # CPU
        )
    return summarizer

# ───────── request / response 스키마 ─────────
class SummaryRequest(BaseModel):
    text: str

class SummaryResponse(BaseModel):
    summary: str

# ───────── API ─────────
@app.post("/summarize", response_model=SummaryResponse)
def summarize(req: SummaryRequest):
    """
    JSON 바디로  { "text": "...원문..." }  를 받으면
    요약 결과를  { "summary": "...요약..." }  로 돌려줍니다.
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(422, detail="텍스트를 보내 주세요.")
    try:
        result = get_summarizer()(text, max_length=120, min_length=30, do_sample=False)
        return {"summary": result[0]["summary_text"]}
    except Exception as e:
        raise HTTPException(500, detail=f"요약 실패: {e}")

# ───────── 로컬 실행 ─────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
