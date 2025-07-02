import streamlit as st
from streamlit_javascript import st_javascript
import requests

st.set_page_config(page_title="체감온도 계산기", page_icon="🌡️", layout="centered")

# OpenWeather API 키 (secrets에서 불러오기)
API_KEY = st.secrets["OWM_KEY"]

# 위치 추출 (JS)
coords = str(st_javascript("""
    () => new Promise((resolve) => {
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
    })
"""))

st.title("🌡️ 현재 위치 체감온도")
st.code(f"coords: {coords} (type: {type(coords)})")

# === Function: 체감온도 계산 ===
def calculate_heat_index(temp_c, rh):
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh
          - 0.22475541*T*rh - 6.83783e-3*T**2
          - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
          + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

# === Function: 이슬점 계산 ===
def calculate_dew_point(temp_c, rh):
    return round(temp_c - ((100 - rh)/5), 1)

# === Function: 날씨 호출 ===
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        return res["main"]["temp"], res["main"]["humidity"]
    except:
        return None, None

# 파싱 및 출력
if coords in ["None", "0", "denied", "unsupported", "error"]:
    st.warning("📍 위치 정보를 가져올 수 없습니다. 브라우저 권한을 확인해주세요.")
elif "," in coords:
    try:
        lat, lon = map(float, coords.split(","))
        st.success(f"📍 현재 위치: 위도 {lat}, 경도 {lon}")

        temp, humidity = get_weather(lat, lon)
        if temp is not None and humidity is not None:
            st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")

            hi = calculate_heat_index(temp, humidity)
            dew = calculate_dew_point(temp, humidity)

            st.markdown(f"### 🔥 체감온도: **{hi}°C**")
            st.markdown(f"### 💧 이슬점 온도: **{dew}°C**")
        else:
            st.error("❌ 날씨 데이터를 가져오지 못했습니다.")
    except Exception as e:
        st.error(f"❌ 위치 데이터 파싱 오류: {e}")
else:
    st.error(f"⚠️ 잘못된 위치 데이터 형식: {coords} (type: {type(coords)})")
