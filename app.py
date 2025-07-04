import streamlit as st
import requests
import json
import time

# === Function: 브라우저 위치 API 활용 ===
def get_browser_location():
    """브라우저의 Geolocation API를 활용한 위치 감지"""
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>위치 감지</title>
    </head>
    <body>
        <div id="location-info">
            <h3>🌐 현재 위치 감지</h3>
            <button onclick="getLocationAndAnalyze()" id="location-btn">📍 현재위치 날씨정보</button>
            <div id="result"></div>
        </div>
        
        <script>
        function getLocationAndAnalyze() {{
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('location-btn');
            
            if (navigator.geolocation) {{
                btn.textContent = '🔍 위치 감지 중...';
                btn.disabled = true;
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {{
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        
                        resultDiv.innerHTML = `
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>✅ 위치 감지 성공!</h4>
                                <p><strong>위도:</strong> ${{lat.toFixed(6)}}</p>
                                <p><strong>경도:</strong> ${{lon.toFixed(6)}}</p>
                                <p style="color: #4CAF50; font-weight: bold;">🌡️ 분석을 시작합니다...</p>
                            </div>
                        `;
                        
                        // 현재 페이지 URL에 좌표 파라미터 추가하고 새로고침
                        const currentUrl = new URL(window.location.href);
                        currentUrl.searchParams.set('auto_lat', lat);
                        currentUrl.searchParams.set('auto_lon', lon);
                        currentUrl.searchParams.set('auto_analyze', 'true');
                        currentUrl.searchParams.set('timestamp', Date.now()); // 캐시 방지
                        
                        // 페이지 새로고침으로 Streamlit이 파라미터를 인식하도록 함
                        window.location.href = currentUrl.toString();
                    }},
                    function(error) {{
                        let errorMessage = '';
                        switch(error.code) {{
                            case error.PERMISSION_DENIED:
                                errorMessage = '위치 접근이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해주세요.';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = '위치 정보를 사용할 수 없습니다.';
                                break;
                            case error.TIMEOUT:
                                errorMessage = '위치 요청 시간이 초과되었습니다.';
                                break;
                            default:
                                errorMessage = '알 수 없는 오류가 발생했습니다.';
                                break;
                        }}
                        
                        resultDiv.innerHTML = `
                            <div style="background: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>❌ 위치 감지 실패</h4>
                                <p>${{errorMessage}}</p>
                                <p style="font-size: 12px; color: #666;">
                                    💡 Chrome/Edge: 주소창 왼쪽 자물쇠 아이콘 클릭 → 위치 허용<br>
                                    💡 Firefox: 주소창 왼쪽 방패 아이콘 클릭 → 위치 허용
                                </p>
                            </div>
                        `;
                        btn.textContent = '🔄 다시 시도';
                        btn.disabled = false;
                    }},
                    {{
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000
                    }}
                );
            }} else {{
                resultDiv.innerHTML = `
                    <div style="background: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>❌ 위치 서비스 미지원</h4>
                        <p>브라우저가 위치 서비스를 지원하지 않습니다.</p>
                        <p>Chrome, Firefox, Safari 등의 최신 브라우저를 사용해주세요.</p>
                    </div>
                `;
            }}
        }}
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
                'weather_desc': res["weather"][0]["description"],
                'city_name': res.get("name", "Unknown"),
                'country': res.get("sys", {}).get("country", "")
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
    if temp_c < 20:  # 낮은 온도에서는 Heat Index 공식이 부정확
        return temp_c
    
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh
          - 0.22475541*T*rh - 6.83783e-3*T**2
          - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh
          + 8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

def calculate_dew_point(temp_c, rh):
    """이슬점 계산"""
    a = 17.27
    b = 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + (rh / 100.0)
    return round((b * alpha) / (a - alpha), 1)

def calculate_comprehensive_feel(temp, humidity, dew_point):
    """습도와 이슬점이 적용된 종합 체감온도"""
    # 습도 보정 (50% 기준)
    humidity_factor = (humidity - 50) * 0.03
    # 이슬점 보정 (15°C 기준)
    dew_factor = max(0, (dew_point - 15) * 0.15)
    
    return round(temp + humidity_factor + dew_factor, 1)

