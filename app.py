import streamlit as st
import requests
from streamlit_javascript import st_javascript

st.set_page_config(page_title="체감온도 계산기", layout="centered")
st.title("🌡️ 현재 위치 체감온도")

API_KEY = st.secrets["OWM_KEY"]

# 📍 JS로 GPS 위치 요청
coords = st_javascript(
    """
    () => new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(6);
                const lon = pos.coords.longitude.toFixed(6);
                resolve(lat + "," + lon);
            },
            (err) => {
                resolve("denied");
            }
        );
    })
    """
)

# 📌 위치값 검증
if coords is None:
    st.info("⏳ 위치 정보를 가져오는 중입니다... (브라우저 위치 권한 허용 필요)")
elif coords == "denied":
    st.warning("🚫 위치 정보 접근이 거부되었습니다. 브라우저 권한 설정을 확인해주세요.")
elif isinstance(coords, str) and "," in coords:
    try:
        lat_str, lon_str = coords.split(",")
        lat, lon = float(lat_str), float(lon_str)
        st.info(f"📍 현재 위치: 위도 {lat}, 경도 {lon}")

        # 🌤️ 날씨 정보 가져오기
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]
        st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")

        # 계산 함수
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

        st.markdown(f"### 🔥 체감온도: **{hi}°C**")
        st.markdown(f"### 💧 이슬점 온도: **{dew}°C**")

        # 상태 평가
        if hi < 27:
            st.info("→ 쾌적한 상태입니다.")
        elif hi < 33:
            st.warning("→ 다소 더운 상태입니다.")
        elif hi < 40:
            st.error("→ 매우 더움. 수분 섭취가 필요합니다!")
        else:
            st.error("🥵 폭염 수준! 외출을 자제하세요.")
    except Exception as e:
        st.error(f"❗위치 데이터 처리 오류: {e}")
else:
    st.error(f"⚠️ 잘못된 위치 데이터 형식: {coords}")
