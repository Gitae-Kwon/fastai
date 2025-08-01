# -*- coding: utf-8 -*-
import http.client
import json
import streamlit as st
import uuid


class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key  # 순수 키만 (Bearer 없음)
        self._request_id = request_id

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {self._api_key}',
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('POST', '/v1/api-tools/summarization/v2', json.dumps(completion_request), headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode(encoding='utf-8'))
        conn.close()
        return result

    def execute(self, completion_request):
        return self._send_request(completion_request)


# ✅ Streamlit 앱
st.set_page_config(page_title="Ai 요약기", layout="centered")
st.title("✂️ Ai 요약기 (Studio API v2)")

input_text = st.text_area("요약할 내용을 입력하세요", height=200)

if st.button("요약하기"):
    if not input_text.strip():
        st.warning("요약할 내용을 입력해주세요.")
    else:
        with st.spinner("요약 중입니다..."):
            try:
                executor = CompletionExecutor(
                    host="clovastudio.stream.ntruss.com",
                    api_key=st.secrets["clova"]["api_key"],  # secrets.toml 또는 cloud secrets에 저장된 키
                    request_id=str(uuid.uuid4())
                )

                request_data = {
                    "texts": [input_text],
                    "segMinSize": 300,
                    "includeAiFilters": False,
                    "autoSentenceSplitter": True,
                    "segCount": -1,
                    "segMaxSize": 1000
                }

                response = executor.execute(request_data)

                if response["status"]["code"] == "20000" and "text" in response["result"]:
                    st.success("✅ 요약 결과:")
                    st.write(response["result"]["text"])
                else:
                    st.error("❌ 요약 실패:")
                    st.json(response)
            except Exception as e:
                st.error(f"오류 발생: {e}")