def get_comfort_level(feel_temp):
    """쾌적도 평가"""
    if feel_temp < 10:
        return "매우 추움 🥶", "#0066cc"
    elif feel_temp < 16:
        return "추움 😰", "#3399ff"
    elif feel_temp < 20:
        return "선선함 😊", "#66ccff"
    elif feel_temp < 25:
        return "쾌적 😃", "#00cc66"
    elif feel_temp < 28:
        return "따뜻함 😌", "#ffcc00"
    elif feel_temp < 32:
        return "더움 😓", "#ff6600"
    else:
        return "매우 더움 🥵", "#ff0000"

def analyze_weather(lat, lon, api_key):
    """날씨 분석 함수"""
    weather_data = get_weather(lat, lon, api_key)
    
    if weather_data:
        temp = weather_data['temp']
        humidity = weather_data['humidity']
        feels_like_owm = weather_data['feels_like']
        weather_desc = weather_data['weather_desc']
        city_name = weather_data['city_name']
        country = weather_data['country']
        
        # 체감온도 계산
        heat_index = calculate_heat_index(temp, humidity)
        dew_point = calculate_dew_point(temp, humidity)
        comprehensive_feel = calculate_comprehensive_feel(temp, humidity, dew_point)
        
        # 쾌적도 평가
        comfort_text, comfort_color = get_comfort_level(comprehensive_feel)
        
        # 결과 표시
        st.subheader(f"🌡️ {city_name}, {country} 날씨 분석")
        
        # 메인 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌡️ 현재 기온", f"{temp:.1f}°C")
        with col2:
            st.metric("💧 습도", f"{humidity}%")
        with col3:
            st.metric("🌤️ 날씨", weather_desc.title())
        
        # 체감온도 비교
        st.markdown("### 📊 체감온도 분석")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🌡️ OpenWeatherMap 체감온도", f"{feels_like_owm:.1f}°C", 
                     f"{feels_like_owm-temp:+.1f}°C")
            st.metric("🌡️ Heat Index (습도 적용)", f"{heat_index:.1f}°C", 
                     f"{heat_index-temp:+.1f}°C")
        
        with col2:
            st.metric("💧 이슬점", f"{dew_point:.1f}°C")
            st.metric("🌡️ 종합 체감온도", f"{comprehensive_feel:.1f}°C", 
                     f"{comprehensive_feel-temp:+.1f}°C")
        
        # 쾌적도 표시
        st.markdown(f"""
        <div style="background: {comfort_color}20; padding: 20px; border-radius: 10px; 
                    border-left: 5px solid {comfort_color}; margin: 20px 0;">
            <h3 style="color: {comfort_color}; margin: 0;">쾌적도 평가: {comfort_text}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 상세 정보
        with st.expander("📈 상세 분석 정보"):
            st.markdown(f"""
            **계산 방법:**
            - **Heat Index**: 온도와 습도를 고려한 미국 기상청 공식
            - **이슬점**: 공기가 포화되어 이슬이 맺히는 온도
            - **종합 체감온도**: 습도와 이슬점을 모두 고려한 계산
            
            **현재 조건:**
            - 기온: {temp:.1f}°C
            - 습도: {humidity}%
            - 이슬점: {dew_point:.1f}°C
            - 습도 보정: {(humidity-50)*0.03:+.1f}°C
            - 이슬점 보정: {max(0, (dew_point-15)*0.15):+.1f}°C
            """)
        
        return True
    else:
        st.error("❌ 날씨 정보를 가져올 수 없습니다. 다시 시도해주세요.")
        return False

# === Streamlit UI ===
st.set_page_config(
    page_title="🌡️ 위치 기반 체감온도 분석기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 위치 기반 체감온도 분석기")
st.markdown("현재 위치의 날씨 정보를 바탕으로 실제 체감온도를 분석합니다.")

# API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except:
    st.error("⚠️ secrets.toml 파일에 OWM_KEY가 설정되지 않았습니다.")
    API_KEY = None

if API_KEY:
    # URL 파라미터에서 자동 분석 확인
    query_params = st.query_params
    auto_analyze = False
    
    if 'auto_analyze' in query_params and query_params['auto_analyze'] == 'true':
        try:
            auto_lat = float(query_params['auto_lat'])
            auto_lon = float(query_params['auto_lon'])
            auto_analyze = True
            
            # 파라미터 정리 (무한 루프 방지)
            st.query_params.clear()
            
            # 자동 분석 실행
            st.success(f"📍 자동 분석 위치: 위도 {auto_lat:.6f}, 경도 {auto_lon:.6f}")
            
            with st.spinner("🌡️ 위치 감지된 날씨 정보를 분석하는 중..."):
                success = analyze_weather(auto_lat, auto_lon, API_KEY)
                
                if success:
                    st.success("✅ 자동 분석이 완료되었습니다!")
                    
                    # 다시 분석 버튼
                    if st.button("🔄 다른 위치 분석하기", type="secondary"):
                        st.rerun()
                else:
                    st.error("❌ 자동 분석에 실패했습니다.")
        except:
            st.error("❌ 자동 분석 파라미터가 올바르지 않습니다.")
    
    # 자동 분석이 아닌 경우에만 탭 표시
    if not auto_analyze:
        # 탭으로 위치 입력 방식 구분
        tab1, tab2 = st.tabs(["🌐 브라우저 위치 감지", "🏙️ 도시 검색"])
        
        with tab1:
            st.markdown("### 현재 위치 자동 감지")
            st.info("💡 '현재위치 날씨정보' 버튼을 클릭하면 위치 감지 후 자동으로 분석이 시작됩니다!")
            
            # 브라우저 위치 API HTML
            html_location = get_browser_location()
            st.components.v1.html(html_location, height=350)
            
            # 위치 감지 후 수동 입력 옵션
            st.markdown("---")
            st.markdown("**또는 직접 좌표를 입력하세요:**")
            
            col1, col2 = st.columns(2)
            with col1:
                manual_lat = st.number_input("위도", value=0.0, format="%.6f", key="manual_lat")
            with col2:
                manual_lon = st.number_input("경도", value=0.0, format="%.6f", key="manual_lon")
            
            if st.button("🌡️ 수동 입력으로 분석하기"):
                if manual_lat != 0.0 and manual_lon != 0.0:
                    st.success(f"📍 분석 위치: 위도 {manual_lat:.6f}, 경도 {manual_lon:.6f}")
                    
                    with st.spinner("🌡️ 날씨 정보를 분석하는 중..."):
                        success = analyze_weather(manual_lat, manual_lon, API_KEY)
                        
                        if success:
                            # 다시 분석 버튼
                            if st.button("🔄 다른 위치 분석하기", type="secondary", key="reset_manual"):
                                st.rerun()
                else:
                    st.warning("⚠️ 위도와 경도를 모두 입력해주세요.")
        
        with tab2:
            st.markdown("### 도시명으로 검색")
            city_input = st.text_input("도시명 입력", placeholder="Seoul, Paris, Tokyo, New York...")
            
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
                            st.success(f"✅ 선택됨: {location_str}")
                            
                            with st.spinner("🌡️ 날씨 정보를 분석하는 중..."):
                                success = analyze_weather(city['lat'], city['lon'], API_KEY)
                                
                                if success:
                                    # 다시 분석 버튼
                                    if st.button("🔄 다른 위치 분석하기", type="secondary", key=f"reset_city_{i}"):
                                        st.rerun()
                else:
                    st.error("❌ 검색 결과가 없습니다. 영어로 입력해보세요.")
        
        st.info("👆 위 탭에서 위치를 설정하여 날씨 분석을 시작하세요!")

else:
    st.warning("⚠️ OpenWeatherMap API 키가 필요합니다.")
    st.markdown("""
    ### 📝 API 키 설정 방법:
    1. [OpenWeatherMap](https://openweathermap.org/api)에서 무료 계정 생성
    2. API 키 발급 후 `.streamlit/secrets.toml` 파일에 추가:
    ```toml
    OWM_KEY = "your_api_key_here"
    ```
    3. 앱 재시작
    """)

# 하단 정보
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    🌡️ 위치 기반 체감온도 분석기 | 데이터 제공: OpenWeatherMap
</div>
""", unsafe_allow_html=True)
