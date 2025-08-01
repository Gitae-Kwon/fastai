from fastapi import FastAPI, HTTPException
import os, http.client, json, uuid

app = FastAPI(title="Clova Summarizer API")

# -------- Clova 래퍼 --------
class CompletionExecutor:
    def __init__(self, host, api_key, request_id=None):
        self.host = host
        self.api_key = api_key
        self.request_id = request_id or str(uuid.uuid4())

    def execute(self, payload):
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
        }
        conn = http.client.HTTPSConnection(self.host)
        conn.request("POST", "/v1/api-tools/summarization/v2",
                     json.dumps(payload), headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        conn.close()
        return data
# ---------------------------

@app.post("/summarize")
def summarize(text: str):
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="빈 텍스트")

    executor = CompletionExecutor(
        host="clovastudio.stream.ntruss.com",
        api_key=os.getenv("CLOVA_API_KEY")
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

    if result["status"]["code"] == "20000" and "text" in result["result"]:
        return {"summary": result["result"]["text"]}
    raise HTTPException(status_code=500, detail=result)
