import streamlit as st
from streamlit_javascript import st_javascript
import requests

# === 이슬점 계산 ===
def calculate_dew_point(temp_c, rh):
    return round(temp_c - ((100 - rh) / 5), 1)

# === 체감온도 계산 ===
def calculate_heat_index(temp_c, rh):
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh
          - 0.22475541*T*rh - 6.83783e-3*T**2
          - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
          + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

# === 날씨 데이터 요청 ===
def get_weather(lat, lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        res = requests.get(url).json()
        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]
        return temp, humidity
    except:
        return None, None

# === Streamlit UI 시작 ===
st.set_page_config(page_title="위치 기반 체감온도", page_icon="🌡️")
st.title("🌡️ 현재 위치 체감온도")

# 📍 위치 정보: JS로 가져오기
coords = st_javascript("""
    () => new Promise((resolve, reject) => {
        try {
            if (!navigator.geolocation) {
                resolve("unsupported");
            } else {
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
            }
        } catch (e) {
            resolve("error");
        }
    });
""")

# 디버깅용 출력
st.code(f"coords: {coords} (type: {type(coords)})")

# 🌍 위치 결과 처리
if coords is None:
    st.info("⏳ 위치 정보를 가져오는 중입니다...")
elif coords in ["denied", "unsupported", "error"]:
    st.warning("🚫 위치 정보 접근이 거부되었거나 사용할 수 없습니다.")
elif isinstance(coords, str) and "," in coords:
    try:
        lat, lon = map(float, coords.split(","))
        st.success(f"📍 현재 위치: 위도 {lat}, 경도 {lon}")

        # 🔐 OpenWeather API 키 (secrets.toml에서 관리)
        api_key = st.secrets["OWM_KEY"]

        temp, humidity = get_weather(lat, lon, api_key)

        if temp is not None:
            st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")
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
        else:
            st.error("❌ 날씨 정보를 가져올 수 없습니다.")

    except Exception as e:
        st.error(f"❌ 위치 데이터 파싱 오류: {e}")
else:
    st.error(f"⚠️ 잘못된 위치 데이터 형식: {coords} (type: {type(coords)})")
