import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="체감온도 계산기", layout="centered")
st.title("🌡️ 자동 위치 기반 체감온도 계산기 (JS 기반)")

# 1️⃣ JavaScript로 브라우저 위치 감지
components.html(
    """
    <script>
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                const location = latitude + "," + longitude;
                document.cookie = "user_coords=" + location;
                window.location.reload();  // 다시 로드해서 Streamlit이 쿠키 읽게 함
            },
            (err) => {
                document.cookie = "user_coords=denied";
                window.location.reload();
            }
        );
    </script>
    """,
    height=0,
)

# 2️⃣ 쿠키에서 위치값 읽기
import http.cookies
import os

raw_cookie = os.environ.get("HTTP_COOKIE", "")
cookie = http.cookies.SimpleCookie()
cookie.load(raw_cookie)

coords = cookie.get("user_coords")
if coords:
    val = coords.value
    if val == "denied":
        st.warning("❗ 위치 정보 접근이 거부되었습니다. 브라우저 설정을 확인하세요.")
    else:
        try:
            lat, lon = map(float, val.split(","))
            st.success(f"📍 현재 위치: 위도 {lat}, 경도 {lon}")

            # 3️⃣ 날씨 API 호출
            API_KEY = st.secrets["OWM_KEY"]
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            res = requests.get(url).json()
            temp = res["main"]["temp"]
            humidity = res["main"]["humidity"]

            st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")

            # 체감온도 계산
            def calculate_heat_index(temp_c, rh):
                T = temp_c * 9/5 + 32
                HI = (-42.379 + 2.04901523*T + 10.14333127*rh
                      - 0.22475541*T*rh - 6.83783e-3*T**2
                      - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
                      + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
                return round((HI - 32) * 5/9, 1)

            def calculate_dew_point(temp_c, rh):
                return round(temp_c - ((100 - rh)/5), 1)

            hi = calculate_heat_index(temp, humidity)
            dew = calculate_dew_point(temp, humidity)

            st.markdown(f"### 🔥 체감온도 (Heat Index): **{hi}°C**")
            st.markdown(f"### 💧 이슬점 온도: **{dew}°C**")

            if hi < 27:
                st.info("→ 쾌적한 상태입니다.")
            elif hi < 33:
                st.warning("→ 다소 더운 상태입니다.")
            elif hi < 40:
                st.error("→ 매우 더움. 수분 섭취가 필요합니다!")
            else:
                st.error("🥵 폭염 수준! 외출을 자제하세요.")
        except:
            st.error("위치 값을 처리할 수 없습니다.")
else:
    st.info("⏳ 위치 정보를 가져오는 중입니다... (브라우저 허용 필요)")
