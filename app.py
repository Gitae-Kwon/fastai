import streamlit as st
import math

def calculate_heat_index(temp_celsius, humidity):
    # 섭씨를 화씨로 변환
    T = temp_celsius * 9/5 + 32
    RH = humidity

    # NOAA 공식 (화씨 기준)
    HI = (-42.379 + 2.04901523*T + 10.14333127*RH
          - 0.22475541*T*RH - 6.83783e-3*T**2
          - 5.481717e-2*RH**2 + 1.22874e-3*T**2*RH
          + 8.5282e-4*T*RH**2 - 1.99e-6*T**2*RH**2)

    # 화씨를 섭씨로 변환
    HI_C = (HI - 32) * 5/9
    return round(HI_C, 1)

st.title("🌡️ 여름 체감온도 계산기")
temp = st.slider("기온 (°C)", 20, 45, 30)
humidity = st.slider("상대 습도 (%)", 10, 100, 70)

if st.button("체감온도 계산하기"):
    hi = calculate_heat_index(temp, humidity)
    st.success(f"체감온도는 약 {hi}°C 입니다.")

    # 부가 정보
    if hi < 27:
        st.info("→ 쾌적한 수준입니다.")
    elif hi < 32:
        st.warning("→ 다소 더운 상태입니다.")
    elif hi < 40:
        st.error("→ 매우 더운 상태, 수분 섭취 필요!")
    else:
        st.error("🥵 폭염 수준! 외출 자제 권장")
