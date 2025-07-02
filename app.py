import streamlit as st
import requests
from streamlit_javascript import st_javascript

# OpenWeatherMap API
API_KEY = "629f65f9a3aa0600b09e6171855f3afe"

# Step 1: 사용자 위치 정보 가져오기 (위도, 경도)
coords = st_javascript("navigator.geolocation.getCurrentPosition((loc) => {window.location = '?lat=' + loc.coords.latitude + '&lon=' + loc.coords.longitude})", key="get_location")

lat = st.experimental_get_query_params().get("lat", [None])[0]
lon = st.experimental_get_query_params().get("lon", [None])[0]

if lat and lon:
    st.success(f"현재 위치: 위도 {lat}, 경도 {lon}")

    # Step 2: 날씨 데이터 가져오기
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    res = requests.get(url).json()
    temp = res["main"]["temp"]
    humidity = res["main"]["humidity"]

    # Step 3: 체감온도 계산
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
    dew_point = calculate_dew_point(temp, humidity)

    st.markdown(f"🌡️ 현재 온도: **{temp}°C**")
    st.markdown(f"💧 습도: **{humidity}%**")
    st.markdown(f"🔥 체감온도(Heat Index): **{hi}°C**")
    st.markdown(f"💦 이슬점(Dew Point): **{dew_point}°C**")
else:
    st.info("브라우저에서 위치 정보 제공을 허용해주세요.")
