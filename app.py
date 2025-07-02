import streamlit as st
import requests

# === Function: IP 기반 위치 감지 ===
def get_location_by_ip():
    try:
        res = requests.get("https://ipinfo.io").json()
        lat, lon = res["loc"].split(",")
        city = res.get("city", "Unknown")
        return float(lat), float(lon), city
    except:
        return None, None, "Unknown"

# === Function: OpenWeather API로 날씨 데이터 가져오기 ===
def get_weather(lat, lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        res = requests.get(url).json()
        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]
        return temp, humidity
    except:
        return None, None

# === Function: 체감온도 계산 (Heat Index 공식) ===
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

# === Streamlit UI ===
st.title("🌡️ 자동 위치 기반 체감온도 계산기")

# API Key 입력
API_KEY = "c239f9f652ba585441a6f0e5db6f2226"

if API_KEY:
    lat, lon, city = get_location_by_ip()
    
    if lat and lon:
        st.info(f"📍 현재 추정 위치: **{city}** (위도 {lat}, 경도 {lon})")

        temp, humidity = get_weather(lat, lon, API_KEY)

        if temp is not None and humidity is not None:
            st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")

            hi = calculate_heat_index(temp, humidity)
            dew = calculate_dew_point(temp, humidity)

            st.markdown(f"### 🔥 체감온도 (Heat Index): **{hi}°C**")
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
        else:
            st.error("날씨 정보를 가져올 수 없습니다. API 키 또는 네트워크를 확인하세요.")
    else:
        st.error("위치 정보를 가져올 수 없습니다.")
else:
    st.warning("먼저 OpenWeatherMap API 키를 입력하세요.")
