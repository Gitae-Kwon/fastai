import streamlit as st
import requests
from streamlit_javascript import st_javascript

# === Function: OpenWeather API로 날씨 데이터 가져오기 ===
def get_weather(lat, lon, api_key):
    """OpenWeatherMap 현재 날씨 데이터 호출"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        return temp, humidity
    else:
        st.error(f"날씨 API 오류: {response.status_code} - {response.text}")
        return None, None

# === Function: 체감온도 계산 (Heat Index 공식) ===
def calculate_heat_index(temp_c, rh):
    """온도와 습도로 Heat Index 계산"""
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523 * T + 10.14333127 * rh
          - 0.22475541 * T * rh - 6.83783e-3 * T**2
          - 5.481717e-2 * rh**2 + 1.22874e-3 * T**2 * rh
          + 8.5282e-4 * T * rh**2 - 1.99e-6 * T**2 * rh**2)
    return round((HI - 32) * 5/9, 1)

# === Function: 이슬점 계산 ===
def calculate_dew_point(temp_c, rh):
    """온도와 습도로 이슬점 계산"""
    return round(temp_c - ((100 - rh) / 5), 1)

# === Streamlit UI 설정 ===
st.set_page_config(page_title="위치 기반 체감기온 분석기", layout="centered")
st.title("🌡️ 위치 기반 체감기온 분석기")

# API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except KeyError:
    st.error("⚠️ secrets.toml에 OWM_KEY가 설정되지 않았습니다.")
    st.stop()

st.markdown("---")
st.info("💡 브라우저 위치 권한을 허용하고, '현재 위치 가져오기' 버튼을 눌러 분석하세요.")

if st.button("📍 현재 위치 가져오기"):
    # 브라우저에서 JS 호출로 위치 얻기
    coord = st_javascript(
        "() => new Promise((resolve, reject) => {\
           navigator.geolocation.getCurrentPosition(\
             pos => resolve(`${pos.coords.latitude},${pos.coords.longitude}`),\
             err => reject(err)\
           );\
         })"
    )
    if coord:
        try:
            lat, lon = map(float, coord.split(","))
        except:
            st.error("위치 좌표 파싱 실패")
            st.stop()

        # 날씨 데이터 조회
        temp, humidity = get_weather(lat, lon, API_KEY)
        if temp is None:
            st.stop()

        # 지표 계산
        hi_humidity = calculate_heat_index(temp, humidity)
        dew_point = calculate_dew_point(temp, humidity)

        # 결과 표시
        st.markdown("---")
        st.subheader(f"📍 위치: 위도 {lat:.6f}, 경도 {lon:.6f}")
        st.write("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="현재 기온 (°C)", value=f"{temp:.1f}")
        with col2:
            st.metric(label="체감기온 (습도만) (°C)", value=f"{hi_humidity:.1f}")
        with col3:
            st.metric(label="체감기온 (습도+이슬점) (°C)", value=f"{dew_point:.1f}")
    else:
        st.warning("위치 정보 가져오기 실패: 브라우저 권한을 확인하세요.")
else:
    st.write("👆 '현재 위치 가져오기' 버튼을 클릭하세요.")

st.markdown("---")
st.markdown("💡 **팁**: 모바일 환경에서는 위치 권한 설정이 필요합니다.")
