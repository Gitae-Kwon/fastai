import streamlit as st
import requests
import time

# === Function: IP 기반 위치 감지 (개선된 버전) ===
def get_location_by_ip():
    """여러 IP 위치 서비스를 순차적으로 시도"""
    
    # 여러 IP 위치 서비스 목록
    services = [
        {
            'url': 'https://ipinfo.io/json',
            'parser': lambda res: (
                res["loc"].split(",")[0], 
                res["loc"].split(",")[1], 
                res.get("city", "Unknown")
            )
        },
        {
            'url': 'http://ip-api.com/json',
            'parser': lambda res: (
                str(res["lat"]), 
                str(res["lon"]), 
                res.get("city", "Unknown")
            )
        },
        {
            'url': 'https://ipapi.co/json',
            'parser': lambda res: (
                str(res["latitude"]), 
                str(res["longitude"]), 
                res.get("city", "Unknown")
            )
        }
    ]
    
    for i, service in enumerate(services):
        try:
            st.write(f"🔍 위치 서비스 {i+1} 시도 중...")
            
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
                st.write(f"📡 응답 데이터: {res}")  # 디버깅용
                
                lat, lon, city = service['parser'](res)
                
                # 좌표 유효성 검사
                lat_float = float(lat)
                lon_float = float(lon)
                
                if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                    st.success(f"✅ 위치 정보 획득 성공 (서비스 {i+1})")
                    return lat_float, lon_float, city
                else:
                    st.warning(f"⚠️ 서비스 {i+1}: 잘못된 좌표값")
                    
        except requests.exceptions.Timeout:
            st.warning(f"⏰ 서비스 {i+1}: 응답 시간 초과")
        except requests.exceptions.ConnectionError:
            st.warning(f"🔌 서비스 {i+1}: 연결 오류")
        except KeyError as e:
            st.warning(f"🔑 서비스 {i+1}: 필수 키 누락 - {e}")
        except ValueError as e:
            st.warning(f"🔢 서비스 {i+1}: 좌표 변환 오류 - {e}")
        except Exception as e:
            st.warning(f"❌ 서비스 {i+1}: 기타 오류 - {e}")
        
        # 서비스 간 지연시간
        if i < len(services) - 1:
            time.sleep(1)
    
    st.error("모든 위치 서비스에서 실패했습니다.")
    return None, None, "Unknown"

# === Function: 수동 위치 입력 옵션 ===
def manual_location_input():
    """사용자가 직접 위치를 입력할 수 있는 옵션"""
    st.subheader("🗺️ 수동 위치 입력")
    
    # 주요 도시 프리셋 추가
    preset_cities = {
        "서울": (37.5665, 126.9780),
        "부산": (35.1796, 129.0756),
        "양주": (37.8128, 127.0459),
        "의정부": (37.7381, 127.0473),
        "파리 (Paris)": (48.8566, 2.3522),
        "클리시 (Clichy)": (48.9042, 2.3064),
        "직접 입력": None
    }
    
    selected_city = st.selectbox("도시를 선택하거나 직접 입력하세요:", list(preset_cities.keys()))
    
    if preset_cities[selected_city] is not None:
        manual_lat, manual_lon = preset_cities[selected_city]
        manual_city = selected_city
        st.success(f"✅ 선택된 도시: {selected_city} (위도: {manual_lat}, 경도: {manual_lon})")
    else:
        st.subheader("직접 좌표 입력")
        col1, col2 = st.columns(2)
        with col1:
            manual_lat = st.number_input("위도 (Latitude)", 
                                       value=37.5665, 
                                       min_value=-90.0, 
                                       max_value=90.0, 
                                       step=0.0001,
                                       format="%.4f")
        with col2:
            manual_lon = st.number_input("경도 (Longitude)", 
                                       value=126.9780, 
                                       min_value=-180.0, 
                                       max_value=180.0, 
                                       step=0.0001,
                                       format="%.4f")
        
        manual_city = st.text_input("도시명 (선택사항)", value="Custom Location")
    
    return manual_lat, manual_lon, manual_city

