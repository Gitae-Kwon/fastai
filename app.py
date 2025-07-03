import streamlit as st
import requests
import time
import json

# === Function: 브라우저 위치 API 활용 (HTML/JavaScript) ===
def get_browser_location():
    """브라우저의 Geolocation API를 활용한 위치 감지"""
    
    # HTML과 JavaScript로 브라우저 위치 API 호출
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>위치 감지</title>
    </head>
    <body>
        <div id="location-info">
            <h3>🌐 브라우저 위치 감지</h3>
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
                        const accuracy = position.coords.accuracy;
                        
                        resultDiv.innerHTML = `
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>✅ 위치 감지 성공!</h4>
                                <p><strong>위도:</strong> ${lat.toFixed(6)}</p>
                                <p><strong>경도:</strong> ${lon.toFixed(6)}</p>
                                <p><strong>정확도:</strong> ${accuracy.toFixed(0)}m</p>
                                <p style="color: #666; font-size: 0.9em;">
                                    위 좌표를 복사하여 '수동 좌표 입력'에 사용하세요!
                                </p>
                            </div>
                        `;
                        btn.textContent = '🔄 다시 감지';
                        btn.disabled = false;
                    },
                    function(error) {
                        let errorMsg = '';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMsg = "사용자가 위치 정보 접근을 거부했습니다.";
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMsg = "위치 정보를 사용할 수 없습니다.";
                                break;
                            case error.TIMEOUT:
                                errorMsg = "위치 요청 시간이 초과되었습니다.";
                                break;
                            default:
                                errorMsg = "알 수 없는 오류가 발생했습니다.";
                                break;
                        }
                        resultDiv.innerHTML = `
                            <div style="background: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                <h4>❌ 위치 감지 실패</h4>
                                <p>${errorMsg}</p>
                                <p style="color: #666; font-size: 0.9em;">
                                    '수동 좌표 입력' 옵션을 사용하세요.
                                </p>
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
        </script>
    </body>
    </html>
    """
    
    return html_code

# === Function: 사용자 친화적인 도시 검색 ===
def search_city_coordinates(city_name, api_key):
    """도시명으로 좌표 검색"""
    try:
        # OpenWeatherMap Geocoding API
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={api_key}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results = response.json()
            if results:
                return results  # 여러 결과 반환
        return []
    except Exception as e:
        st.error(f"도시 검색 중 오류: {e}")
        return []

# === Function: IP 기반 위치 감지 (개선된 버전) ===
def get_location_by_ip():
    """여러 IP 위치 서비스를 순차적으로 시도"""
    
    # 여러 IP 위치 서비스 목록
    services = [
        {
            'name': 'ipinfo.io',
            'url': 'https://ipinfo.io/json',
            'parser': lambda res: (
                res["loc"].split(",")[0], 
                res["loc"].split(",")[1], 
                res.get("city", "Unknown"),
                res.get("region", ""),
                res.get("country", "")
            )
        },
        {
            'name': 'ip-api.com',
            'url': 'http://ip-api.com/json',
            'parser': lambda res: (
                str(res["lat"]), 
                str(res["lon"]), 
                res.get("city", "Unknown"),
                res.get("regionName", ""),
                res.get("country", "")
            )
        },
        {
            'name': 'ipapi.co',
            'url': 'https://ipapi.co/json',
            'parser': lambda res: (
                str(res["latitude"]), 
                str(res["longitude"]), 
                res.get("city", "Unknown"),
                res.get("region", ""),
                res.get("country", "")
            )
        }
    ]
    
    for i, service in enumerate(services):
        try:
            st.write(f"🔍 {service['name']} 서비스 시도 중...")
            
            # 타임아웃과 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(
                service['url'], 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                res = response.json()
                
                lat, lon, city, region, country = service['parser'](res)
                
                # 좌표 유효성 검사
                lat_float = float(lat)
                lon_float = float(lon)
                
                if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                    full_location = f"{city}, {region}, {country}".strip(", ")
                    st.success(f"✅ 위치 정보 획득 성공 ({service['name']})")
                    st.info(f"📍 감지된 위치: {full_location}")
                    return lat_float, lon_float, full_location
                else:
                    st.warning(f"⚠️ {service['name']}: 잘못된 좌표값")
                    
        except requests.exceptions.Timeout:
            st.warning(f"⏰ {service['name']}: 응답 시간 초과")
        except requests.exceptions.ConnectionError:
            st.warning(f"🔌 {service['name']}: 연결 오류")
        except KeyError as e:
            st.warning(f"🔑 {service['name']}: 필수 키 누락 - {e}")
        except ValueError as e:
            st.warning(f"🔢 {service['name']}: 좌표 변환 오류 - {e}")
        except Exception as e:
            st.warning(f"❌ {service['name']}: 기타 오류 - {e}")
        
        # 서비스 간 지연시간
        if i < len(services) - 1:
            time.sleep(1)
    
    st.error("모든 IP 위치 서비스에서 실패했습니다.")
    return None, None, "Unknown"

# === Function: 수동 위치 입력 옵션 (개선된 버전) ===
def manual_location_input(api_key):
    """사용자가 직접 위치를 입력할 수 있는 옵션"""
    st.subheader("🗺️ 위치 입력 옵션")
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["🏙️ 도시명 검색", "📍 직접 좌표 입력", "🌐 브라우저 위치"])
    
    with tab1:
        st.markdown("### 도시명으로 검색")
        city_input = st.text_input("도시명을 입력하세요 (예: Seoul, Paris, Tokyo)", 
                                 placeholder="도시명을 영어 또는 한글로 입력")
        
        if city_input and st.button("🔍 도시 검색"):
            with st.spinner("도시를 검색하는 중..."):
                cities = search_city_coordinates(city_input, api_key)
                
                if cities:
                    st.success(f"검색 결과 ({len(cities)}개):")
                    
                    for i, city in enumerate(cities):
                        city_name = city['name']
                        country = city.get('country', '')
                        state = city.get('state', '')
                        lat = city['lat']
                        lon = city['lon']
                        
                        location_str = f"{city_name}"
                        if state:
                            location_str += f", {state}"
                        if country:
                            location_str += f", {country}"
                        
                        if st.button(f"📍 {location_str} 선택", key=f"city_{i}"):
                            st.session_state.selected_lat = lat
                            st.session_state.selected_lon = lon
                            st.session_state.selected_city = location_str
                            st.success(f"✅ 선택됨: {location_str}")
                            st.rerun()
                else:
                    st.error("검색 결과가 없습니다. 다른 도시명을 시도해보세요.")
    
    with tab2:
        st.markdown("### 직접 좌표 입력")
        
        # 주요 도시 프리셋
        preset_cities = {
            "직접 입력": None,
            "서울, 대한민국": (37.5665, 126.9780),
            "부산, 대한민국": (35.1796, 129.0756),
            "파리, 프랑스": (48.8566, 2.3522),
            "도쿄, 일본": (35.6762, 139.6503),
            "뉴욕, 미국": (40.7128, -74.0060),
            "런던, 영국": (51.5074, -0.1278),
        }
        
        selected_preset = st.selectbox("주요 도시 선택 또는 직접 입력:", list(preset_cities.keys()))
        
        if preset_cities[selected_preset] is not None:
            lat, lon = preset_cities[selected_preset]
            city_name = selected_preset
            st.session_state.selected_lat = lat
            st.session_state.selected_lon = lon
            st.session_state.selected_city = city_name
            st.success(f"✅ 선택된 도시: {city_name}")
        else:
            col1, col2 = st.columns(2)
            with col1:
                manual_lat = st.number_input("위도 (Latitude)", 
                                           value=37.5665, 
                                           min_value=-90.0, 
                                           max_value=90.0, 
                                           step=0.0001,
                                           format="%.6f")
            with col2:
                manual_lon = st.number_input("경도 (Longitude)", 
                                           value=126.9780, 
                                           min_value=-180.0, 
                                           max_value=180.0, 
                                           step=0.0001,
                                           format="%.6f")
            
            manual_city = st.text_input("위치명 (선택사항)", value="사용자 지정 위치")
            
            if st.button("📍 좌표 설정"):
                st.session_state.selected_lat = manual_lat
                st.session_state.selected_lon = manual_lon
                st.session_state.selected_city = manual_city
                st.success(f"✅ 좌표 설정됨: {manual_city}")
    
    with tab3:
        st.markdown("### 브라우저 위치 감지")
        st.info("💡 가장 정확한 위치를 얻을 수 있는 방법입니다!")
        
        # 브라우저 위치 API HTML 삽입
        html_location = get_browser_location()
        st.components.v1.html(html_location, height=300)
        
        st.markdown("---")
        st.markdown("**브라우저에서 위치를 감지한 후 아래에 좌표를 입력하세요:**")
        
        col1, col2 = st.columns(2)
        with col1:
            browser_lat = st.number_input("브라우저 감지 위도", 
                                        value=0.0, 
                                        min_value=-90.0, 
                                        max_value=90.0, 
                                        step=0.000001,
                                        format="%.6f",
                                        key="browser_lat")
        with col2:
            browser_lon = st.number_input("브라우저 감지 경도", 
                                        value=0.0, 
                                        min_value=-180.0, 
                                        max_value=180.0, 
                                        step=0.000001,
                                        format="%.6f",
                                        key="browser_lon")
        
        if st.button("🌐 브라우저 위치 사용"):
            if browser_lat != 0.0 or browser_lon != 0.0:
                st.session_state.selected_lat = browser_lat
                st.session_state.selected_lon = browser_lon
                st.session_state.selected_city = "브라우저 감지 위치"
                st.success("✅ 브라우저 위치가 설정되었습니다!")
            else:
                st.warning("⚠️ 먼저 위 버튼을 클릭하여 위치를 감지하세요.")
    
    # 현재 설정된 위치 표시
    if hasattr(st.session_state, 'selected_lat') and st.session_state.selected_lat is not None:
        return st.session_state.selected_lat, st.session_state.selected_lon, st.session_state.selected_city
    
    return None, None, None

# === Function: OpenWeather API로 날씨 데이터 가져오기 ===
def get_weather(lat, lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            res = response.json()
            temp = res["main"]["temp"]
            humidity = res["main"]["humidity"]
            feels_like = res["main"]["feels_like"]  # OpenWeather 자체 체감온도
            weather_desc = res["weather"][0]["description"]
            return temp, humidity, feels_like, weather_desc
        else:
            st.error(f"날씨 API 오류: {response.status_code} - {response.text}")
            return None, None, None, None
            
    except Exception as e:
        st.error(f"날씨 API 오류: {e}")
        return None, None, None, None

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

# === Function: 종합 체감온도 분석 ===
def analyze_comprehensive_comfort(temp, humidity, feels_like_owm, heat_index, dew_point):
    """다양한 체감온도 지표를 종합 분석"""
    
    analysis = {
        "comfort_level": "",
        "primary_factors": [],
        "recommendations": [],
        "comfort_score": 0
    }
    
    # 체감온도 점수 계산 (0-100, 높을수록 불편)
    temp_score = max(0, (temp - 20) * 2)  # 20도 이상부터 점수 증가
    humidity_score = max(0, (humidity - 40) * 1.5)  # 40% 이상부터 점수 증가
    dew_score = max(0, (dew_point - 15) * 3)  # 15도 이상부터 점수 증가
    
    total_score = temp_score + humidity_score + dew_score
    analysis["comfort_score"] = min(100, total_score)
    
    # 주요 영향 요인 분석
    if humidity > 70:
        analysis["primary_factors"].append("높은 습도")
    if dew_point > 20:
        analysis["primary_factors"].append("높은 이슬점")
    if temp > 30:
        analysis["primary_factors"].append("고온")
    
    # 쾌적도 레벨 결정
    if analysis["comfort_score"] < 20:
        analysis["comfort_level"] = "매우 쾌적 😊"
    elif analysis["comfort_score"] < 40:
        analysis["comfort_level"] = "쾌적 🙂"
    elif analysis["comfort_score"] < 60:
        analysis["comfort_level"] = "보통 😐"
    elif analysis["comfort_score"] < 80:
        analysis["comfort_level"] = "불쾌 😓"
    else:
        analysis["comfort_level"] = "매우 불쾌 🥵"
    
    # 권장사항 생성
    if humidity > 80:
        analysis["recommendations"].append("제습기 사용을 권장합니다")
    if dew_point > 22:
        analysis["recommendations"].append("야외 활동을 자제하세요")
    if temp > 28:
        analysis["recommendations"].append("충분한 수분 섭취가 필요합니다")
    if analysis["comfort_score"] > 60:
        analysis["recommendations"].append("에어컨이나 선풍기 사용을 권장합니다")
    
    return analysis

# === Streamlit UI ===
st.title("🌡️ 정확한 위치 기반 체감온도 분석기")

# 세션 상태 초기화
if 'selected_lat' not in st.session_state:
    st.session_state.selected_lat = None
if 'selected_lon' not in st.session_state:
    st.session_state.selected_lon = None
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None

# 개선 사항 안내
st.info("""
🎯 **개선된 위치 감지 기능**
- **브라우저 위치**: 가장 정확한 현재 위치 (GPS 기반)
- **도시명 검색**: 전 세계 도시명으로 쉽게 검색
- **직접 좌표**: 정확한 좌표 입력
- **IP 위치**: 참고용 (서버 위치일 수 있음)
""")

# 🔐 API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except:
    st.error("⚠️ secrets.toml 파일에 OWM_KEY가 설정되지 않았습니다.")
    st.code("""
# .streamlit/secrets.toml 파일에 추가:
OWM_KEY = "your_openweathermap_api_key_here"
    """)
    API_KEY = None

if API_KEY:
    # 위치 입력 방식 선택
    location_method = st.radio(
        "위치 정보 입력 방식을 선택하세요:",
        ["🗺️ 수동 위치 입력 (권장)", "🌐 IP 위치 감지 (참고용)"],
        index=0
    )
    
    lat, lon, city = None, None, None
    
    if location_method == "🗺️ 수동 위치 입력 (권장)":
        lat, lon, city = manual_location_input(API_KEY)
    else:
        st.warning("⚠️ **주의**: IP 위치 감지는 스트림릿 서버 위치(미국)를 반환할 수 있습니다.")
        if st.button("🔍 IP 기반 위치 감지 시도"):
            with st.spinner("IP 위치를 감지하는 중..."):
                lat, lon, city = get_location_by_ip()
    
    # 위치 정보가 설정되었을 때만 날씨 분석 수행
    if lat is not None and lon is not None:
        st.success(f"📍 **현재 설정된 위치**: {city}")
        st.info(f"🌍 좌표: 위도 {lat:.6f}, 경도 {lon:.6f}")
        
        # 날씨 분석 버튼
        if st.button("🌤️ 날씨 분석 시작", type="primary"):
            with st.spinner("날씨 정보를 분석하는 중..."):
                weather_data = get_weather(lat, lon, API_KEY)
                
                if weather_data[0] is not None:
                    temp, humidity, feels_like_owm, weather_desc = weather_data
                    
                    # 추가 계산
                    heat_index = calculate_heat_index(temp, humidity)
                    dew_point = calculate_dew_point(temp, humidity)
                    
                    # 종합 분석
                    comfort_analysis = analyze_comprehensive_comfort(
                        temp, humidity, feels_like_owm, heat_index, dew_point
                    )
                    
                    # 결과 표시
                    st.markdown("---")
                    st.subheader("🌡️ 상세 날씨 분석")
                    
                    # 기본 정보
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**날씨**: {weather_desc.title()}")
                        st.info(f"**온도**: {temp}°C")
                        st.info(f"**습도**: {humidity}%")
                    with col2:
                        st.info(f"**이슬점**: {dew_point}°C")
                        st.info(f"**OpenWeather 체감온도**: {feels_like_owm}°C")
                        st.info(f"**Heat Index**: {heat_index}°C")
                    
                    # 종합 쾌적도 평가
                    st.markdown("### 🎯 종합 쾌적도 평가")
                    
                    # 쾌적도 점수 시각화
                    score = comfort_analysis["comfort_score"]
                    if score < 40:
                        st.success(f"**{comfort_analysis['comfort_level']}** (점수: {score:.1f}/100)")
                    elif score < 70:
                        st.warning(f"**{comfort_analysis['comfort_level']}** (점수: {score:.1f}/100)")
                    else:
                        st.error(f"**{comfort_analysis['comfort_level']}** (점수: {score:.1f}/100)")
                    
                    # 주요 영향 요인
                    if comfort_analysis["primary_factors"]:
                        st.write("**주요 영향 요인:**", ", ".join(comfort_analysis["primary_factors"]))
                    
                    # 권장사항
                    if comfort_analysis["recommendations"]:
                        st.markdown("### 💡 권장사항")
                        for i, rec in enumerate(comfort_analysis["recommendations"], 1):
                            st.write(f"{i}. {rec}")
                    
                    # 상세 비교표
                    with st.expander("📊 체감온도 비교 분석"):
                        st.markdown("**다양한 체감온도 지표 비교:**")
                        
                        comparison_data = {
                            "지표": [
                                "실제 온도", 
                                "OpenWeather 체감온도", 
                                "Heat Index", 
                                "이슬점"
                            ],
                            "온도 (°C)": [
                                temp, 
                                feels_like_owm, 
                                heat_index, 
                                dew_point
                            ],
                            "실온과의 차이": [
                                0, 
                                round(feels_like_owm - temp, 1), 
                                round(heat_index - temp, 1), 
                                round(dew_point - temp, 1)
                            ]
                        }
                        
                        import pandas as pd
                        df = pd.DataFrame(comparison_data)
                        st.dataframe(df, hide_index=True)
                else:
                    st.error("❌ 날씨 정보를 가져올 수 없습니다. 다른 위치를 시도해보세요.")
    
    else:
        st.info("👆 위에서 위치를 선택하거나 입력하세요!")
        
else:
    st.warning("⚠️ OpenWeatherMap API 키가 필요합니다.")
    st.markdown("""
    ### 📝 API 키 설정 방법:
    1. [OpenWeatherMap](https://openweathermap.org/api)에서 무료 계정 생성
    2. API 키 발급 (무료 플랜 사용 가능)
    3. 스트림릿 앱 설정에서 secrets 추가:
    ```
    OWM_KEY = "your_api_key_here"
    ```
    """)

# 푸터 정보
st.markdown("---")
st.markdown("💡 **팁**: 브라우저 위치 감지가 가장 정확한 결과를 제공합니다!")
