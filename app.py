import streamlit as st
import requests
import json

# === 날씨 데이터 및 계산 함수들 ===
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
        return None
    except Exception as e:
        st.error(f"날씨 API 오류: {e}")
        return None

def calculate_heat_index(temp_c, rh):
    if temp_c < 20:
        return temp_c
    T = temp_c * 9/5 + 32
    HI = (-42.379 + 2.04901523*T + 10.14333127*rh - 0.22475541*T*rh - 
          6.83783e-3*T**2 - 5.481717e-2*rh**2 + 1.22874e-3*T**2*rh + 
          8.5282e-4*T*rh**2 - 1.99e-6*T**2*rh**2)
    return round((HI - 32) * 5/9, 1)

def calculate_dew_point(temp_c, rh):
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + (rh / 100.0)
    return round((b * alpha) / (a - alpha), 1)

def calculate_comprehensive_feel(temp, humidity, dew_point):
    humidity_factor = (humidity - 50) * 0.03
    dew_factor = max(0, (dew_point - 15) * 0.15)
    return round(temp + humidity_factor + dew_factor, 1)

def get_comfort_level(feel_temp):
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

def search_city_coordinates(city_name, api_key):
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

# === 위치 감지 HTML (모바일 최적화) ===
def get_mobile_location_html():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; }}
            .container {{ max-width: 100%; }}
            .btn {{ 
                background: #ff4b4b; color: white; border: none; padding: 12px 20px; 
                border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; 
                margin: 10px 0; box-sizing: border-box;
            }}
            .btn:hover {{ background: #ff6b6b; }}
            .btn:disabled {{ background: #ccc; cursor: not-allowed; }}
            .result {{ margin: 15px 0; padding: 15px; border-radius: 8px; }}
            .success {{ background: #e8f5e8; border: 1px solid #4CAF50; }}
            .error {{ background: #ffe8e8; border: 1px solid #f44336; }}
            .coord-box {{ 
                background: #f0f0f0; padding: 10px; border-radius: 5px; 
                margin: 5px 0; font-family: monospace; font-size: 14px;
            }}
            .copy-btn {{ 
                background: #4CAF50; color: white; border: none; padding: 5px 10px; 
                border-radius: 3px; font-size: 12px; margin-left: 10px; cursor: pointer;
            }}
            .copy-btn:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3>📍 현재 위치 감지</h3>
            <button onclick="getLocation()" id="locationBtn" class="btn">
                📍 현재 위치 감지하기
            </button>
            <div id="result"></div>
        </div>
        
        <script>
        function getLocation() {{
            const btn = document.getElementById('locationBtn');
            const result = document.getElementById('result');
            
            if (!navigator.geolocation) {{
                result.innerHTML = `
                    <div class="result error">
                        <h4>❌ 위치 서비스 미지원</h4>
                        <p>브라우저가 위치 서비스를 지원하지 않습니다.</p>
                    </div>
                `;
                return;
            }}
            
            btn.textContent = '🔍 위치 감지 중...';
            btn.disabled = true;
            
            navigator.geolocation.getCurrentPosition(
                function(position) {{
                    const lat = position.coords.latitude.toFixed(6);
                    const lon = position.coords.longitude.toFixed(6);
                    
                    result.innerHTML = `
                        <div class="result success">
                            <h4>✅ 위치 감지 성공!</h4>
                            <div class="coord-box">
                                <strong>위도:</strong> ${{lat}}
                                <button class="copy-btn" onclick="copyToClipboard('${{lat}}')">복사</button>
                            </div>
                            <div class="coord-box">
                                <strong>경도:</strong> ${{lon}}
                                <button class="copy-btn" onclick="copyToClipboard('${{lon}}')">복사</button>
                            </div>
                            <p style="color: #4CAF50; margin-top: 10px;">
                                📋 위도/경도를 복사하여 아래 입력칸에 붙여넣으세요!
                            </p>
                        </div>
                    `;
                    
                    btn.textContent = '🔄 다시 감지하기';
                    btn.disabled = false;
                    
                    // 자동으로 Streamlit 입력창에 값 설정 (가능한 경우)
                    try {{
                        window.parent.postMessage({{
                            type: 'coordinates',
                            lat: parseFloat(lat),
                            lon: parseFloat(lon)
                        }}, '*');
                    }} catch(e) {{
                        console.log('Parent communication failed:', e);
                    }}
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
                    }}
                    
                    result.innerHTML = `
                        <div class="result error">
                            <h4>❌ 위치 감지 실패</h4>
                            <p>${{errorMessage}}</p>
                            <p style="font-size: 12px; color: #666;">
                                💡 Chrome/Safari: 주소창 자물쇠 아이콘 → 위치 허용<br>
                                💡 Firefox: 주소창 방패 아이콘 → 위치 허용
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
        }}
        
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(function() {{
                // 복사 성공 피드백
                event.target.textContent = '✅복사됨';
                setTimeout(() => {{
                    event.target.textContent = '복사';
                }}, 1000);
            }}).catch(function() {{
                // 복사 실패시 선택하기
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                event.target.textContent = '✅복사됨';
                setTimeout(() => {{
                    event.target.textContent = '복사';
                }}, 1000);
            }});
        }}
        </script>
    </body>
    </html>
    """

# === 날씨 분석 함수 ===
def analyze_weather(lat, lon, api_key):
    weather_data = get_weather(lat, lon, api_key)
    
    if not weather_data:
        return False
    
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
    st.markdown(f"### 🌡️ {city_name}, {country}")
    
    # 메인 정보 (모바일 최적화)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🌡️ 현재 기온", f"{temp:.1f}°C")
        st.metric("💧 습도", f"{humidity}%")
    with col2:
        st.metric("🌤️ 날씨", weather_desc.title())
        st.metric("🌡️ 체감온도", f"{comprehensive_feel:.1f}°C", f"{comprehensive_feel-temp:+.1f}°C")
    
    # 쾌적도 표시
    st.markdown(f"""
    <div style="background: {comfort_color}20; padding: 15px; border-radius: 10px; 
                border-left: 4px solid {comfort_color}; margin: 15px 0; text-align: center;">
        <h3 style="color: {comfort_color}; margin: 0; font-size: 18px;">
            쾌적도: {comfort_text}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 상세 정보
    with st.expander("📊 상세 체감온도 분석"):
        st.markdown(f"""
        **체감온도 비교:**
        - OpenWeatherMap: {feels_like_owm:.1f}°C ({feels_like_owm-temp:+.1f}°C)
        - Heat Index: {heat_index:.1f}°C ({heat_index-temp:+.1f}°C)
        - 종합 체감온도: {comprehensive_feel:.1f}°C ({comprehensive_feel-temp:+.1f}°C)
        
        **기타 정보:**
        - 이슬점: {dew_point:.1f}°C
        - 습도 보정: {(humidity-50)*0.03:+.1f}°C
        - 이슬점 보정: {max(0, (dew_point-15)*0.15):+.1f}°C
        """)
    
    return True

# === Streamlit UI ===
st.set_page_config(
    page_title="🌡️ 체감온도 분석기",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🌡️ 체감온도 분석기")
st.markdown("📱 모바일 친화적 날씨 분석 도구")

# API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except:
    st.error("⚠️ secrets.toml 파일에 OWM_KEY가 설정되지 않았습니다.")
    API_KEY = None

if API_KEY:
    # 탭 구성
    tab1, tab2 = st.tabs(["📍 위치 감지", "🏙️ 도시 검색"])
    
    with tab1:
        st.markdown("### 현재 위치 자동 감지")
        
        # 위치 감지 HTML
        st.components.v1.html(get_mobile_location_html(), height=400)
        
        # 수동 입력
        st.markdown("### 또는 직접 입력")
        col1, col2 = st.columns(2)
        
        with col1:
            lat = st.number_input("위도", value=0.0, format="%.6f", help="위에서 감지된 위도를 붙여넣으세요")
        with col2:
            lon = st.number_input("경도", value=0.0, format="%.6f", help="위에서 감지된 경도를 붙여넣으세요")
        
        if st.button("🌡️ 날씨 분석하기", type="primary", use_container_width=True):
            if lat != 0.0 and lon != 0.0:
                with st.spinner("🔍 날씨 정보를 분석하는 중..."):
                    success = analyze_weather(lat, lon, API_KEY)
                    if success:
                        st.success("✅ 분석 완료!")
                    else:
                        st.error("❌ 분석에 실패했습니다.")
            else:
                st.warning("⚠️ 위도와 경도를 입력해주세요.")
    
    with tab2:
        st.markdown("### 도시명으로 검색")
        city_input = st.text_input("도시명", placeholder="Seoul, Tokyo, Paris...")
        
        if city_input:
            if st.button("🔍 검색", type="primary", use_container_width=True):
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
                        
                        if st.button(f"📍 {location_str}", key=f"city_{i}", use_container_width=True):
                            with st.spinner("🔍 날씨 정보를 분석하는 중..."):
                                success = analyze_weather(city['lat'], city['lon'], API_KEY)
                                if success:
                                    st.success("✅ 분석 완료!")
                                else:
                                    st.error("❌ 분석에 실패했습니다.")
                else:
                    st.error("❌ 검색 결과가 없습니다.")

else:
    st.warning("⚠️ OpenWeatherMap API 키가 필요합니다.")
    st.code('''
# .streamlit/secrets.toml
OWM_KEY = "your_api_key_here"
    ''')

# 하단 정보
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px; padding: 10px;">
    📱 모바일 최적화 체감온도 분석기 | 📡 OpenWeatherMap API
</div>
""", unsafe_allow_html=True)