# === Function: OpenWeather API로 날씨 데이터 가져오기 (개선된 버전) ===
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
            return temp, humidity
        else:
            st.error(f"날씨 API 오류: {response.status_code} - {response.text}")
            return None, None
            
    except requests.exceptions.Timeout:
        st.error("날씨 API 응답 시간 초과")
        return None, None
    except requests.exceptions.ConnectionError:
        st.error("날씨 API 연결 오류")
        return None, None
    except Exception as e:
        st.error(f"날씨 API 기타 오류: {e}")
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

# === Function: 이슬점을 반영한 통합 체감온도 계산 ===
def calculate_comprehensive_feels_like(temp_c, humidity, dew_point):
    """
    이슬점과 습도를 모두 고려한 포괄적 체감온도 계산
    - 기본 Heat Index
    - 이슬점 보정 (불쾌지수 반영)
    - 습도 차이에 따른 추가 보정
    """
    # 1. 기본 Heat Index
    base_heat_index = calculate_heat_index(temp_c, humidity)
    
    # 2. 이슬점 보정 계산
    # 이슬점이 높을수록(습한 공기) 더 불쾌함
    dew_point_correction = 0
    if dew_point > 24:  # 매우 습함
        dew_point_correction = 3.0
    elif dew_point > 21:  # 습함
        dew_point_correction = 2.0
    elif dew_point > 18:  # 약간 습함
        dew_point_correction = 1.0
    elif dew_point > 15:  # 보통
        dew_point_correction = 0
    elif dew_point > 10:  # 건조
        dew_point_correction = -0.5
    else:  # 매우 건조
        dew_point_correction = -1.0
    
    # 3. 온도와 이슬점의 차이 보정
    # 차이가 클수록 덜 불쾌함 (건조함)
    temp_dew_diff = temp_c - dew_point
    if temp_dew_diff > 15:  # 매우 건조
        diff_correction = -1.5
    elif temp_dew_diff > 10:  # 건조
        diff_correction = -1.0
    elif temp_dew_diff > 5:  # 보통
        diff_correction = -0.5
    else:  # 습함
        diff_correction = 0.5
    
    # 4. 최종 체감온도 계산
    comprehensive_feels_like = base_heat_index + dew_point_correction + diff_correction
    
    return round(comprehensive_feels_like, 1), dew_point_correction, diff_correction

# === Function: 체감온도 상세 분석 ===
def analyze_comfort_level(temp, humidity, dew_point, feels_like):
    """체감온도에 대한 상세 분석 제공"""
    
    analysis = {
        "comfort_level": "",
        "humidity_effect": "",
        "dew_point_effect": "",
        "recommendations": []
    }
    
    # 체감온도 기준 쾌적도
    if feels_like < 20:
        analysis["comfort_level"] = "쾌적함 😊"
    elif feels_like < 25:
        analysis["comfort_level"] = "약간 따뜻함 🙂"
    elif feels_like < 28:
        analysis["comfort_level"] = "따뜻함 😐"
    elif feels_like < 32:
        analysis["comfort_level"] = "더움 😓"
    elif feels_like < 35:
        analysis["comfort_level"] = "매우 더움 🥵"
    else:
        analysis["comfort_level"] = "위험 수준 🔥"
    
    # 습도 영향 분석
    if humidity > 80:
        analysis["humidity_effect"] = "매우 습함 - 땀 증발이 어려워 더 덥게 느껴집니다"
        analysis["recommendations"].append("실내에서는 제습기 사용을 권장합니다")
    elif humidity > 60:
        analysis["humidity_effect"] = "습함 - 체감온도가 실온보다 높습니다"
        analysis["recommendations"].append("통풍이 잘 되는 곳에 머무르세요")
    elif humidity > 40:
        analysis["humidity_effect"] = "적정 습도 - 쾌적한 수준입니다"
    else:
        analysis["humidity_effect"] = "건조함 - 피부와 호흡기에 주의하세요"
        analysis["recommendations"].append("충분한 수분 섭취와 보습이 필요합니다")
    
    # 이슬점 영향 분석
    if dew_point > 24:
        analysis["dew_point_effect"] = "매우 습한 공기 - 극도로 불쾌합니다"
        analysis["recommendations"].append("야외 활동을 피하고 에어컨이 있는 곳에 머무르세요")
    elif dew_point > 21:
        analysis["dew_point_effect"] = "습한 공기 - 불쾌감을 느낄 수 있습니다"
        analysis["recommendations"].append("격렬한 운동은 피하세요")
    elif dew_point > 18:
        analysis["dew_point_effect"] = "약간 습한 공기 - 대부분 견딜 만합니다"
    elif dew_point > 15:
        analysis["dew_point_effect"] = "쾌적한 공기 - 좋은 날씨입니다"
    else:
        analysis["dew_point_effect"] = "건조한 공기 - 매우 쾌적합니다"
    
    return analysis

