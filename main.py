import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# Streamlit 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(page_title="어제 박스오피스", layout="wide")

st.title("🎬 어제 일자 박스오피스 TOP 10")


# --- [1] 데이터 불러오기 함수 (캐싱 적용) ---
# ttl=3600: 동일한 인자(target_date)로 호출할 경우 1시간(3600초) 동안 API 재요청 없이 기존 결과를 사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office(target_date, api_key):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        # HTTP 응답 상태 코드 확인
        if response.status_code != 200:
            return None, f"API 요청에 실패했습니다. (응답 코드: {response.status_code})"

        data = response.json()

        # KOBIS API 특성: 인증키 오류 등의 문제 발생 시 status_code는 200이지만 faultInfo 응답이 옵니다.
        if "faultInfo" in data:
            fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
            return None, f"KOBIS API 오류가 발생했습니다: {fault_msg}"

        # 데이터 구조 추출
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 결과 목록이 비어있는 경우
        if not daily_list:
            return (
                None,
                "조회된 영화 목록이 없습니다. 날짜 또는 API 상태를 확인해 주세요.",
            )

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {str(e)}"


# --- [2] 인증키 설정 및 검증 ---
# Streamlit Secrets(비밀 금고)에서 KOBIS_KEY 항목을 가져옵니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "💡 **[안내] API 키 설정 필요**\n\n"
        "Streamlit Cloud의 App Settings > Secrets에서 `KOBIS_KEY`를 설정해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# --- [3] 어제 날짜 계산 (한국 표준시 KST 기준) ---
# 배포 서버의 시계가 해외 기준이더라도 정확히 한국 시간 기준 어제 날짜를 구합니다.
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday_kst = now_kst - datetime.timedelta(days=1)
target_date_str = yesterday_kst.strftime("%Y%m%d")
display_date_str = yesterday_kst.strftime("%Y년 %m월 %d일")

st.caption(f"기준 일자: **{display_date_str}**")


# --- [4] API 데이터 수집 및 예외 처리 ---
daily_list, error_message = fetch_box_office(target_date_str, api_key)

# 에러가 발생했거나 데이터가 없는 경우 안내문 표시 후 중단
if error_message:
    st.error(
        f"⚠️ **데이터를 불러오지 못했습니다.**\n\n"
        f"**상세 내용:** {error_message}\n\n"
        "**확인해야 할 사항:**\n"
        "1. `KOBIS_KEY`가 올바르게 등록되었는지 확인해 주세요.\n"
        "2. 영화진흥위원회(KOBIS) API 서비스가 정상 작동 중인지 확인해 주세요.\n"
        "3. 잠시 후 페이지를 새로고침해 주세요."
    )
    st.stop()


# --- [5] 데이터 전처리 (문자열 -> 숫자 변환) ---
df = pd.DataFrame(daily_list)

# 필요한 필드들을 숫자로 변환 (전일 대비 증감은 rankInten 사용)
numeric_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt",
]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# --- [6] 1위 영화 핵심 지표 (Metric Card) ---
top_1 = df[df["rank"] == 1].iloc[0]

# 순위 변동 표시 텍스트 생성
rank_inten = top_1["rankInten"]
if rank_inten > 0:
    rank_delta = f"▲ {rank_inten} (순위 상승)"
elif rank_inten < 0:
    rank_delta = f"▼ {abs(rank_inten)} (순위 하락)"
else:
    rank_delta = "– (순위 유지)"

st.markdown(f"### 🏆 오늘의 1위 영화: **{top_1['movieNm']}**")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="어제 관객수",
        value=f"{top_1['audiCnt']:,} 명",
        delta=rank_delta,
    )
with col2:
    st.metric(
        label="누적 관객수",
        value=f"{top_1['audiAcc']:,} 명",
    )
with col3:
    st.metric(
        label="스크린수",
        value=f"{top_1['scrnCnt']:,} 개",
    )

st.divider()


# --- [7] 상위 5개 영화 관객수 막대그래프 ---
st.subheader("📊 관객수 TOP 5")
top5_df = df.sort_values(by="rank").head(5)

# 차트 시각화를 위한 전용 데이터프레임 구성
chart_df = top5_df[["movieNm", "audiCnt"]].set_index("movieNm")
chart_df.columns = ["관객수"]

st.bar_chart(chart_df)

st.divider()


# --- [8] 전체 순위 표 출력 ---
st.subheader("📋 전체 박스오피스 순위")

# 표 출력을 위한 칼럼 정리 및 이름 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객수",
    "스크린수",
]

# 숫자에 천 단위 쉼표(,) 서식 적용
formatted_df = display_df.copy()
formatted_df["관객수"] = formatted_df["관객수"].apply(lambda x: f"{x:,}")
formatted_df["누적관객수"] = formatted_df["누적관객수"].apply(
    lambda x: f"{x:,}"
)
formatted_df["스크린수"] = formatted_df["스크린수"].apply(
    lambda x: f"{x:,}"
)

st.dataframe(formatted_df, use_container_width=True, hide_index=True)
