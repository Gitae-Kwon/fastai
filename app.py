import streamlit as st
import requests

API_KEY = "YOUR_OPENWEATHER_API_KEY"
CITY = "Seoul"

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    res = requests.get(url).json()
    temp = res["main"]["temp"]
    humidity = res["main"]["humidity"]
    return temp, humidity

def calculate_heat_index(temp_c, rh):
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh
          - 0.22475541*T*rh - 6.83783e-3*T**2
          - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
          + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

def calculate_dew_point(temp_c, rh):
    return round(temp_c - ((100 - rh)/5), 1)

st.title("🌡️ 실시간 체감온도 계산기")

# Step 1: 날씨 가져오기
st.subheader("📍 현재 날씨 정보 (도시 기반)")
city = st.text_input("도시명을 입력하세요", CITY)

if st.button("날씨 가져오기"):
    try:
        temp, humidity = get_weather(city)
        st.success(f"{city} 현재 기온: {temp}°C, 습도: {humidity}%")

        # Step 2: 계산
        hi = calculate_heat_index(temp, humidity)
        dew_point = calculate_dew_point(temp, humidity)

        # Step 3: 출력
        st.markdown(f"### 🌞 체감온도: **{hi}°C**")
        st.markdown(f"### 💧 이슬점 온도: **{dew_point}°C**")

        # 상태 평가
        if hi < 27:
            st.info("→ 쾌적한 상태입니다.")
        elif hi < 33:
            st.warning("→ 더운 상태입니다.")
        elif hi < 40:
            st.error("→ 매우 더움. 수분 섭취 필요!")
        else:
            st.error("🥵 폭염 수준! 외출 자제 권장")

    except Exception as e:
        st.error("날씨 정보를 불러오지 못했습니다. 도시명을 다시 확인해주세요.")