# === Streamlit UI ===
st.title("🌡️ 자동 위치 기반 체감온도 계산기")

# 스트림릿 클라우드 배포 시 주의사항 안내
st.info("⚠️ **스트림릿 클라우드 배포 시 주의사항**: IP 기반 위치 감지는 서버 위치를 반환할 수 있습니다. 정확한 위치를 원하시면 '수동 좌표 입력'을 사용하세요.")

# 위치 입력 방식 선택 (기본값을 수동 입력으로 변경)
location_method = st.radio(
    "위치 정보 입력 방식을 선택하세요:",
    ["수동 좌표 입력", "자동 IP 위치 감지"],
    index=0  # 수동 입력을 기본값으로 설정
)

# 🔐 API Key 확인
try:
    API_KEY = st.secrets["OWM_KEY"]
except:
    st.error("secrets.toml 파일에 OWM_KEY가 설정되지 않았습니다.")
    st.code("""
# .streamlit/secrets.toml 파일에 추가:
OWM_KEY = "your_openweathermap_api_key_here"
    """)
    API_KEY = None

if API_KEY:
    if location_method == "자동 IP 위치 감지":
        st.warning("🚨 **IP 위치 감지 제한사항**: 스트림릿 클라우드에서는 서버 위치가 감지될 수 있습니다.")
        if st.button("🎯 현재 위치 자동 감지 (참고용)"):
            with st.spinner("위치 정보를 가져오는 중..."):
                lat, lon, city = get_location_by_ip()
                if lat and lon:
                    st.warning(f"감지된 위치가 실제 위치와 다를 수 있습니다: {city}")
    else:
        lat, lon, city = manual_location_input()
    
    # 위치 정보가 있으면 날씨 데이터 가져오기
    if 'lat' in locals() and lat is not None and lon is not None:
        st.info(f"📍 현재 설정된 위치: **{city}** (위도 {lat}, 경도 {lon})")
        
        with st.spinner("날씨 정보를 가져오는 중..."):
            temp, humidity = get_weather(lat, lon, API_KEY)
            
        if temp is not None and humidity is not None:
            st.success(f"✅ 현재 기온: {temp}°C, 습도: {humidity}%")
            
            # 기본 계산
            hi = calculate_heat_index(temp, humidity)
            dew = calculate_dew_point(temp, humidity)
            
            # 이슬점 반영한 통합 체감온도 계산
            comprehensive_feels_like, dew_correction, diff_correction = calculate_comprehensive_feels_like(temp, humidity, dew)
            
            # 체감온도 상세 분석
            comfort_analysis = analyze_comfort_level(temp, humidity, dew, comprehensive_feels_like)
            
            # 결과 표시
            st.markdown("---")
            st.subheader("🌡️ 온도 분석 결과")
            
            # 메인 지표들
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("실제 온도", f"{temp}°C")
            with col2:
                st.metric("기본 체감온도", f"{hi}°C", f"{hi-temp:+.1f}°C")
            with col3:
                st.metric("**통합 체감온도**", f"{comprehensive_feels_like}°C", f"{comprehensive_feels_like-temp:+.1f}°C")
            with col4:
                st.metric("이슬점", f"{dew}°C")
            
            # 체감온도 보정 요인 설명
            st.markdown("### 🔍 체감온도 보정 분석")
            
            correction_col1, correction_col2 = st.columns(2)
            with correction_col1:
                st.info(f"**이슬점 보정**: {dew_correction:+.1f}°C\n\n이슬점이 {dew}°C로 {comfort_analysis['dew_point_effect']}")
                
            with correction_col2:
                temp_dew_diff = temp - dew
                st.info(f"**건조도 보정**: {diff_correction:+.1f}°C\n\n온도-이슬점 차이: {temp_dew_diff:.1f}°C")
            
            # 전체적인 쾌적도 평가
            st.markdown("### 📊 종합 쾌적도 평가")
            
            # 쾌적도 레벨에 따른 색상 표시
            if comprehensive_feels_like < 25:
                st.success(f"🎯 **{comfort_analysis['comfort_level']}**")
            elif comprehensive_feels_like < 30:
                st.warning(f"🎯 **{comfort_analysis['comfort_level']}**")
            else:
                st.error(f"🎯 **{comfort_analysis['comfort_level']}**")
            
            # 습도 영향
            st.write(f"💧 **습도 영향**: {comfort_analysis['humidity_effect']}")
            
            # 권장사항
            if comfort_analysis['recommendations']:
                st.markdown("### 💡 권장사항")
                for i, rec in enumerate(comfort_analysis['recommendations'], 1):
                    st.write(f"{i}. {rec}")
            
            # 상세 수치 비교표
            with st.expander("📋 상세 수치 비교"):
                comparison_data = {
                    "지표": ["실제 온도", "기본 체감온도 (Heat Index)", "통합 체감온도 (이슬점 반영)", "이슬점 온도"],
                    "온도 (°C)": [temp, hi, comprehensive_feels_like, dew],
                    "실온과의 차이": [0, hi-temp, comprehensive_feels_like-temp, dew-temp],
                    "설명": [
                        "측정된 실제 기온",
                        "습도만 고려한 전통적 체감온도",
                        "이슬점과 건조도까지 반영한 종합 체감온도",
                        "공기 중 수증기가 포화되는 온도"
                    ]
                }
                
                import pandas as pd
                df = pd.DataFrame(comparison_data)
                st.dataframe(df, hide_index=True)
        else:
            st.error("날씨 정보를 가져올 수 없습니다.")
    
        
    # 디버깅 정보 표시 (개발 중에만)
    if st.checkbox("🔧 디버깅 정보 표시"):
        st.subheader("디버깅 정보")
        st.write("- 현재 환경: 스트림릿 클라우드 (추정)")
        st.write("- IP 위치 서비스는 서버 IP를 기준으로 위치를 감지합니다")
        st.write("- 정확한 날씨 정보를 원하시면 수동 입력을 사용하세요")
        if 'lat' in locals() and lat is not None:
            st.json({
                "설정된_위도": lat,
                "설정된_경도": lon,
                "설정된_도시": city
            })
else:
    st.warning("먼저 OpenWeatherMap API 키를 설정하세요.")
    st.markdown("""
    ### API 키 설정 방법:
    1. [OpenWeatherMap](https://openweathermap.org/api)에서 무료 계정 생성
    2. API 키 발급
    3. `.streamlit/secrets.toml` 파일 생성 후 다음 내용 추가:
    ```toml
    OWM_KEY = "your_api_key_here"
    ```
    """)
