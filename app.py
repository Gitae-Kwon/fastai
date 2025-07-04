import streamlit as st
import requests
import json

# === Function: 브라우저 위치 API 활용 ===
def get_browser_location():
    """브라우저의 Geolocation API를 활용한 위치 감지"""
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>위치 감지</title>
    </head>
    <body>
        <div id="location-info">
            <h3>🌐 현재 위치 감지</h3>
            <button onclick="getLocation()" id="location-btn">📍 현재 위치 가져오기</button>
            <div id="result"></div>
        </div>
        
        <script>
        function getLocation() {
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('location-btn');
            
            if (navigator.geolocation) {
                btn.textContent = '🔍 위치 감지 중...';
                btn.disabled = true;
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        
                        // Streamlit으로 위치 정보 전달
                        window.parent.postMessage({
                            type: 'location_found',
                            lat: lat,
                            lon: lon
                        }, '*');
                        
                        resultDiv.innerHTML = `
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>✅ 위치 감지 성공!</h4>
                                <p><strong>위도:</strong> ${lat.toFixed(6)}</p>
                                <p><strong>경도:</strong> ${lon.toFixed(6)}</p>
                                <p style="color: #666; font-size: 0.9em;">
                                    위치 정보가 자동으로 설정됩니다.
                                </p>
                            </div>
                        `;
                        btn.textContent = '✅ 위치 감지 완료';
                        btn.disabled = false;
                    },
                    function(error) {
                        resultDiv.innerHTML = `
                            <div style="background: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>❌ 위치 감지 실패</h4>
                                <p>위치 권한을 허용해주세요.</p>
                            </div>
                        `;
                        btn.textContent = '🔄 다시 시도';
                        btn.disabled = false;
                    }
                );
            } else {
                resultDiv.innerHTML = `
                    <div style="background: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>❌ 위치 서비스 미지원</h4>
                        <p>브라우저가 위치 서비스를 지원하지 않습니다.</p>
                    </div>
                `;
            }
        }
        
        // 메시지 수신 리스너
        window.addEventListener('message', function(event) {
            if (event.data.type === 'location_found') {
                // 위치 정보가 전달되었을 때 처리
                console.log('위치 정보 수신:', event.data);
            }
        });
        </script>
    </body>
    </html>
    """
    return html_code

# === Function: 도시 검색 ===
def search_city_coordinates(city_name, api_key):
    """도시명으로 좌표 검색"""
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results = response.json()
            return results if results else []
        return []
    except Exception as e:
        st.error(f"도시 검색 중 오류: {e}")
        return []

# === Function: 날씨 데이터 가져오기 ===
def get_weather(lat, lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            res = response.json()
            return {
                'temp': res["main"]["temp"],
                'humidity': res["main"]["humidity"],
                'feels_like': res["main"]["feels_like"],
                'weather_desc': res["weather"][0]["description"]
            }
        else:
            st.error(f"날씨 API 오류: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"날씨 API 오류: {e}")
        return None

# === Function: 체감온도 계산 ===
def calculate_heat_index(temp_c, rh):
    """습도만 적용된 체감온도 (Heat Index)"""
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh
          - 0.22475541*T*rh - 6.83783e-3*T**2
          - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
          + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

def calculate_dew_point(temp_c, rh):
    """이슬점 계산"""
    return round(temp_c - ((100 - rh)/5), 1)

def calculate_comprehensive_feel(temp, humidity, dew_point):
    """습도와 이슬점이 적용된 종합 체감온도"""
    # 습도 보정
    humidity_factor = (humidity - 50) * 0.05
    # 이슬점 보정
    dew_factor = max(0, (dew_point - 15) * 0.1)
    
    return round(temp + humidity_factor + dew_factor, 1)

# === Streamlit UI ===
st.title("🌡️ 위치 기반 체감온도 분석기")

# 세션 상태 초기화
if 'location_set' not in st.session_state:
    st.session_state.location_set = False
if 'lat' not in st.session_state:
    st.session_state.lat = None
if 'lon' not in st.session_state:
    st.session_state.lon = None

# API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except:
    st.error("⚠️ secrets.toml 파일에 OWM_KEY가 설정되지 않았습니다.")
    API_KEY = None

if API_KEY:
    # 탭으로 위치 입력 방식 구분
    tab1, tab2 = st.tabs(["🌐 브라우저 위치 감지", "🏙️ 도시 검색"])
    
    with tab1:
        st.markdown("### 현재 위치 자동 감지")
        st.info("💡 가장 정확한 위치를 얻을 수 있습니다!")
        
        # 브라우저 위치 API HTML
        html_location = get_browser_location()
        st.components.v1.html(html_location, height=250)
        
        # 수동으로 위치 입력 받기 (JavaScript에서 자동 전달이 안될 경우)
        st.markdown("---")
        st.markdown("**브라우저에서 위치를 감지한 후 아래 버튼을 클릭하여 분석하세요:**")
        
        col1, col2 = st.columns(2)
        with col1:
            detected_lat = st.number_input("감지된 위도", value=0.0, format="%.6f", key="det_lat")
        with col2:
            detected_lon = st.number_input("감지된 경도", value=0.0, format="%.6f", key="det_lon")
        
        if st.button("🌐 현재 위치로 분석하기", type="primary"):
            if detected_lat != 0.0 or detected_lon != 0.0:
                st.session_state.lat = detected_lat
                st.session_state.lon = detected_lon
                st.session_state.location_set = True
                st.success("✅ 위치가 설정되었습니다!")
            else:
                st.warning("⚠️ 먼저 위 버튼을 클릭하여 위치를 감지하세요.")
    
    with tab2:
        st.markdown("### 도시명으로 검색")
        city_input = st.text_input("도시명 입력", placeholder="Seoul, Paris, Tokyo...")
        
        if city_input and st.button("🔍 도시 검색"):
            cities = search_city_coordinates(city_input, API_KEY)
            
            if cities:
                st.success(f"검색 결과 ({len(cities)}개):")
                for i, city in enumerate(cities):
                    city_name = city['name']
                    country = city.get('country', '')
                    state = city.get('state', '')
                    
                    location_str = f"{city_name}"
                    if state:
                        location_str += f", {state}"
                    if country:
                        location_str += f", {country}"
                    
                    if st.button(f"📍 {location_str}", key=f"city_{i}"):
                        st.session_state.lat = city['lat']
                        st.session_state.lon = city['lon']
                        st.session_state.location_set = True
                        st.success(f"✅ 선택됨: {location_str}")
            else:
                st.error("검색 결과가 없습니다.")
    
    # 위치가 설정되었을 때 날씨 분석
    if st.session_state.location_set and st.session_state.lat and st.session_state.lon:
        st.success(f"📍 설정된 위치: 위도 {st.session_state.lat:.6f}, 경도 {st.session_state.lon:.6f}")
        
        # 자동으로 날씨 분석 수행
        with st.spinner("날씨 정보를 분석하는 중..."):
            weather_data = get_weather(st.session_state.lat, st.session_state.lon, API_KEY)
            
            if weather_data:
                temp = weather_data['temp']
                humidity = weather_data['humidity']
                feels_like_owm = weather_data['feels_like']
                weather_desc = weather_data['weather_desc']
                
                # 체감온도 계산
                heat_index = calculate_heat_index(temp, humidity)
                dew_point = calculate_dew_point(temp, humidity)
                comprehensive_feel = calculate_comprehensive_feel(temp, humidity, dew_point)
                
                # 결과 표시
                st.markdown("---")
                st.subheader("🌡️ 체감온도 분석 결과")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**날씨**: {weather_desc.title()}")
                    st.info(f"**습도**: {humidity}%")
                    st.info(f"**이슬점**: {dew_point}°C")
                
                with col2:
                    st.metric("🌡️ 현재 기온", f"{temp}°C")
                    st.metric("💧 습도만 적용된 체감기온", f"{heat_index}°C", f"{heat_index-temp:+.1f}°C")
                    st.metric("🌡️ 습도+이슬점 적용 체감기온", f"{comprehensive_feel}°C", f"{comprehensive_feel-temp:+.1f}°C")
                
                # 간단한 쾌적도 평가
                if comprehensive_feel < 20:
                    comfort = "쾌적 😊"
                elif comprehensive_feel < 25:
                    comfort = "보통 😐"
                elif comprehensive_feel < 30:
                    comfort = "더움 😓"
                else:
                    comfort = "매우 더움 🥵"
                
                st.success(f"**쾌적도**: {comfort}")
                
                # 초기화 버튼
                if st.button("🔄 다른 위치 분석하기"):
                    st.session_state.location_set = False
                    st.session_state.lat = None
                    st.session_state.lon = None
                    st.rerun()
            else:
                st.error("❌ 날씨 정보를 가져올 수 없습니다.")
    
    elif not st.session_state.location_set:
        st.info("👆 위치를 설정하세요!")

else:
    st.warning("⚠️ OpenWeatherMap API 키가 필요합니다.")
    st.markdown("""
    ### 📝 API 키 설정:
    1. [OpenWeatherMap](https://openweathermap.org/api)에서 무료 계정 생성
    2. `.streamlit/secrets.toml`에 추가:
    ```
    OWM_KEY = "your_api_key_here"
    ```
    """)
